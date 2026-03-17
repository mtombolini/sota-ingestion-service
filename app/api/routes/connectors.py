"""Connector management endpoints (CRUD, check, primary, jobs, sync)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.connectors.base import ConnectorMode
from app.core.database import get_db
from app.core.utils import clean_string
from app.jobs.tasks import execute_run
from app.models import (
    IntegrationConnection,
    IntegrationError,
    IntegrationJob,
    IntegrationJobRun,
    IntegrationOutboxEvent,
)
from app.providers import provider_registry
from app.schemas.admin import (
    AdminConnectionResponse,
    ConnectorBatchRunResponse,
    ConnectorConfigUpdate,
    ConnectorCreateRequest,
    ConnectorJobsResponse,
    ConnectorModeUpdate,
    HealthResponse,
    OverviewConnectionResponse,
    ProviderJobResponse,
    ProviderResponse,
    TenantOverviewResponse,
    TenantResponse,
)
from app.secrets import get_secret_store
from app.services.ingestion_service import IngestionService

from app.api.helpers import (
    actor_name,
    connection_for_tenant,
    connection_health_stats,
    connection_to_response,
    count_provider_connections,
    ensure_unique_connection_name,
    has_primary_connection,
    job_response,
    jobs_for_connection,
    next_connection_name,
    parse_mode_or_400,
    provider_or_400,
    reconcile_jobs_for_connections,
    record_audit,
    record_connection_error,
    resolve_tenant,
    run_response,
    set_primary_connection,
)

router = APIRouter()


class JobActivationRequest(BaseModel):
    enabled: bool = True


@router.get("/health", response_model=HealthResponse)
def healthcheck() -> HealthResponse:
    return HealthResponse(status="ok", service="sota-ingestion-service")


@router.get("/providers", response_model=list[ProviderResponse])
def list_providers() -> list[ProviderResponse]:
    return [
        ProviderResponse(
            key=provider.key,
            display_name=provider.display_name,
            description=provider.description,
            environments=list(provider.environments),
            default_environment=provider.default_environment,
            default_base_urls={
                ConnectorMode.MOCK.value: provider.default_base_url(mode=ConnectorMode.MOCK),
                ConnectorMode.REAL.value: provider.default_base_url(mode=ConnectorMode.REAL),
            },
            docs_url=provider.docs_url,
            jobs=[
                ProviderJobResponse(job_type=job.job_type, label=job.label, description=job.description)
                for job in provider.jobs
            ],
        )
        for provider in provider_registry.all()
    ]


@router.get("/overview", response_model=TenantOverviewResponse)
def tenant_overview(tenant_id: int | None = None, db: Session = Depends(get_db)) -> TenantOverviewResponse:
    tenant = resolve_tenant(db, tenant_id)
    tenant_schema = TenantResponse(id=tenant.id, slug=tenant.slug, name=tenant.name, is_active=tenant.is_active)
    connections = db.scalars(
        select(IntegrationConnection)
        .where(IntegrationConnection.tenant_id == tenant.id)
        .order_by(IntegrationConnection.provider, IntegrationConnection.priority, IntegrationConnection.id)
    ).all()
    if reconcile_jobs_for_connections(db, list(connections)):
        db.commit()
        connections = db.scalars(
            select(IntegrationConnection)
            .where(IntegrationConnection.tenant_id == tenant.id)
            .order_by(IntegrationConnection.provider, IntegrationConnection.priority, IntegrationConnection.id)
        ).all()
    overview_connections = []
    healthy = 0
    canonical_jobs = [job for conn in connections for job in jobs_for_connection(db, conn)]
    for conn in connections:
        stats = connection_health_stats(db, conn)
        if conn.status == "healthy":
            healthy += 1
        provider = provider_or_400(conn.provider)
        overview_connections.append(
            OverviewConnectionResponse(
                connection_id=conn.id,
                provider=conn.provider,
                provider_label=provider.display_name,
                name=conn.name,
                environment=conn.environment,
                mode=ConnectorMode(conn.mode),
                status=conn.status,
                is_primary=conn.is_primary,
                jobs_enabled=stats.jobs_enabled,
                jobs_total=stats.jobs_total,
                last_sync_at=stats.last_sync_at,
                last_run_status=stats.last_run_status,
                recent_error_count=stats.recent_error_count,
            )
        )

    totals = {
        "connections_total": len(connections),
        "connections_healthy": healthy,
        "connections_primary": sum(1 for conn in connections if conn.is_primary),
        "jobs_total": len(canonical_jobs),
        "jobs_enabled": sum(1 for job in canonical_jobs if job.is_enabled),
        "errors_recent": int(db.scalar(select(func.count()).select_from(IntegrationError).where(IntegrationError.tenant_id == tenant.id)) or 0),
        "outbox_pending": int(
            db.scalar(
                select(func.count()).select_from(IntegrationOutboxEvent).where(
                    IntegrationOutboxEvent.tenant_id == tenant.id,
                    IntegrationOutboxEvent.status == "pending",
                )
            )
            or 0
        ),
    }
    return TenantOverviewResponse(tenant=tenant_schema, totals=totals, providers=overview_connections)


@router.get("/connectors", response_model=list[AdminConnectionResponse])
def list_connectors(tenant_id: int | None = None, db: Session = Depends(get_db)) -> list[AdminConnectionResponse]:
    tenant = resolve_tenant(db, tenant_id)
    conns = db.scalars(
        select(IntegrationConnection)
        .where(IntegrationConnection.tenant_id == tenant.id)
        .order_by(IntegrationConnection.provider, IntegrationConnection.priority, IntegrationConnection.id)
    ).all()
    if reconcile_jobs_for_connections(db, list(conns)):
        db.commit()
        conns = db.scalars(
            select(IntegrationConnection)
            .where(IntegrationConnection.tenant_id == tenant.id)
            .order_by(IntegrationConnection.provider, IntegrationConnection.priority, IntegrationConnection.id)
        ).all()
    return [connection_to_response(db, conn) for conn in conns]


@router.post("/connectors", response_model=AdminConnectionResponse)
def create_connector(
    body: ConnectorCreateRequest,
    request: Request,
    tenant_id: int | None = None,
    db: Session = Depends(get_db),
) -> AdminConnectionResponse:
    tenant = resolve_tenant(db, tenant_id)
    provider = provider_or_400(body.provider)
    payload = body.model_dump(exclude_unset=True)
    name = clean_string(body.name) or next_connection_name(db, tenant.id, body.provider)
    ensure_unique_connection_name(db, tenant.id, body.provider, name)

    mode = body.mode
    conn = IntegrationConnection(
        tenant_id=tenant.id,
        provider=body.provider,
        name=name,
        mode=mode.value,
        environment=clean_string(body.environment) or ("mock" if mode == ConnectorMode.MOCK else provider.default_environment),
        base_url=clean_string(body.base_url) or provider.default_base_url(mode=mode),
        status="mock" if mode == ConnectorMode.MOCK else "config_incomplete",
        priority=body.priority or (100 + count_provider_connections(db, tenant.id, body.provider)),
        is_primary=False,
        is_active=True,
        config_payload=body.config_payload,
    )
    db.add(conn)
    db.flush()

    message = provider.apply_configuration(db, conn, payload | {"name": name}, secret_store=get_secret_store())
    should_be_primary = body.is_primary or not has_primary_connection(db, tenant.id, body.provider)
    set_primary_connection(db, conn, make_primary=should_be_primary)
    reconcile_jobs_for_connections(db, [conn], enabled=False)
    record_audit(
        db,
        tenant_id=tenant.id,
        actor=actor_name(request),
        action="connector.created",
        target_type="integration_connection",
        target_id=str(conn.id),
        target_label=conn.name,
        payload={"provider": conn.provider, "mode": conn.mode, "environment": conn.environment, "is_primary": conn.is_primary},
    )
    db.commit()
    db.refresh(conn)
    return connection_to_response(db, conn, message=message)


@router.patch("/connectors/{conn_id}", response_model=AdminConnectionResponse)
def update_connector(
    conn_id: int,
    body: ConnectorConfigUpdate,
    request: Request,
    tenant_id: int | None = None,
    db: Session = Depends(get_db),
) -> AdminConnectionResponse:
    tenant = resolve_tenant(db, tenant_id)
    conn = connection_for_tenant(db, tenant.id, conn_id)
    provider = provider_or_400(conn.provider)
    payload = body.model_dump(exclude_unset=True)

    next_name = clean_string(body.name) or conn.name
    ensure_unique_connection_name(db, tenant.id, conn.provider, next_name, exclude_id=conn.id)
    message = provider.apply_configuration(db, conn, payload | {"name": next_name}, secret_store=get_secret_store())
    if body.is_primary is True:
        set_primary_connection(db, conn, make_primary=True)
    elif body.is_primary is False and conn.is_primary:
        set_primary_connection(db, conn, make_primary=False)

    reconcile_jobs_for_connections(db, [conn], enabled=False)
    record_audit(
        db,
        tenant_id=tenant.id,
        actor=actor_name(request),
        action="connector.updated",
        target_type="integration_connection",
        target_id=str(conn.id),
        target_label=conn.name,
        payload={"provider": conn.provider, "mode": conn.mode, "environment": conn.environment, "status": conn.status},
    )
    db.commit()
    db.refresh(conn)
    return connection_to_response(db, conn, message=message)


@router.post("/connectors/{conn_id}/check", response_model=AdminConnectionResponse)
def check_connector(
    conn_id: int,
    request: Request,
    tenant_id: int | None = None,
    db: Session = Depends(get_db),
) -> AdminConnectionResponse:
    tenant = resolve_tenant(db, tenant_id)
    conn = connection_for_tenant(db, tenant.id, conn_id)
    reconcile_jobs_for_connections(db, [conn], enabled=False)
    provider = provider_or_400(conn.provider)
    result = provider.check_connection(db, conn, secret_store=get_secret_store())
    if not result.connected:
        record_connection_error(db, conn, message=result.message)
    record_audit(
        db,
        tenant_id=tenant.id,
        actor=actor_name(request),
        action="connector.checked",
        target_type="integration_connection",
        target_id=str(conn.id),
        target_label=conn.name,
        payload={"provider": conn.provider, "connected": result.connected, "status": conn.status},
    )
    db.commit()
    db.refresh(conn)
    return connection_to_response(db, conn, connected=result.connected, message=result.message)


@router.post("/connectors/{conn_id}/primary", response_model=AdminConnectionResponse)
def make_connector_primary(
    conn_id: int,
    request: Request,
    tenant_id: int | None = None,
    db: Session = Depends(get_db),
) -> AdminConnectionResponse:
    tenant = resolve_tenant(db, tenant_id)
    conn = connection_for_tenant(db, tenant.id, conn_id)
    set_primary_connection(db, conn, make_primary=True)
    record_audit(
        db,
        tenant_id=tenant.id,
        actor=actor_name(request),
        action="connector.primary_set",
        target_type="integration_connection",
        target_id=str(conn.id),
        target_label=conn.name,
        payload={"provider": conn.provider},
    )
    db.commit()
    db.refresh(conn)
    return connection_to_response(db, conn, message="Conexion marcada como primaria.")


@router.get("/connectors/{conn_id}/jobs", response_model=ConnectorJobsResponse)
def get_connector_jobs(conn_id: int, tenant_id: int | None = None, db: Session = Depends(get_db)) -> ConnectorJobsResponse:
    tenant = resolve_tenant(db, tenant_id)
    conn = connection_for_tenant(db, tenant.id, conn_id)
    reconcile_jobs_for_connections(db, [conn], enabled=False)
    jobs = jobs_for_connection(db, conn)
    return ConnectorJobsResponse(
        connection_id=conn.id,
        jobs_total=len(jobs),
        jobs_enabled=sum(1 for job in jobs if job.is_enabled),
        jobs=[job_response(db, job) for job in jobs],
    )


@router.post("/connectors/{conn_id}/jobs/activate", response_model=ConnectorJobsResponse)
def set_connector_jobs_enabled(
    conn_id: int,
    body: JobActivationRequest,
    request: Request,
    tenant_id: int | None = None,
    db: Session = Depends(get_db),
) -> ConnectorJobsResponse:
    tenant = resolve_tenant(db, tenant_id)
    conn = connection_for_tenant(db, tenant.id, conn_id)
    reconcile_jobs_for_connections(db, [conn], enabled=body.enabled)
    jobs = jobs_for_connection(db, conn)
    for job in jobs:
        job.is_enabled = body.enabled
    record_audit(
        db,
        tenant_id=tenant.id,
        actor=actor_name(request),
        action="connector.jobs_toggled",
        target_type="integration_connection",
        target_id=str(conn.id),
        target_label=conn.name,
        payload={"enabled": body.enabled, "job_count": len(jobs)},
    )
    db.commit()
    jobs = jobs_for_connection(db, conn)
    return ConnectorJobsResponse(
        connection_id=conn.id,
        jobs_total=len(jobs),
        jobs_enabled=sum(1 for job in jobs if job.is_enabled),
        jobs=[job_response(db, job) for job in jobs],
    )


@router.post("/connectors/{conn_id}/sync", response_model=ConnectorBatchRunResponse)
def queue_connector_sync(
    conn_id: int,
    request: Request,
    tenant_id: int | None = None,
    db: Session = Depends(get_db),
) -> ConnectorBatchRunResponse:
    tenant = resolve_tenant(db, tenant_id)
    conn = connection_for_tenant(db, tenant.id, conn_id)
    jobs = jobs_for_connection(db, conn)
    enabled_jobs = [job for job in jobs if job.is_enabled]
    if not enabled_jobs:
        raise HTTPException(status_code=400, detail="No hay jobs habilitados para esta conexion. Activalos antes de correr el sync inicial.")

    service = IngestionService(db)
    queued_runs: list[IntegrationJobRun] = []
    for job in enabled_jobs:
        run = service.trigger_job(job.id, tenant_id=tenant.id)
        execute_run.delay(run.id)
        queued_runs.append(run)

    record_audit(
        db,
        tenant_id=tenant.id,
        actor=actor_name(request),
        action="connector.sync_queued",
        target_type="integration_connection",
        target_id=str(conn.id),
        target_label=conn.name,
        payload={"queued_runs": [run.id for run in queued_runs]},
    )
    db.commit()
    return ConnectorBatchRunResponse(
        connection_id=conn.id,
        queued_runs=[run_response(db, run) for run in queued_runs],
        message=f"Se encolaron {len(queued_runs)} jobs para {conn.name}.",
    )


@router.patch("/connectors/{conn_id}/mode", response_model=AdminConnectionResponse)
def set_connector_mode(
    conn_id: int,
    body: ConnectorModeUpdate,
    request: Request,
    tenant_id: int | None = None,
    db: Session = Depends(get_db),
) -> AdminConnectionResponse:
    update_payload = ConnectorConfigUpdate(
        mode=parse_mode_or_400(body.mode),
        base_url=body.base_url,
        api_key=body.api_key,
        secret_ref=body.secret_ref,
    )
    response = update_connector(conn_id, update_payload, request, tenant_id=tenant_id, db=db)
    if not body.check_connection:
        return response
    return check_connector(conn_id, request, tenant_id=tenant_id, db=db)
