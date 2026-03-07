from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.jobs.tasks import execute_run
from app.models import IntegrationConnection, IntegrationMapping
from app.schemas.admin import ErrorResponse, HealthResponse, JobResponse, JobRunResponse
from app.services.ingestion_service import IngestionService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/health", response_model=HealthResponse)
def healthcheck():
    return HealthResponse(status="ok", service="sota-ingestion-service")


@router.get("/connectors")
def connector_state(db: Session = Depends(get_db)):
    conns = db.scalars(select(IntegrationConnection).order_by(IntegrationConnection.id)).all()
    return [
        {"id": c.id, "tenant_id": c.tenant_id, "provider": c.provider, "mode": c.mode, "base_url": c.base_url, "is_active": c.is_active}
        for c in conns
    ]


@router.get("/jobs", response_model=list[JobResponse])
def list_jobs(db: Session = Depends(get_db)):
    return IngestionService(db).list_jobs()


@router.post("/jobs/{job_id}/runs", response_model=JobRunResponse)
def trigger_job(job_id: int, db: Session = Depends(get_db)):
    service = IngestionService(db)
    try:
        run = service.trigger_job(job_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    execute_run.delay(run.id)
    return run


@router.get("/runs", response_model=list[JobRunResponse])
def list_runs(limit: int = 30, db: Session = Depends(get_db)):
    return IngestionService(db).list_runs(limit)


@router.get("/errors", response_model=list[ErrorResponse])
def list_errors(limit: int = 30, db: Session = Depends(get_db)):
    return IngestionService(db).list_errors(limit)


@router.get("/mappings")
def list_mappings(db: Session = Depends(get_db)):
    mappings = db.scalars(select(IntegrationMapping).order_by(IntegrationMapping.id)).all()
    return [
        {
            "id": m.id,
            "tenant_id": m.tenant_id,
            "provider": m.provider,
            "object_name": m.object_name,
            "version": m.version,
            "is_active": m.is_active,
            "mapping_payload": m.mapping_payload,
        }
        for m in mappings
    ]
