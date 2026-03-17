"""Job runs, errors, audit and mapping endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import desc, or_, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.jobs.tasks import execute_run
from app.models import (
    AdminAuditLog,
    IntegrationConnection,
    IntegrationError,
    IntegrationJob,
    IntegrationJobRun,
    IntegrationMapping,
    IntegrationRawObject,
)
from app.schemas.admin import (
    AuditLogResponse,
    ErrorResponse,
    JobResponse,
    JobRunResponse,
    MappingResponse,
    RunDetailResponse,
    RunRawObjectResponse,
    RunStepResponse,
)
from app.services.ingestion_service import IngestionService

from app.api.helpers import (
    actor_name,
    job_response,
    reconcile_jobs_for_connections,
    resolve_tenant,
    run_response,
    jobs_for_connection,
)

router = APIRouter()


@router.get("/jobs", response_model=list[JobResponse])
def list_jobs(tenant_id: int | None = None, db: Session = Depends(get_db)) -> list[JobResponse]:
    tenant = resolve_tenant(db, tenant_id)
    connections = db.scalars(select(IntegrationConnection).where(IntegrationConnection.tenant_id == tenant.id)).all()
    if reconcile_jobs_for_connections(db, list(connections)):
        db.commit()
    jobs: list[IntegrationJob] = []
    for conn in sorted(connections, key=lambda item: (item.provider, item.priority, item.id)):
        jobs.extend(jobs_for_connection(db, conn))
    return [job_response(db, job) for job in jobs]


@router.post("/jobs/{job_id}/runs", response_model=JobRunResponse)
def trigger_job(job_id: int, request: Request, tenant_id: int | None = None, db: Session = Depends(get_db)) -> JobRunResponse:
    tenant = resolve_tenant(db, tenant_id)
    service = IngestionService(db)
    try:
        run = service.trigger_job(job_id, tenant_id=tenant.id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    execute_run.delay(run.id)
    from app.api.helpers import record_audit
    record_audit(
        db,
        tenant_id=tenant.id,
        actor=actor_name(request),
        action="job.run_queued",
        target_type="integration_job",
        target_id=str(job_id),
        target_label=f"job #{job_id}",
        payload={"run_id": run.id},
    )
    db.commit()
    return run_response(db, run)


@router.get("/runs", response_model=list[JobRunResponse])
def list_runs(limit: int = 30, tenant_id: int | None = None, db: Session = Depends(get_db)) -> list[JobRunResponse]:
    tenant = resolve_tenant(db, tenant_id)
    runs = db.scalars(
        select(IntegrationJobRun)
        .join(IntegrationJob, IntegrationJob.id == IntegrationJobRun.job_id)
        .where(IntegrationJob.tenant_id == tenant.id)
        .order_by(desc(IntegrationJobRun.id))
        .limit(limit)
    ).all()
    return [run_response(db, run) for run in runs]


@router.get("/runs/{run_id}", response_model=RunDetailResponse)
def get_run_detail(run_id: int, tenant_id: int | None = None, db: Session = Depends(get_db)) -> RunDetailResponse:
    tenant = resolve_tenant(db, tenant_id)
    run = db.get(IntegrationJobRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")

    job = db.get(IntegrationJob, run.job_id)
    if job is None or job.tenant_id != tenant.id:
        raise HTTPException(status_code=404, detail="run not found")

    raw_rows = db.scalars(
        select(IntegrationRawObject)
        .where(IntegrationRawObject.job_run_id == run.id)
        .order_by(IntegrationRawObject.id)
    ).all()
    steps_by_endpoint: dict[str, list[IntegrationRawObject]] = {}
    for row in raw_rows:
        steps_by_endpoint.setdefault(row.endpoint, []).append(row)

    errors = db.scalars(
        select(IntegrationError)
        .where(IntegrationError.job_run_id == run.id)
        .order_by(IntegrationError.id)
    ).all()

    return RunDetailResponse(
        run=run_response(db, run),
        errors=[
            ErrorResponse(
                id=error.id,
                tenant_id=error.tenant_id,
                job_run_id=error.job_run_id,
                object_name=error.object_name,
                message=error.message,
                severity=error.severity,
                payload=error.payload,
                created_at=error.created_at,
            )
            for error in errors
        ],
        steps=[
            RunStepResponse(
                endpoint=endpoint,
                record_count=len(rows),
                raw_objects=[
                    RunRawObjectResponse(
                        id=row.id,
                        endpoint=row.endpoint,
                        checksum=row.checksum,
                        fetched_at=row.fetched_at,
                        payload=row.payload,
                    )
                    for row in rows
                ],
            )
            for endpoint, rows in steps_by_endpoint.items()
        ],
    )


@router.get("/errors", response_model=list[ErrorResponse])
def list_errors(limit: int = 30, tenant_id: int | None = None, db: Session = Depends(get_db)) -> list[ErrorResponse]:
    tenant = resolve_tenant(db, tenant_id)
    errors = db.scalars(
        select(IntegrationError)
        .where(IntegrationError.tenant_id == tenant.id)
        .order_by(desc(IntegrationError.id))
        .limit(limit)
    ).all()
    return [
        ErrorResponse(
            id=error.id,
            tenant_id=error.tenant_id,
            job_run_id=error.job_run_id,
            object_name=error.object_name,
            message=error.message,
            severity=error.severity,
            payload=error.payload,
            created_at=error.created_at,
        )
        for error in errors
    ]


@router.get("/audit", response_model=list[AuditLogResponse])
def list_audit(limit: int = 40, tenant_id: int | None = None, db: Session = Depends(get_db)) -> list[AuditLogResponse]:
    tenant = resolve_tenant(db, tenant_id)
    rows = db.scalars(
        select(AdminAuditLog)
        .where(or_(AdminAuditLog.tenant_id == tenant.id, AdminAuditLog.tenant_id.is_(None)))
        .order_by(desc(AdminAuditLog.id))
        .limit(limit)
    ).all()
    return [
        AuditLogResponse(
            id=row.id,
            tenant_id=row.tenant_id,
            actor=row.actor,
            action=row.action,
            target_type=row.target_type,
            target_id=row.target_id,
            target_label=row.target_label,
            payload=row.payload,
            created_at=row.created_at,
        )
        for row in rows
    ]


@router.get("/mappings", response_model=list[MappingResponse])
def list_mappings(tenant_id: int | None = None, db: Session = Depends(get_db)) -> list[MappingResponse]:
    tenant = resolve_tenant(db, tenant_id)
    mappings = db.scalars(
        select(IntegrationMapping)
        .where(IntegrationMapping.tenant_id == tenant.id)
        .order_by(IntegrationMapping.provider, IntegrationMapping.object_name, IntegrationMapping.id)
    ).all()
    return [
        MappingResponse(
            id=m.id,
            tenant_id=m.tenant_id,
            connection_id=m.connection_id,
            provider=m.provider,
            object_name=m.object_name,
            version=m.version,
            mapping_payload=m.mapping_payload,
            is_active=m.is_active,
        )
        for m in mappings
    ]
