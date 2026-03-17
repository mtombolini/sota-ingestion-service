import hashlib
import json
import logging
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.exceptions import ConnectorError, NormalizationError, PersistenceError
from app.models import (
    IntegrationConnection,
    IntegrationError,
    IntegrationJob,
    IntegrationJobRun,
    IntegrationOutboxEvent,
    IntegrationRawObject,
    Location,
    Product,
    SalesOrder,
    SalesOrderLine,
    Stock,
    StockMovement,
    Variant,
)
from app.providers import provider_registry
from app.secrets import get_secret_store

logger = logging.getLogger(__name__)


class IngestionService:
    def __init__(self, db: Session):
        self.db = db

    def list_jobs(self, tenant_id: int | None = None) -> list[IntegrationJob]:
        stmt = select(IntegrationJob)
        if tenant_id is not None:
            stmt = stmt.where(IntegrationJob.tenant_id == tenant_id)
        return list(self.db.scalars(stmt.order_by(IntegrationJob.id)).all())

    def list_runs(self, limit: int = 30, tenant_id: int | None = None) -> list[IntegrationJobRun]:
        from sqlalchemy import desc
        stmt = select(IntegrationJobRun)
        if tenant_id is not None:
            stmt = stmt.join(IntegrationJob, IntegrationJob.id == IntegrationJobRun.job_id).where(IntegrationJob.tenant_id == tenant_id)
        return list(self.db.scalars(stmt.order_by(desc(IntegrationJobRun.id)).limit(limit)).all())

    def list_errors(self, limit: int = 30, tenant_id: int | None = None) -> list[IntegrationError]:
        from sqlalchemy import desc
        stmt = select(IntegrationError)
        if tenant_id is not None:
            stmt = stmt.where(IntegrationError.tenant_id == tenant_id)
        return list(self.db.scalars(stmt.order_by(desc(IntegrationError.id)).limit(limit)).all())

    def trigger_job(self, job_id: int, tenant_id: int | None = None) -> IntegrationJobRun:
        job = self.db.get(IntegrationJob, job_id)
        if not job:
            raise ValueError(f"job {job_id} not found")
        if tenant_id is not None and job.tenant_id != tenant_id:
            raise ValueError(f"job {job_id} not found for tenant {tenant_id}")
        run = IntegrationJobRun(job_id=job.id, correlation_id=str(uuid.uuid4()), status="queued")
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    async def execute_job_run(self, run_id: int) -> None:
        run = self.db.get(IntegrationJobRun, run_id)
        if not run:
            raise ValueError("run not found")
        job = self.db.get(IntegrationJob, run.job_id)
        tenant_id = job.tenant_id
        job_type = job.job_type

        run.status = "running"
        run.started_at = datetime.utcnow()
        self.db.commit()

        connection = None
        try:
            connection = self.db.get(IntegrationConnection, job.connection_id)
            provider = provider_registry.get(connection.provider)

            try:
                connector = provider.build_runtime_connector(self.db, connection, secret_store=get_secret_store())
            except Exception as exc:
                raise ConnectorError(f"Failed to build connector: {exc}") from exc

            try:
                records = await provider.fetch_records(connector, job_type)
            except ConnectorError:
                raise
            except Exception as exc:
                raise ConnectorError(f"Failed to fetch records for {job_type}: {exc}") from exc

            run.records_raw = len(records)

            try:
                if job_type == "sync_product_catalog":
                    run.records_normalized = self._persist_products(tenant_id, run.id, records, provider=provider)
                elif job_type == "sync_locations":
                    run.records_normalized = self._persist_locations(tenant_id, run.id, records, provider=provider)
                elif job_type == "sync_stock":
                    run.records_normalized = self._persist_inventory(tenant_id, run.id, records, provider=provider)
                elif job_type == "sync_sales_orders":
                    run.records_normalized = self._persist_sales_orders(tenant_id, run.id, records, provider=provider)
                elif job_type in ("sync_customers", "sync_document_types"):
                    for rec in records:
                        self._persist_raw(tenant_id, run.id, provider.source_system(), provider.source_endpoint_for_job(job_type), rec)
                    self.db.commit()
                    run.records_normalized = 0
                else:
                    raise ValueError(f"unsupported job type {job_type}")
            except (ConnectorError, NormalizationError, PersistenceError, ValueError):
                raise
            except Exception as exc:
                raise PersistenceError(f"Failed to persist {job_type}: {exc}") from exc

            run.status = "success"
            run.finished_at = datetime.utcnow()
            self.db.commit()

        except Exception as exc:
            self.db.rollback()
            run = self.db.get(IntegrationJobRun, run_id)
            if run:
                run.status = "failed"
                run.finished_at = datetime.utcnow()

            error_type = type(exc).__name__
            self.db.add(
                IntegrationError(
                    tenant_id=tenant_id,
                    job_run_id=run_id,
                    object_name=job_type,
                    severity="error",
                    message=f"[{error_type}] {exc}",
                    payload={
                        "connection_id": job.connection_id,
                        "provider": connection.provider if connection is not None else None,
                        "error_type": error_type,
                    },
                )
            )
            self.db.commit()
            logger.exception("job failed", extra={"run_id": run_id, "error_type": error_type})

    # ------------------------------------------------------------------
    # Raw & outbox helpers
    # ------------------------------------------------------------------

    def _persist_raw(self, tenant_id: int, run_id: int, source_system: str, endpoint: str, payload: dict[str, Any]) -> None:
        safe_payload = self._json_safe(payload)
        checksum = hashlib.sha256(json.dumps(safe_payload, sort_keys=True).encode()).hexdigest()
        self.db.add(
            IntegrationRawObject(
                tenant_id=tenant_id,
                job_run_id=run_id,
                source_system=source_system,
                endpoint=endpoint,
                checksum=checksum,
                payload=safe_payload,
            )
        )

    def _emit_outbox(self, tenant_id: int, event_type: str, aggregate_type: str, aggregate_id: str, payload: dict) -> None:
        self.db.add(
            IntegrationOutboxEvent(
                tenant_id=tenant_id,
                event_type=event_type,
                aggregate_type=aggregate_type,
                aggregate_id=aggregate_id,
                payload=self._json_safe(payload),
            )
        )

    @staticmethod
    def _json_safe(value):
        if isinstance(value, dict):
            return {k: IngestionService._json_safe(v) for k, v in value.items()}
        if isinstance(value, list):
            return [IngestionService._json_safe(v) for v in value]
        if isinstance(value, tuple):
            return [IngestionService._json_safe(v) for v in value]
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        if isinstance(value, Decimal):
            return float(value)
        return value

    # ------------------------------------------------------------------
    # Generic FK resolution (consolidates _resolve_product_id,
    # _resolve_variant_id, _resolve_location_id)
    # ------------------------------------------------------------------

    def _resolve_entity_id(self, model, tenant_id: int, source_system: str, external_id: str) -> int | None:
        return self.db.scalar(
            select(model.id).where(
                model.tenant_id == tenant_id,
                model.source_system == source_system,
                model.external_id == external_id,
            )
        )

    # ------------------------------------------------------------------
    # Canonical persist methods
    # ------------------------------------------------------------------

    def _persist_products(self, tenant_id: int, run_id: int, records: list[dict], *, provider) -> int:
        source_system = provider.source_system()
        for rec in records:
            self._persist_raw(tenant_id, run_id, source_system, provider.source_endpoint_for_job("sync_product_catalog"), rec)
            n = provider.normalize("sync_product_catalog", rec)
            variants = n.pop("variants", [])
            existing = self.db.scalar(
                select(Product).where(
                    Product.tenant_id == tenant_id,
                    Product.source_system == source_system,
                    Product.external_id == n["external_id"],
                )
            )
            if existing:
                for k, v in n.items():
                    setattr(existing, k, v)
                product = existing
            else:
                product = Product(tenant_id=tenant_id, **n)
                self.db.add(product)
                self.db.flush()

            for variant_payload in variants:
                variant_payload["product_id"] = product.id
                existing_variant = self.db.scalar(
                    select(Variant).where(
                        Variant.tenant_id == tenant_id,
                        Variant.source_system == source_system,
                        Variant.external_id == variant_payload["external_id"],
                    )
                )
                if existing_variant:
                    for k, v in variant_payload.items():
                        setattr(existing_variant, k, v)
                else:
                    self.db.add(Variant(tenant_id=tenant_id, **variant_payload))
            self._emit_outbox(tenant_id, "product.upserted", "product", n["external_id"], n)
        self.db.commit()
        return len(records)

    def _persist_locations(self, tenant_id: int, run_id: int, records: list[dict], *, provider) -> int:
        source_system = provider.source_system()
        for rec in records:
            self._persist_raw(tenant_id, run_id, source_system, provider.source_endpoint_for_job("sync_locations"), rec)
            n = provider.normalize("sync_locations", rec)
            existing = self.db.scalar(
                select(Location).where(
                    Location.tenant_id == tenant_id,
                    Location.source_system == source_system,
                    Location.external_id == n["external_id"],
                )
            )
            if existing:
                for k, v in n.items():
                    setattr(existing, k, v)
            else:
                self.db.add(Location(tenant_id=tenant_id, **n))
            self._emit_outbox(tenant_id, "location.upserted", "location", n["external_id"], n)
        self.db.commit()
        return len(records)

    def _persist_stock(self, tenant_id: int, run_id: int, records: list[dict], *, provider) -> int:
        source_system = provider.source_system()
        for rec in records:
            clean_rec = {k: v for k, v in rec.items() if not k.startswith("_")}
            self._persist_raw(tenant_id, run_id, source_system, provider.source_endpoint_for_job("sync_stock"), clean_rec)
            n = provider.normalize("sync_stock", rec)

            n["variant_id"] = self._resolve_entity_id(Variant, tenant_id, source_system, n["variant_external_id"])
            n["location_id"] = self._resolve_entity_id(Location, tenant_id, source_system, n["location_external_id"])

            existing = self.db.scalar(
                select(Stock).where(
                    Stock.tenant_id == tenant_id,
                    Stock.source_system == source_system,
                    Stock.variant_external_id == n["variant_external_id"],
                    Stock.location_external_id == n["location_external_id"],
                )
            )
            if existing:
                for k, v in n.items():
                    setattr(existing, k, v)
            else:
                self.db.add(Stock(tenant_id=tenant_id, **n))

            self._emit_outbox(
                tenant_id, "stock.updated", "stock",
                f"{n['variant_external_id']}:{n['location_external_id']}", n,
            )
        self.db.commit()
        return len(records)

    def _persist_stock_movements(self, tenant_id: int, run_id: int, records: list[dict], *, provider, endpoint: str, job_type: str) -> int:
        source_system = provider.source_system()
        movement_count = 0
        for rec in records:
            clean_rec = {k: v for k, v in rec.items() if not k.startswith("_")}
            self._persist_raw(tenant_id, run_id, source_system, endpoint, clean_rec)
            normalized = provider.normalize(job_type, rec)
            for movement in normalized.get("movements", []):
                movement["variant_id"] = self._resolve_entity_id(Variant, tenant_id, source_system, movement["variant_external_id"])
                location_ext = movement.get("location_external_id")
                movement["location_id"] = (
                    self._resolve_entity_id(Location, tenant_id, source_system, location_ext) if location_ext else None
                )

                existing = self.db.scalar(
                    select(StockMovement).where(
                        StockMovement.tenant_id == tenant_id,
                        StockMovement.source_system == source_system,
                        StockMovement.external_id == movement["external_id"],
                    )
                )
                if existing:
                    for k, v in movement.items():
                        setattr(existing, k, v)
                else:
                    self.db.add(StockMovement(tenant_id=tenant_id, **movement))
                movement_count += 1
        self.db.commit()
        return movement_count

    def _persist_inventory(self, tenant_id: int, run_id: int, records: list[dict], *, provider) -> int:
        snapshots: list[dict] = []
        movement_records_by_endpoint: dict[str, list[dict]] = {}

        for rec in records:
            record_type = rec.get("_stock_record_type")
            if record_type == "snapshot":
                snapshots.append(rec)
            elif record_type in {"reception", "consumption"}:
                endpoint = rec.get("_source_endpoint") or provider.source_endpoint_for_job("sync_stock")
                movement_records_by_endpoint.setdefault(endpoint, []).append(rec)
            else:
                raise ValueError("unsupported stock record type")

        normalized_count = 0
        if snapshots:
            normalized_count += self._persist_stock(tenant_id, run_id, snapshots, provider=provider)
        for endpoint, movement_records in movement_records_by_endpoint.items():
            normalized_count += self._persist_stock_movements(
                tenant_id,
                run_id,
                movement_records,
                provider=provider,
                endpoint=endpoint,
                job_type="sync_stock",
            )
        return normalized_count

    def _persist_sales_orders(self, tenant_id: int, run_id: int, records: list[dict], *, provider) -> int:
        source_system = provider.source_system()
        for rec in records:
            self._persist_raw(tenant_id, run_id, source_system, provider.source_endpoint_for_job("sync_sales_orders"), rec)
            n = provider.normalize("sync_sales_orders", rec)
            lines = n.pop("lines", [])

            location_ext_id = n.pop("location_external_id", None)
            n["location_external_id"] = location_ext_id
            n["location_id"] = self._resolve_entity_id(Location, tenant_id, source_system, location_ext_id) if location_ext_id else None

            existing = self.db.scalar(
                select(SalesOrder).where(
                    SalesOrder.tenant_id == tenant_id,
                    SalesOrder.source_system == source_system,
                    SalesOrder.external_id == n["external_id"],
                )
            )

            if existing:
                for k, v in n.items():
                    setattr(existing, k, v)
                existing.lines.clear()
                for line in lines:
                    line["variant_id"] = self._resolve_entity_id(Variant, tenant_id, source_system, line["variant_external_id"])
                    existing.lines.append(SalesOrderLine(**line))
                order = existing
            else:
                order = SalesOrder(tenant_id=tenant_id, **n)
                for line in lines:
                    line["variant_id"] = self._resolve_entity_id(Variant, tenant_id, source_system, line["variant_external_id"])
                    order.lines.append(SalesOrderLine(**line))
                self.db.add(order)
                self.db.flush()

            self._replace_sales_order_movements(tenant_id, source_system, order)

            outbox_payload = {**n, "lines": lines}
            self._emit_outbox(tenant_id, "sales_order.upserted", "sales_order", n["external_id"], outbox_payload)
        self.db.commit()
        return len(records)

    def _replace_sales_order_movements(self, tenant_id: int, source_system: str, order: SalesOrder) -> None:
        self.db.execute(
            delete(StockMovement).where(
                StockMovement.tenant_id == tenant_id,
                StockMovement.source_system == source_system,
                StockMovement.reference_type == "SALES_ORDER",
                StockMovement.reference_id == order.external_id,
            )
        )
        if order.status == "CANCELLED":
            return
        for idx, line in enumerate(order.lines, start=1):
            self.db.add(
                StockMovement(
                    tenant_id=tenant_id,
                    source_system=source_system,
                    external_id=f"sales-order:{order.external_id}:{idx}",
                    variant_id=line.variant_id,
                    location_id=order.location_id,
                    variant_external_id=line.variant_external_id,
                    location_external_id=order.location_external_id,
                    movement_type="SALE_OUT",
                    quantity=Decimal(str(line.quantity)) * Decimal("-1"),
                    reference_type="SALES_ORDER",
                    reference_id=order.external_id,
                    movement_date=order.order_date,
                    unit_cost=None,
                )
            )
