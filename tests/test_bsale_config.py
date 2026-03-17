from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.helpers import jobs_for_connection as _jobs_for_connection, reconcile_jobs_for_connections as _reconcile_jobs_for_connections
from app.api.routes.jobs import get_run_detail
from app.connectors.base import ConnectorMode
from app.connectors.bsale import build_bsale_config
from app.models import Base, IntegrationConnection, IntegrationError, IntegrationJob, IntegrationJobRun, IntegrationRawObject, Tenant


def test_build_bsale_config_normalizes_legacy_host():
    config = build_bsale_config(
        mode=ConnectorMode.REAL,
        base_url="https://api.bsale.cl/v1",
        api_key="demo-token",
    )

    assert config.base_url == "https://api.bsale.io/v1"


def test_build_bsale_config_appends_v1_for_official_host():
    config = build_bsale_config(
        mode=ConnectorMode.REAL,
        base_url="https://api.bsale.io",
        api_key="demo-token",
    )

    assert config.base_url == "https://api.bsale.io/v1"


def test_reconcile_jobs_for_legacy_connection_creates_missing_jobs():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)

    with Session() as db:
        tenant = Tenant(slug="demo-retail", name="Demo Retail")
        db.add(tenant)
        db.flush()

        conn = IntegrationConnection(
            tenant_id=tenant.id,
            provider="bsale",
            name="Bsale principal",
            mode="real",
            environment="production",
            base_url="https://api.bsale.io/v1",
            status="configured",
            is_primary=True,
            priority=100,
            is_active=True,
        )
        db.add(conn)
        db.commit()

        created = _reconcile_jobs_for_connections(db, [conn])
        db.commit()

        jobs = db.query(IntegrationJob).filter_by(connection_id=conn.id).all()

        assert created == 6
        assert len(jobs) == 6
        assert {job.job_type for job in jobs} == {
            "sync_product_catalog",
            "sync_locations",
            "sync_stock",
            "sync_sales_orders",
            "sync_customers",
            "sync_document_types",
        }


def test_jobs_for_connection_filters_legacy_and_duplicate_jobs():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)

    with Session() as db:
        tenant = Tenant(slug="demo-retail", name="Demo Retail")
        db.add(tenant)
        db.flush()

        conn = IntegrationConnection(
            tenant_id=tenant.id,
            provider="bsale",
            name="Bsale principal",
            mode="real",
            environment="production",
            base_url="https://api.bsale.io/v1",
            status="configured",
            is_primary=True,
            priority=100,
            is_active=True,
        )
        db.add(conn)
        db.flush()

        db.add_all(
            [
                IntegrationJob(tenant_id=tenant.id, connection_id=conn.id, job_type="sync_product_catalog", is_enabled=True),
                IntegrationJob(tenant_id=tenant.id, connection_id=conn.id, job_type="sync_product_catalog", is_enabled=False),
                IntegrationJob(tenant_id=tenant.id, connection_id=conn.id, job_type="sync_stock_snapshot", is_enabled=True),
                IntegrationJob(tenant_id=tenant.id, connection_id=conn.id, job_type="sync_branches", is_enabled=True),
            ]
        )
        db.commit()

        jobs = _jobs_for_connection(db, conn)

        assert len(jobs) == 1
        assert jobs[0].job_type == "sync_product_catalog"


def test_reconcile_jobs_replaces_legacy_bsale_jobs_with_canonical_ones():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)

    with Session() as db:
        tenant = Tenant(slug="demo-retail", name="Demo Retail")
        db.add(tenant)
        db.flush()

        conn = IntegrationConnection(
            tenant_id=tenant.id,
            provider="bsale",
            name="Bsale principal",
            mode="real",
            environment="production",
            base_url="https://api.bsale.io/v1",
            status="configured",
            is_primary=True,
            priority=100,
            is_active=True,
        )
        db.add(conn)
        db.flush()

        db.add_all(
            [
                IntegrationJob(tenant_id=tenant.id, connection_id=conn.id, job_type="sync_stock_snapshot", is_enabled=True),
                IntegrationJob(tenant_id=tenant.id, connection_id=conn.id, job_type="sync_sales_documents", is_enabled=True),
                IntegrationJob(tenant_id=tenant.id, connection_id=conn.id, job_type="sync_branches", is_enabled=False),
            ]
        )
        db.commit()

        changed = _reconcile_jobs_for_connections(db, [conn])
        db.commit()

        jobs = db.query(IntegrationJob).filter_by(connection_id=conn.id).all()
        job_types = {job.job_type for job in jobs}

        assert changed >= 1
        assert "sync_stock_snapshot" not in job_types
        assert "sync_sales_documents" not in job_types
        assert "sync_branches" not in job_types
        assert job_types == {
            "sync_product_catalog",
            "sync_locations",
            "sync_stock",
            "sync_sales_orders",
            "sync_customers",
            "sync_document_types",
        }


def test_get_run_detail_returns_steps_and_errors():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)

    with Session() as db:
        tenant = Tenant(slug="demo-retail", name="Demo Retail")
        db.add(tenant)
        db.flush()

        conn = IntegrationConnection(
            tenant_id=tenant.id,
            provider="bsale",
            name="Bsale principal",
            mode="real",
            environment="production",
            base_url="https://api.bsale.io/v1",
            status="configured",
            is_primary=True,
            priority=100,
            is_active=True,
        )
        db.add(conn)
        db.flush()

        job = IntegrationJob(tenant_id=tenant.id, connection_id=conn.id, job_type="sync_stock", is_enabled=True)
        db.add(job)
        db.flush()

        run = IntegrationJobRun(job_id=job.id, status="failed", correlation_id="corr-1", records_raw=2, records_normalized=1)
        db.add(run)
        db.flush()

        db.add_all(
            [
                IntegrationRawObject(
                    tenant_id=tenant.id,
                    job_run_id=run.id,
                    source_system="bsale",
                    endpoint="stocks.json",
                    checksum="abc",
                    payload={"id": 1},
                ),
                IntegrationRawObject(
                    tenant_id=tenant.id,
                    job_run_id=run.id,
                    source_system="bsale",
                    endpoint="stocks/receptions.json",
                    checksum="def",
                    payload={"id": 2},
                ),
                IntegrationError(
                    tenant_id=tenant.id,
                    job_run_id=run.id,
                    object_name="sync_stock",
                    message="boom",
                    payload={"reason": "test"},
                ),
            ]
        )
        db.commit()

        detail = get_run_detail(run.id, tenant_id=tenant.id, db=db)

        assert detail.run.id == run.id
        assert len(detail.steps) == 2
        assert {step.endpoint for step in detail.steps} == {"stocks.json", "stocks/receptions.json"}
        assert detail.errors[0].message == "boom"
