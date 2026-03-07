import hashlib
import json
import logging
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.connectors.bsale import BsaleConnector
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
from app.normalizers.bsale import normalize_branch, normalize_product, normalize_sales_document, normalize_stock

logger = logging.getLogger(__name__)


class IngestionService:
    def __init__(self, db: Session):
        self.db = db

    def list_jobs(self) -> list[IntegrationJob]:
        return list(self.db.scalars(select(IntegrationJob).order_by(IntegrationJob.id)).all())

    def list_runs(self, limit: int = 30) -> list[IntegrationJobRun]:
        return list(self.db.scalars(select(IntegrationJobRun).order_by(desc(IntegrationJobRun.id)).limit(limit)).all())

    def list_errors(self, limit: int = 30) -> list[IntegrationError]:
        return list(self.db.scalars(select(IntegrationError).order_by(desc(IntegrationError.id)).limit(limit)).all())

    def trigger_job(self, job_id: int) -> IntegrationJobRun:
        job = self.db.get(IntegrationJob, job_id)
        if not job:
            raise ValueError(f"job {job_id} not found")
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
        connection = self.db.get(IntegrationConnection, job.connection_id)
        connector = BsaleConnector(connection.base_url, connection.secret_ref or "mock-token")

        run.status = "running"
        run.started_at = datetime.utcnow()
        self.db.commit()

        try:
            if job.job_type == "sync_product_catalog":
                records = await connector.fetch_products()
                run.records_raw = len(records)
                run.records_normalized = self._persist_products(tenant_id, run.id, records)
            elif job_type == "sync_stock_snapshot":
                records = await connector.fetch_stock()
                run.records_raw = len(records)
                run.records_normalized = self._persist_stock(tenant_id, run.id, records)
            elif job_type == "sync_sales_documents":
                records = await connector.fetch_sales_documents()
                run.records_raw = len(records)
                run.records_normalized = self._persist_sales(tenant_id, run.id, records)
            elif job_type == "sync_branches":
                records = await connector.fetch_branches()
                run.records_raw = len(records)
                run.records_normalized = self._persist_branches(tenant_id, run.id, records)
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
            self.db.add(IntegrationError(tenant_id=tenant_id, job_run_id=run_id, object_name=job_type, message=str(exc)))
            self.db.commit()
            logger.exception("job failed", extra={"run_id": run_id})

    def _persist_raw(self, tenant_id: int, run_id: int, endpoint: str, payload: dict) -> None:
        safe_payload = self._json_safe(payload)
        checksum = hashlib.sha256(json.dumps(safe_payload, sort_keys=True).encode()).hexdigest()
        self.db.add(
            IntegrationRawObject(
                tenant_id=tenant_id,
                job_run_id=run_id,
                source_system="bsale",
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

    def _persist_products(self, tenant_id: int, run_id: int, records: list[dict]) -> int:
        for rec in records:
            self._persist_raw(tenant_id, run_id, "products.json", rec)
            n = normalize_product(rec)
            existing = self.db.scalar(select(Product).where(Product.tenant_id == tenant_id, Product.external_id == n["external_id"]))
            if existing:
                for k, v in n.items():
                    setattr(existing, k, v)
            else:
                self.db.add(Product(tenant_id=tenant_id, **n))
            self._emit_outbox(tenant_id, "product.upserted", "product", n["external_id"], n)
        self.db.commit()
        return len(records)

    def _persist_branches(self, tenant_id: int, run_id: int, records: list[dict]) -> int:
        for rec in records:
            self._persist_raw(tenant_id, run_id, "offices.json", rec)
            n = normalize_branch(rec)
            existing = self.db.scalar(select(Branch).where(Branch.tenant_id == tenant_id, Branch.external_id == n["external_id"]))
            if existing:
                for k, v in n.items():
                    setattr(existing, k, v)
            else:
                self.db.add(Branch(tenant_id=tenant_id, **n))
            self._emit_outbox(tenant_id, "branch.upserted", "branch", n["external_id"], n)
        self.db.commit()
        return len(records)

    def _persist_stock(self, tenant_id: int, run_id: int, records: list[dict]) -> int:
        for rec in records:
            self._persist_raw(tenant_id, run_id, "stocks.json", rec)
            n = normalize_stock(rec)
            self.db.add(StockSnapshot(tenant_id=tenant_id, **n))
            self._emit_outbox(tenant_id, "stock.snapshot", "stock_snapshot", f"{n['product_external_id']}:{n['branch_external_id']}", n)
        self.db.commit()
        return len(records)

    def _persist_sales(self, tenant_id: int, run_id: int, records: list[dict]) -> int:
        for rec in records:
            self._persist_raw(tenant_id, run_id, "documents/sales.json", rec)
            n = normalize_sales_document(rec)
            existing = self.db.scalar(select(SalesDocument).where(SalesDocument.tenant_id == tenant_id, SalesDocument.external_id == n["external_id"]))
            if existing:
                existing.issued_at = n["issued_at"]
                existing.total_amount = n["total_amount"]
                existing.branch_external_id = n["branch_external_id"]
                existing.customer_external_id = n["customer_external_id"]
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
