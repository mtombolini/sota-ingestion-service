import os

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import IntegrationConnection, IntegrationJob, IntegrationMapping, Tenant


def _seed_enabled() -> bool:
    return os.getenv("SEED_DEMO_DATA", "").strip().lower() in {"1", "true", "yes", "on"}


def main():
    if not _seed_enabled():
        print("seed skipped (SEED_DEMO_DATA disabled)")
        return

    db = SessionLocal()
    try:
        tenant = db.scalar(select(Tenant).where(Tenant.slug == "demo-retail"))
        if not tenant:
            tenant = Tenant(slug="demo-retail", name="Demo Retail")
            db.add(tenant)
            db.flush()

        conn = db.scalar(select(IntegrationConnection).where(IntegrationConnection.tenant_id == tenant.id, IntegrationConnection.provider == "bsale"))
        if not conn:
            conn = IntegrationConnection(
                tenant_id=tenant.id,
                provider="bsale",
                name="Bsale principal",
                mode="mock",
                environment="mock",
                base_url="http://mock-bsale-api:8010/v1",
                secret_ref="mock-token",
                status="mock",
                is_primary=True,
                priority=100,
            )
            db.add(conn)
            db.flush()
        else:
            if not conn.name:
                conn.name = "Bsale principal"
            if not getattr(conn, "environment", None):
                conn.environment = "mock" if conn.mode == "mock" else "production"
            if not conn.status:
                conn.status = "mock" if conn.mode == "mock" else "configured"
            if not getattr(conn, "priority", None):
                conn.priority = 100
            if getattr(conn, "is_primary", None) is None:
                conn.is_primary = True

        job_types = [
            "sync_product_catalog",
            "sync_locations",
            "sync_stock",
            "sync_sales_orders",
            "sync_customers",
            "sync_document_types",
        ]
        existing = {j.job_type for j in db.scalars(select(IntegrationJob).where(IntegrationJob.tenant_id == tenant.id)).all()}
        for jt in job_types:
            if jt not in existing:
                db.add(IntegrationJob(tenant_id=tenant.id, connection_id=conn.id, job_type=jt, schedule=None))

        for obj in ["products", "variants", "locations", "stock", "stock_movements", "sales_orders", "customers", "document_types"]:
            m = db.scalar(select(IntegrationMapping).where(IntegrationMapping.tenant_id == tenant.id, IntegrationMapping.object_name == obj))
            if not m:
                db.add(IntegrationMapping(tenant_id=tenant.id, provider="bsale", object_name=obj, version="v1", mapping_payload={"strategy": "static-approved", "notes": "onboarding mapping"}))

        db.commit()
        print("seed completed")
    finally:
        db.close()


if __name__ == "__main__":
    main()
