import hashlib
import json
import logging
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models import (
    Branch,
    IntegrationConnection,
    IntegrationError,
    IntegrationJob,
    IntegrationJobRun,
    IntegrationOutboxEvent,
    IntegrationRawObject,
    Product,
    SalesDocument,
    SalesDocumentLine,
    StockSnapshot,
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
        stmt = select(IntegrationJobRun)
        if tenant_id is not None:
            stmt = stmt.join(IntegrationJob, IntegrationJob.id == IntegrationJobRun.job_id).where(IntegrationJob.tenant_id == tenant_id)
        return list(self.db.scalars(stmt.order_by(desc(IntegrationJobRun.id)).limit(limit)).all())

    def list_errors(self, limit: int = 30, tenant_id: int | None = None) -> list[IntegrationError]:
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

        try:
            connection = self.db.get(IntegrationConnection, job.connection_id)
            provider = provider_registry.get(connection.provider)
            connector = provider.build_runtime_connector(self.db, connection, secret_store=get_secret_store())
            if job.job_type == "sync_product_catalog":
                records = await provider.fetch_records(connector, job.job_type)
                run.records_raw = len(records)
                run.records_normalized = self._persist_products(tenant_id, run.id, records, provider=provider)
            elif job_type == "sync_stock_snapshot":
                records = await provider.fetch_records(connector, job.job_type)
                run.records_raw = len(records)
                run.records_normalized = self._persist_stock(tenant_id, run.id, records, provider=provider)
            elif job_type == "sync_sales_documents":
                records = await provider.fetch_records(connector, job.job_type)
                run.records_raw = len(records)
                run.records_normalized = self._persist_sales(tenant_id, run.id, records, provider=provider)
            elif job_type == "sync_branches":
                records = await provider.fetch_records(connector, job.job_type)
                run.records_raw = len(records)
                run.records_normalized = self._persist_branches(tenant_id, run.id, records, provider=provider)
            else:
                raise ValueError(f"unsupported job type {job_type}")

            run.status = "success"
            run.finished_at = datetime.utcnow()
            self.db.commit()
        except Exception as exc:
            # Reset session state after failed flush/commit before writing failure metadata.
            self.db.rollback()
            run = self.db.get(IntegrationJobRun, run_id)
            if run:
                run.status = "failed"
                run.finished_at = datetime.utcnow()
            self.db.add(
                IntegrationError(
                    tenant_id=tenant_id,
                    job_run_id=run_id,
                    object_name=job_type,
                    message=str(exc),
                    payload={
                        "connection_id": job.connection_id,
                        "provider": connection.provider if "connection" in locals() and connection is not None else None,
                    },
                )
            )
            self.db.commit()
            logger.exception("job failed", extra={"run_id": run_id})

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

    def _persist_products(self, tenant_id: int, run_id: int, records: list[dict], *, provider) -> int:
        for rec in records:
            self._persist_raw(tenant_id, run_id, provider.source_system(), provider.source_endpoint_for_job("sync_product_catalog"), rec)
            n = provider.normalize("sync_product_catalog", rec)
            existing = self.db.scalar(select(Product).where(Product.tenant_id == tenant_id, Product.external_id == n["external_id"]))
            if existing:
                for k, v in n.items():
                    setattr(existing, k, v)
            else:
                self.db.add(Product(tenant_id=tenant_id, **n))
            self._emit_outbox(tenant_id, "product.upserted", "product", n["external_id"], n)
        self.db.commit()
        return len(records)

    def _persist_branches(self, tenant_id: int, run_id: int, records: list[dict], *, provider) -> int:
        for rec in records:
            self._persist_raw(tenant_id, run_id, provider.source_system(), provider.source_endpoint_for_job("sync_branches"), rec)
            n = provider.normalize("sync_branches", rec)
            existing = self.db.scalar(select(Branch).where(Branch.tenant_id == tenant_id, Branch.external_id == n["external_id"]))
            if existing:
                for k, v in n.items():
                    setattr(existing, k, v)
            else:
                self.db.add(Branch(tenant_id=tenant_id, **n))
            self._emit_outbox(tenant_id, "branch.upserted", "branch", n["external_id"], n)
        self.db.commit()
        return len(records)

    def _persist_stock(self, tenant_id: int, run_id: int, records: list[dict], *, provider) -> int:
        for rec in records:
            self._persist_raw(tenant_id, run_id, provider.source_system(), provider.source_endpoint_for_job("sync_stock_snapshot"), rec)
            n = provider.normalize("sync_stock_snapshot", rec)
            self.db.add(StockSnapshot(tenant_id=tenant_id, **n))
            self._emit_outbox(tenant_id, "stock.snapshot", "stock_snapshot", f"{n['product_external_id']}:{n['branch_external_id']}", n)
        self.db.commit()
        return len(records)

    def _persist_sales(self, tenant_id: int, run_id: int, records: list[dict], *, provider) -> int:
        doc_fields = (
            "external_id", "document_type_id", "number", "branch_external_id",
            "issued_at", "customer_external_id", "net_amount", "tax_amount",
            "exempt_amount", "total_amount", "state",
        )
        for rec in records:
            self._persist_raw(tenant_id, run_id, provider.source_system(), provider.source_endpoint_for_job("sync_sales_documents"), rec)
            n = provider.normalize("sync_sales_documents", rec)
            existing = self.db.scalar(select(SalesDocument).where(SalesDocument.tenant_id == tenant_id, SalesDocument.external_id == n["external_id"]))
            if existing:
                for field in doc_fields:
                    if field in n:
                        setattr(existing, field, n[field])
                existing.lines.clear()
                for line in n["lines"]:
                    existing.lines.append(SalesDocumentLine(**line))
            else:
                doc = SalesDocument(tenant_id=tenant_id, **{k: v for k, v in n.items() if k != "lines"})
                doc.lines = [SalesDocumentLine(**line) for line in n["lines"]]
                self.db.add(doc)
            self._emit_outbox(tenant_id, "sales_document.upserted", "sales_document", n["external_id"], n)
        self.db.commit()
        return len(records)
