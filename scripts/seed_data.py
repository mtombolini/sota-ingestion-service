from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import IntegrationConnection, IntegrationJob, IntegrationMapping, Tenant


def main():
    db = SessionLocal()
    try:
        tenant = db.scalar(select(Tenant).where(Tenant.slug == "demo-retail"))
        if not tenant:
            tenant = Tenant(slug="demo-retail", name="Demo Retail")
            db.add(tenant)
            db.flush()

        conn = db.scalar(select(IntegrationConnection).where(IntegrationConnection.tenant_id == tenant.id, IntegrationConnection.provider == "bsale"))
        if not conn:
            conn = IntegrationConnection(tenant_id=tenant.id, provider="bsale", mode="mock", base_url="http://mock-bsale-api:8010/v1", secret_ref="mock-token")
            db.add(conn)
            db.flush()

        job_types = ["sync_product_catalog", "sync_stock_snapshot", "sync_sales_documents", "sync_branches"]
        existing = {j.job_type for j in db.scalars(select(IntegrationJob).where(IntegrationJob.tenant_id == tenant.id)).all()}
        for jt in job_types:
            if jt not in existing:
                db.add(IntegrationJob(tenant_id=tenant.id, connection_id=conn.id, job_type=jt, schedule=None))

        for obj in ["products", "stocks", "sales_documents", "branches"]:
            m = db.scalar(select(IntegrationMapping).where(IntegrationMapping.tenant_id == tenant.id, IntegrationMapping.object_name == obj))
            if not m:
                db.add(IntegrationMapping(tenant_id=tenant.id, provider="bsale", object_name=obj, version="v1", mapping_payload={"strategy": "static-approved", "notes": "onboarding mapping"}))

        db.commit()
        print("seed completed")
    finally:
        db.close()


if __name__ == "__main__":
    main()
