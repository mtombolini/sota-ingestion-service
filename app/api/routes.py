from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session

from app.connectors.base import ConnectorConfigurationError, ConnectorMode
from app.connectors.bsale import bsale_connector
from app.core.database import get_db
from app.jobs.tasks import execute_run
from app.models import (
    AdminAuditLog,
    Branch,
    Client,
    ClientAddress,
    ClientAttribute,
    ClientContact,
    DocumentType,
    IntegrationConnection,
    IntegrationError,
    IntegrationJob,
    IntegrationJobRun,
    IntegrationMapping,
    IntegrationOutboxEvent,
    IntegrationRawObject,
    IntegrationSecret,
    Product,
    ProductTax,
    ProductVariant,
    SalesDocument,
    SalesDocumentLine,
    StockSnapshot,
    Tenant,
)
from app.providers import provider_registry
from app.schemas.admin import (
    AdminConnectionResponse,
    AuditLogResponse,
    ConnectorBatchRunResponse,
    ConnectorConfigUpdate,
    ConnectorCreateRequest,
    ConnectorJobsResponse,
    ConnectorModeUpdate,
    ErrorResponse,
    HealthResponse,
    JobResponse,
    JobRunResponse,
    MappingResponse,
    OverviewConnectionResponse,
    ProviderJobResponse,
    ProviderResponse,
    TenantCreateRequest,
    TenantOverviewResponse,
    TenantResponse,
    TenantUpdateRequest,
)
from app.secrets import get_secret_store
from app.services.ingestion_service import IngestionService

admin_router = APIRouter(prefix="/admin", tags=["admin"])
connectors_router = APIRouter(prefix="/connectors", tags=["connectors"])
router = APIRouter()


class BsaleUpdateRequest(BaseModel):
    mode: ConnectorMode = Field(description="mock o real")
    base_url: str | None = Field(default=None, description="URL base a usar con este modo")
    api_key: str | None = Field(default=None, description="Token Bsale para modo real")
    check_connection: bool = Field(default=True, description="Si true, intenta conectar tras actualizar")


class BsaleStatusResponse(BaseModel):
    connector: str
    mode: ConnectorMode
    base_url: str
    api_key: str | None
    connected: bool | None = None
    message: str | None = None


class JobActivationRequest(BaseModel):
    enabled: bool = True


class ConnectionHealthStats(BaseModel):
    jobs_total: int
    jobs_enabled: int
    successful_runs: int
    failed_runs: int
    recent_error_count: int
    last_sync_at: datetime | None
    last_run_status: str | None


JOB_LABELS = {
    "sync_product_catalog": "Catalogo",
    "sync_customers": "Clientes",
    "sync_document_types": "Tipos de documento",
    "sync_stock_snapshot": "Stock",
    "sync_sales_documents": "Ventas",
    "sync_branches": "Sucursales",
}


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    candidate = value.strip()
    return candidate or None


def _parse_mode_or_400(value: str) -> ConnectorMode:
    try:
        return ConnectorMode(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="mode must be 'mock' or 'real'") from exc


def _resolve_tenant(db: Session, tenant_id: int | None) -> Tenant:
    if tenant_id is not None:
        tenant = db.get(Tenant, tenant_id)
        if tenant is None:
            raise HTTPException(status_code=404, detail=f"tenant {tenant_id} not found")
        return tenant

    tenant = db.scalar(select(Tenant).where(Tenant.is_active.is_(True)).order_by(Tenant.id))
    if tenant is None:
        raise HTTPException(status_code=404, detail="no tenants configured")
    return tenant


def _connection_for_tenant(db: Session, tenant_id: int, conn_id: int) -> IntegrationConnection:
    conn = db.get(IntegrationConnection, conn_id)
    if conn is None or conn.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="connector not found")
    return conn


def _provider_or_400(provider_key: str):
    try:
        return provider_registry.get(provider_key)
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _actor_name(request: Request) -> str:
    return request.headers.get("x-actor", "ui")


def _record_audit(
    db: Session,
    *,
    tenant_id: int | None,
    actor: str,
    action: str,
    target_type: str,
    target_id: str | None,
    target_label: str | None,
    payload: dict | None = None,
) -> None:
    db.add(
        AdminAuditLog(
            tenant_id=tenant_id,
            actor=actor,
            action=action,
            target_type=target_type,
            target_id=target_id,
            target_label=target_label,
            payload=payload,
        )
    )


def _count_provider_connections(db: Session, tenant_id: int, provider_key: str) -> int:
    return int(
        db.scalar(
            select(func.count())
            .select_from(IntegrationConnection)
            .where(IntegrationConnection.tenant_id == tenant_id, IntegrationConnection.provider == provider_key)
        )
        or 0
    )


def _next_connection_name(db: Session, tenant_id: int, provider_key: str) -> str:
    provider = _provider_or_400(provider_key)
    ordinal = _count_provider_connections(db, tenant_id, provider_key) + 1
    return provider.default_connection_name(ordinal=ordinal)


def _ensure_unique_connection_name(db: Session, tenant_id: int, provider_key: str, name: str, *, exclude_id: int | None = None) -> None:
    stmt = select(IntegrationConnection).where(
        IntegrationConnection.tenant_id == tenant_id,
        IntegrationConnection.provider == provider_key,
        IntegrationConnection.name == name,
    )
    if exclude_id is not None:
        stmt = stmt.where(IntegrationConnection.id != exclude_id)
    if db.scalar(stmt) is not None:
        raise HTTPException(status_code=400, detail=f"connection name '{name}' already exists for provider '{provider_key}'")


def _set_primary_connection(db: Session, conn: IntegrationConnection, *, make_primary: bool) -> None:
    siblings = db.scalars(
        select(IntegrationConnection)
        .where(
            IntegrationConnection.tenant_id == conn.tenant_id,
            IntegrationConnection.provider == conn.provider,
        )
        .order_by(IntegrationConnection.priority, IntegrationConnection.id)
    ).all()
    if make_primary:
        for sibling in siblings:
            sibling.is_primary = sibling.id == conn.id
        return

    conn.is_primary = False
    for sibling in siblings:
        if sibling.id != conn.id:
            sibling.is_primary = True
            break


def _has_primary_connection(db: Session, tenant_id: int, provider_key: str) -> bool:
    return bool(
        db.scalar(
            select(IntegrationConnection.id).where(
                IntegrationConnection.tenant_id == tenant_id,
                IntegrationConnection.provider == provider_key,
                IntegrationConnection.is_primary.is_(True),
            )
        )
    )


def _provision_jobs_for_connection(db: Session, conn: IntegrationConnection, *, enabled: bool) -> list[IntegrationJob]:
    provider = _provider_or_400(conn.provider)
    existing = {
        job.job_type: job
        for job in db.scalars(select(IntegrationJob).where(IntegrationJob.connection_id == conn.id)).all()
    }
    created: list[IntegrationJob] = []
    for job_def in provider.jobs:
        job = existing.get(job_def.job_type)
        if job is not None:
            continue
        job = IntegrationJob(
            tenant_id=conn.tenant_id,
            connection_id=conn.id,
            job_type=job_def.job_type,
            is_enabled=enabled,
            schedule=None,
        )
        db.add(job)
        created.append(job)
    db.flush()
    return created


def _connection_health_stats(db: Session, conn: IntegrationConnection) -> ConnectionHealthStats:
    jobs = db.scalars(select(IntegrationJob).where(IntegrationJob.connection_id == conn.id).order_by(IntegrationJob.id)).all()
    job_ids = [job.id for job in jobs]
    jobs_total = len(jobs)
    jobs_enabled = sum(1 for job in jobs if job.is_enabled)

    last_run = None
    successful_runs = 0
    failed_runs = 0
    recent_error_count = 0

    if job_ids:
        last_run = db.scalars(
            select(IntegrationJobRun)
            .where(IntegrationJobRun.job_id.in_(job_ids))
            .order_by(desc(IntegrationJobRun.id))
            .limit(1)
        ).first()
        successful_runs = int(
            db.scalar(
                select(func.count())
                .select_from(IntegrationJobRun)
                .where(IntegrationJobRun.job_id.in_(job_ids), IntegrationJobRun.status == "success")
            )
            or 0
        )
        failed_runs = int(
            db.scalar(
                select(func.count())
                .select_from(IntegrationJobRun)
                .where(IntegrationJobRun.job_id.in_(job_ids), IntegrationJobRun.status == "failed")
            )
            or 0
        )
        run_ids = select(IntegrationJobRun.id).where(IntegrationJobRun.job_id.in_(job_ids))
        recent_error_count = int(
            db.scalar(
                select(func.count())
                .select_from(IntegrationError)
                .where(
                    IntegrationError.tenant_id == conn.tenant_id,
                    or_(
                        IntegrationError.object_name == f"{conn.provider}.connection_test",
                        IntegrationError.job_run_id.in_(run_ids),
                    ),
                )
            )
            or 0
        )
    else:
        recent_error_count = int(
            db.scalar(
                select(func.count())
                .select_from(IntegrationError)
                .where(
                    IntegrationError.tenant_id == conn.tenant_id,
                    IntegrationError.object_name == f"{conn.provider}.connection_test",
                )
            )
            or 0
        )

    return ConnectionHealthStats(
        jobs_total=jobs_total,
        jobs_enabled=jobs_enabled,
        successful_runs=successful_runs,
        failed_runs=failed_runs,
        recent_error_count=recent_error_count,
        last_sync_at=last_run.finished_at if last_run and last_run.status == "success" else (last_run.started_at if last_run else None),
        last_run_status=last_run.status if last_run else None,
    )


def _build_onboarding(conn: IntegrationConnection, stats: ConnectionHealthStats):
    configured_done = conn.mode == ConnectorMode.MOCK.value or conn.status != "config_incomplete"
    checked_done = conn.mode == ConnectorMode.MOCK.value or bool(conn.last_check_ok)
    jobs_done = stats.jobs_enabled > 0
    sync_done = stats.successful_runs > 0
    steps = [
        {
            "key": "config",
            "label": "Guardar configuracion",
            "done": configured_done,
            "detail": conn.last_check_message or "Completa URL base, credenciales y nombre de la conexion.",
        },
        {
            "key": "check",
            "label": "Probar conexion",
            "done": checked_done,
            "detail": "Valida la cuenta real contra el provider antes de habilitar jobs.",
        },
        {
            "key": "jobs",
            "label": "Activar jobs",
            "done": jobs_done,
            "detail": f"Hay {stats.jobs_enabled} de {stats.jobs_total} jobs habilitados para esta conexion.",
        },
        {
            "key": "sync",
            "label": "Sync inicial",
            "done": sync_done,
            "detail": "Corre una sincronizacion inicial para poblar datos y validar el pipeline.",
        },
    ]
    progress = int((sum(1 for step in steps if step["done"]) / len(steps)) * 100)
    next_action = next((step["label"] for step in steps if not step["done"]), None)
    return {
        "ready": checked_done and jobs_done and sync_done,
        "progress": progress,
        "next_action": next_action,
        "steps": steps,
    }


def _connection_to_response(
    db: Session,
    conn: IntegrationConnection,
    *,
    connected: bool | None = None,
    message: str | None = None,
) -> AdminConnectionResponse:
    provider = _provider_or_400(conn.provider)
    stats = _connection_health_stats(db, conn)
    return AdminConnectionResponse(
        id=conn.id,
        tenant_id=conn.tenant_id,
        provider=conn.provider,
        provider_label=provider.display_name,
        name=conn.name,
        mode=ConnectorMode(conn.mode),
        environment=conn.environment,
        base_url=conn.base_url,
        is_active=conn.is_active,
        is_primary=conn.is_primary,
        priority=conn.priority,
        has_secret=bool(conn.secret_ref),
        provider_account_id=conn.provider_account_id,
        status=conn.status,
        last_checked_at=conn.last_checked_at,
        last_check_ok=conn.last_check_ok,
        last_check_message=conn.last_check_message,
        jobs_total=stats.jobs_total,
        jobs_enabled=stats.jobs_enabled,
        last_sync_at=stats.last_sync_at,
        last_run_status=stats.last_run_status,
        recent_error_count=stats.recent_error_count,
        successful_runs=stats.successful_runs,
        failed_runs=stats.failed_runs,
        onboarding=_build_onboarding(conn, stats),
        connected=connected,
        message=message,
    )


def _job_response(db: Session, job: IntegrationJob) -> JobResponse:
    conn = db.get(IntegrationConnection, job.connection_id)
    provider = _provider_or_400(conn.provider)
    return JobResponse(
        id=job.id,
        tenant_id=job.tenant_id,
        connection_id=job.connection_id,
        connection_name=conn.name,
        provider=conn.provider,
        provider_label=provider.display_name,
        job_type=job.job_type,
        job_label=JOB_LABELS.get(job.job_type, job.job_type),
        is_enabled=job.is_enabled,
    )


def _run_response(db: Session, run: IntegrationJobRun) -> JobRunResponse:
    job = db.get(IntegrationJob, run.job_id)
    conn = db.get(IntegrationConnection, job.connection_id)
    provider = _provider_or_400(conn.provider)
    return JobRunResponse(
        id=run.id,
        job_id=run.job_id,
        connection_id=conn.id,
        connection_name=conn.name,
        provider=conn.provider,
        provider_label=provider.display_name,
        job_type=job.job_type,
        status=run.status,
        correlation_id=run.correlation_id,
        started_at=run.started_at,
        finished_at=run.finished_at,
        records_raw=run.records_raw,
        records_normalized=run.records_normalized,
    )


def _jobs_for_connection(db: Session, conn: IntegrationConnection) -> list[IntegrationJob]:
    return db.scalars(select(IntegrationJob).where(IntegrationJob.connection_id == conn.id).order_by(IntegrationJob.id)).all()


def _record_connection_error(db: Session, conn: IntegrationConnection, *, message: str) -> None:
    db.add(
        IntegrationError(
            tenant_id=conn.tenant_id,
            job_run_id=None,
            object_name=f"{conn.provider}.connection_test",
            message=message,
            severity="error",
            payload={
                "connection_id": conn.id,
                "connection_name": conn.name,
                "provider": conn.provider,
                "status": conn.status,
                "environment": conn.environment,
            },
        )
    )


def _bsale_masked_api_key() -> str | None:
    config = bsale_connector.config
    return config.masked_api_key() if config.mode == ConnectorMode.REAL else None


@admin_router.get("/health", response_model=HealthResponse)
def healthcheck() -> HealthResponse:
    return HealthResponse(status="ok", service="sota-ingestion-service")


@admin_router.get("/tenants", response_model=list[TenantResponse])
def list_tenants(db: Session = Depends(get_db)) -> list[TenantResponse]:
    tenants = db.scalars(select(Tenant).order_by(Tenant.name, Tenant.id)).all()
    return [TenantResponse(id=tenant.id, slug=tenant.slug, name=tenant.name, is_active=tenant.is_active) for tenant in tenants]


@admin_router.post("/tenants", response_model=TenantResponse, status_code=201)
def create_tenant(body: TenantCreateRequest, request: Request, db: Session = Depends(get_db)) -> TenantResponse:
    existing = db.scalars(select(Tenant).where(Tenant.slug == body.slug)).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Ya existe un tenant con slug '{body.slug}'")
    tenant = Tenant(slug=body.slug, name=body.name, is_active=True)
    db.add(tenant)
    db.flush()
    db.add(AdminAuditLog(
        tenant_id=tenant.id,
        actor=request.headers.get("x-actor", "ui"),
        action="tenant.created",
        target_type="tenant",
        target_id=str(tenant.id),
        target_label=tenant.name,
        payload={"slug": tenant.slug, "name": tenant.name},
    ))
    db.commit()
    db.refresh(tenant)
    return TenantResponse(id=tenant.id, slug=tenant.slug, name=tenant.name, is_active=tenant.is_active)


@admin_router.patch("/tenants/{tenant_id}", response_model=TenantResponse)
def update_tenant(tenant_id: int, body: TenantUpdateRequest, request: Request, db: Session = Depends(get_db)) -> TenantResponse:
    tenant = db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
    changes = {}
    if body.name is not None:
        tenant.name = body.name
        changes["name"] = body.name
    if body.is_active is not None:
        tenant.is_active = body.is_active
        changes["is_active"] = body.is_active
    if not changes:
        raise HTTPException(status_code=422, detail="Sin cambios para aplicar")
    db.add(AdminAuditLog(
        tenant_id=tenant.id,
        actor=request.headers.get("x-actor", "ui"),
        action="tenant.updated",
        target_type="tenant",
        target_id=str(tenant.id),
        target_label=tenant.name,
        payload=changes,
    ))
    db.commit()
    db.refresh(tenant)
    return TenantResponse(id=tenant.id, slug=tenant.slug, name=tenant.name, is_active=tenant.is_active)


@admin_router.delete("/tenants/{tenant_id}")
def delete_tenant(tenant_id: int, force: bool = False, request: Request = None, db: Session = Depends(get_db)):
    tenant = db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
    conn_count = db.scalar(select(func.count(IntegrationConnection.id)).where(IntegrationConnection.tenant_id == tenant_id)) or 0
    if conn_count > 0 and not force:
        raise HTTPException(status_code=409, detail=f"No se puede eliminar: el tenant tiene {conn_count} conexion(es) asociada(s). Elimina las conexiones primero o usa force=true.")
    # Save info before deletion
    tenant_name = tenant.name
    tenant_slug = tenant.slug
    # Delete all tenant-scoped data in FK-safe order
    # 1. Sales document lines (FK → sales_documents)
    sales_doc_ids = db.scalars(select(SalesDocument.id).where(SalesDocument.tenant_id == tenant_id)).all()
    if sales_doc_ids:
        db.execute(SalesDocumentLine.__table__.delete().where(SalesDocumentLine.sales_document_id.in_(sales_doc_ids)))
    # 2. Tables with FK to tenant only (or to job_runs)
    for model in (SalesDocument, StockSnapshot, ClientAttribute, ClientAddress, ClientContact, Client, ProductTax, ProductVariant, Product, DocumentType, Branch, IntegrationError, IntegrationOutboxEvent, IntegrationMapping, IntegrationSecret, AdminAuditLog):
        db.execute(model.__table__.delete().where(model.tenant_id == tenant_id))
    # 3. Raw objects (FK → job_runs) and job runs (FK → jobs)
    job_ids = db.scalars(select(IntegrationJob.id).where(IntegrationJob.tenant_id == tenant_id)).all()
    if job_ids:
        run_ids = db.scalars(select(IntegrationJobRun.id).where(IntegrationJobRun.job_id.in_(job_ids))).all()
        if run_ids:
            db.execute(IntegrationRawObject.__table__.delete().where(IntegrationRawObject.job_run_id.in_(run_ids)))
        db.execute(IntegrationJobRun.__table__.delete().where(IntegrationJobRun.job_id.in_(job_ids)))
    # 4. Jobs (FK → connections) then connections
    db.execute(IntegrationJob.__table__.delete().where(IntegrationJob.tenant_id == tenant_id))
    db.execute(IntegrationConnection.__table__.delete().where(IntegrationConnection.tenant_id == tenant_id))
    # 5. Tenant itself
    db.delete(tenant)
    # Audit log with null tenant_id since tenant no longer exists
    db.add(AdminAuditLog(
        tenant_id=None,
        actor=request.headers.get("x-actor", "ui") if request else "system",
        action="tenant.deleted",
        target_type="tenant",
        target_id=str(tenant_id),
        target_label=tenant_name,
        payload={"slug": tenant_slug, "force": force, "connections_removed": conn_count},
    ))
    db.commit()
    return {"message": f"Tenant '{tenant_name}' eliminado"}


@admin_router.get("/providers", response_model=list[ProviderResponse])
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


@admin_router.get("/overview", response_model=TenantOverviewResponse)
def tenant_overview(tenant_id: int | None = None, db: Session = Depends(get_db)) -> TenantOverviewResponse:
    tenant = _resolve_tenant(db, tenant_id)
    tenant_schema = TenantResponse(id=tenant.id, slug=tenant.slug, name=tenant.name, is_active=tenant.is_active)
    connections = db.scalars(
        select(IntegrationConnection)
        .where(IntegrationConnection.tenant_id == tenant.id)
        .order_by(IntegrationConnection.provider, IntegrationConnection.priority, IntegrationConnection.id)
    ).all()
    overview_connections = []
    healthy = 0
    for conn in connections:
        stats = _connection_health_stats(db, conn)
        if conn.status == "healthy":
            healthy += 1
        provider = _provider_or_400(conn.provider)
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
        "jobs_total": int(db.scalar(select(func.count()).select_from(IntegrationJob).where(IntegrationJob.tenant_id == tenant.id)) or 0),
        "jobs_enabled": int(
            db.scalar(
                select(func.count()).select_from(IntegrationJob).where(IntegrationJob.tenant_id == tenant.id, IntegrationJob.is_enabled.is_(True))
            )
            or 0
        ),
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


@admin_router.get("/connectors", response_model=list[AdminConnectionResponse])
def list_connectors(tenant_id: int | None = None, db: Session = Depends(get_db)) -> list[AdminConnectionResponse]:
    tenant = _resolve_tenant(db, tenant_id)
    conns = db.scalars(
        select(IntegrationConnection)
        .where(IntegrationConnection.tenant_id == tenant.id)
        .order_by(IntegrationConnection.provider, IntegrationConnection.priority, IntegrationConnection.id)
    ).all()
    return [_connection_to_response(db, conn) for conn in conns]


@admin_router.post("/connectors", response_model=AdminConnectionResponse)
def create_connector(
    body: ConnectorCreateRequest,
    request: Request,
    tenant_id: int | None = None,
    db: Session = Depends(get_db),
) -> AdminConnectionResponse:
    tenant = _resolve_tenant(db, tenant_id)
    provider = _provider_or_400(body.provider)
    payload = body.model_dump(exclude_unset=True)
    name = _clean(body.name) or _next_connection_name(db, tenant.id, body.provider)
    _ensure_unique_connection_name(db, tenant.id, body.provider, name)

    mode = body.mode
    conn = IntegrationConnection(
        tenant_id=tenant.id,
        provider=body.provider,
        name=name,
        mode=mode.value,
        environment=_clean(body.environment) or ("mock" if mode == ConnectorMode.MOCK else provider.default_environment),
        base_url=_clean(body.base_url) or provider.default_base_url(mode=mode),
        status="mock" if mode == ConnectorMode.MOCK else "config_incomplete",
        priority=body.priority or (100 + _count_provider_connections(db, tenant.id, body.provider)),
        is_primary=False,
        is_active=True,
        config_payload=body.config_payload,
    )
    db.add(conn)
    db.flush()

    message = provider.apply_configuration(db, conn, payload | {"name": name}, secret_store=get_secret_store())
    should_be_primary = body.is_primary or not _has_primary_connection(db, tenant.id, body.provider)
    _set_primary_connection(db, conn, make_primary=should_be_primary)
    _provision_jobs_for_connection(db, conn, enabled=False)
    _record_audit(
        db,
        tenant_id=tenant.id,
        actor=_actor_name(request),
        action="connector.created",
        target_type="integration_connection",
        target_id=str(conn.id),
        target_label=conn.name,
        payload={"provider": conn.provider, "mode": conn.mode, "environment": conn.environment, "is_primary": conn.is_primary},
    )
    db.commit()
    db.refresh(conn)
    return _connection_to_response(db, conn, message=message)


@admin_router.patch("/connectors/{conn_id}", response_model=AdminConnectionResponse)
def update_connector(
    conn_id: int,
    body: ConnectorConfigUpdate,
    request: Request,
    tenant_id: int | None = None,
    db: Session = Depends(get_db),
) -> AdminConnectionResponse:
    tenant = _resolve_tenant(db, tenant_id)
    conn = _connection_for_tenant(db, tenant.id, conn_id)
    provider = _provider_or_400(conn.provider)
    payload = body.model_dump(exclude_unset=True)

    next_name = _clean(body.name) or conn.name
    _ensure_unique_connection_name(db, tenant.id, conn.provider, next_name, exclude_id=conn.id)
    message = provider.apply_configuration(db, conn, payload | {"name": next_name}, secret_store=get_secret_store())
    if body.is_primary is True:
        _set_primary_connection(db, conn, make_primary=True)
    elif body.is_primary is False and conn.is_primary:
        _set_primary_connection(db, conn, make_primary=False)

    _provision_jobs_for_connection(db, conn, enabled=False)
    _record_audit(
        db,
        tenant_id=tenant.id,
        actor=_actor_name(request),
        action="connector.updated",
        target_type="integration_connection",
        target_id=str(conn.id),
        target_label=conn.name,
        payload={"provider": conn.provider, "mode": conn.mode, "environment": conn.environment, "status": conn.status},
    )
    db.commit()
    db.refresh(conn)
    return _connection_to_response(db, conn, message=message)


@admin_router.post("/connectors/{conn_id}/check", response_model=AdminConnectionResponse)
def check_connector(
    conn_id: int,
    request: Request,
    tenant_id: int | None = None,
    db: Session = Depends(get_db),
) -> AdminConnectionResponse:
    tenant = _resolve_tenant(db, tenant_id)
    conn = _connection_for_tenant(db, tenant.id, conn_id)
    provider = _provider_or_400(conn.provider)
    result = provider.check_connection(db, conn, secret_store=get_secret_store())
    if not result.connected:
        _record_connection_error(db, conn, message=result.message)
    _record_audit(
        db,
        tenant_id=tenant.id,
        actor=_actor_name(request),
        action="connector.checked",
        target_type="integration_connection",
        target_id=str(conn.id),
        target_label=conn.name,
        payload={"provider": conn.provider, "connected": result.connected, "status": conn.status},
    )
    db.commit()
    db.refresh(conn)
    return _connection_to_response(db, conn, connected=result.connected, message=result.message)


@admin_router.post("/connectors/{conn_id}/primary", response_model=AdminConnectionResponse)
def make_connector_primary(
    conn_id: int,
    request: Request,
    tenant_id: int | None = None,
    db: Session = Depends(get_db),
) -> AdminConnectionResponse:
    tenant = _resolve_tenant(db, tenant_id)
    conn = _connection_for_tenant(db, tenant.id, conn_id)
    _set_primary_connection(db, conn, make_primary=True)
    _record_audit(
        db,
        tenant_id=tenant.id,
        actor=_actor_name(request),
        action="connector.primary_set",
        target_type="integration_connection",
        target_id=str(conn.id),
        target_label=conn.name,
        payload={"provider": conn.provider},
    )
    db.commit()
    db.refresh(conn)
    return _connection_to_response(db, conn, message="Conexion marcada como primaria.")


@admin_router.get("/connectors/{conn_id}/jobs", response_model=ConnectorJobsResponse)
def get_connector_jobs(conn_id: int, tenant_id: int | None = None, db: Session = Depends(get_db)) -> ConnectorJobsResponse:
    tenant = _resolve_tenant(db, tenant_id)
    conn = _connection_for_tenant(db, tenant.id, conn_id)
    _provision_jobs_for_connection(db, conn, enabled=False)
    jobs = _jobs_for_connection(db, conn)
    return ConnectorJobsResponse(
        connection_id=conn.id,
        jobs_total=len(jobs),
        jobs_enabled=sum(1 for job in jobs if job.is_enabled),
        jobs=[_job_response(db, job) for job in jobs],
    )


@admin_router.post("/connectors/{conn_id}/jobs/activate", response_model=ConnectorJobsResponse)
def set_connector_jobs_enabled(
    conn_id: int,
    body: JobActivationRequest,
    request: Request,
    tenant_id: int | None = None,
    db: Session = Depends(get_db),
) -> ConnectorJobsResponse:
    tenant = _resolve_tenant(db, tenant_id)
    conn = _connection_for_tenant(db, tenant.id, conn_id)
    _provision_jobs_for_connection(db, conn, enabled=body.enabled)
    jobs = _jobs_for_connection(db, conn)
    for job in jobs:
        job.is_enabled = body.enabled
    _record_audit(
        db,
        tenant_id=tenant.id,
        actor=_actor_name(request),
        action="connector.jobs_toggled",
        target_type="integration_connection",
        target_id=str(conn.id),
        target_label=conn.name,
        payload={"enabled": body.enabled, "job_count": len(jobs)},
    )
    db.commit()
    jobs = _jobs_for_connection(db, conn)
    return ConnectorJobsResponse(
        connection_id=conn.id,
        jobs_total=len(jobs),
        jobs_enabled=sum(1 for job in jobs if job.is_enabled),
        jobs=[_job_response(db, job) for job in jobs],
    )


@admin_router.post("/connectors/{conn_id}/sync", response_model=ConnectorBatchRunResponse)
def queue_connector_sync(
    conn_id: int,
    request: Request,
    tenant_id: int | None = None,
    db: Session = Depends(get_db),
) -> ConnectorBatchRunResponse:
    tenant = _resolve_tenant(db, tenant_id)
    conn = _connection_for_tenant(db, tenant.id, conn_id)
    jobs = _jobs_for_connection(db, conn)
    enabled_jobs = [job for job in jobs if job.is_enabled]
    if not enabled_jobs:
        raise HTTPException(status_code=400, detail="No hay jobs habilitados para esta conexion. Activalos antes de correr el sync inicial.")

    service = IngestionService(db)
    queued_runs: list[IntegrationJobRun] = []
    for job in enabled_jobs:
        run = service.trigger_job(job.id, tenant_id=tenant.id)
        execute_run.delay(run.id)
        queued_runs.append(run)

    _record_audit(
        db,
        tenant_id=tenant.id,
        actor=_actor_name(request),
        action="connector.sync_queued",
        target_type="integration_connection",
        target_id=str(conn.id),
        target_label=conn.name,
        payload={"queued_runs": [run.id for run in queued_runs]},
    )
    db.commit()
    return ConnectorBatchRunResponse(
        connection_id=conn.id,
        queued_runs=[_run_response(db, run) for run in queued_runs],
        message=f"Se encolaron {len(queued_runs)} jobs para {conn.name}.",
    )


@admin_router.get("/jobs", response_model=list[JobResponse])
def list_jobs(tenant_id: int | None = None, db: Session = Depends(get_db)) -> list[JobResponse]:
    tenant = _resolve_tenant(db, tenant_id)
    jobs = db.scalars(
        select(IntegrationJob)
        .where(IntegrationJob.tenant_id == tenant.id)
        .order_by(IntegrationJob.connection_id, IntegrationJob.id)
    ).all()
    return [_job_response(db, job) for job in jobs]


@admin_router.post("/jobs/{job_id}/runs", response_model=JobRunResponse)
def trigger_job(job_id: int, request: Request, tenant_id: int | None = None, db: Session = Depends(get_db)) -> JobRunResponse:
    tenant = _resolve_tenant(db, tenant_id)
    service = IngestionService(db)
    try:
        run = service.trigger_job(job_id, tenant_id=tenant.id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    execute_run.delay(run.id)
    _record_audit(
        db,
        tenant_id=tenant.id,
        actor=_actor_name(request),
        action="job.run_queued",
        target_type="integration_job",
        target_id=str(job_id),
        target_label=f"job #{job_id}",
        payload={"run_id": run.id},
    )
    db.commit()
    return _run_response(db, run)


@admin_router.get("/runs", response_model=list[JobRunResponse])
def list_runs(limit: int = 30, tenant_id: int | None = None, db: Session = Depends(get_db)) -> list[JobRunResponse]:
    tenant = _resolve_tenant(db, tenant_id)
    runs = db.scalars(
        select(IntegrationJobRun)
        .join(IntegrationJob, IntegrationJob.id == IntegrationJobRun.job_id)
        .where(IntegrationJob.tenant_id == tenant.id)
        .order_by(desc(IntegrationJobRun.id))
        .limit(limit)
    ).all()
    return [_run_response(db, run) for run in runs]


@admin_router.get("/errors", response_model=list[ErrorResponse])
def list_errors(limit: int = 30, tenant_id: int | None = None, db: Session = Depends(get_db)) -> list[ErrorResponse]:
    tenant = _resolve_tenant(db, tenant_id)
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


@admin_router.get("/audit", response_model=list[AuditLogResponse])
def list_audit(limit: int = 40, tenant_id: int | None = None, db: Session = Depends(get_db)) -> list[AuditLogResponse]:
    tenant = _resolve_tenant(db, tenant_id)
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


@admin_router.get("/mappings", response_model=list[MappingResponse])
def list_mappings(tenant_id: int | None = None, db: Session = Depends(get_db)) -> list[MappingResponse]:
    tenant = _resolve_tenant(db, tenant_id)
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


@admin_router.patch("/connectors/{conn_id}/mode", response_model=AdminConnectionResponse)
def set_connector_mode(
    conn_id: int,
    body: ConnectorModeUpdate,
    request: Request,
    tenant_id: int | None = None,
    db: Session = Depends(get_db),
) -> AdminConnectionResponse:
    update_payload = ConnectorConfigUpdate(
        mode=_parse_mode_or_400(body.mode),
        base_url=body.base_url,
        api_key=body.api_key,
        secret_ref=body.secret_ref,
    )
    response = update_connector(conn_id, update_payload, request, tenant_id=tenant_id, db=db)
    if not body.check_connection:
        return response
    return check_connector(conn_id, request, tenant_id=tenant_id, db=db)


@admin_router.get("/data/products")
def data_products(limit: int = 50, tenant_id: int | None = None, db: Session = Depends(get_db)):
    tenant = _resolve_tenant(db, tenant_id)
    stmt = select(Product).where(Product.tenant_id == tenant.id)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    items = db.scalars(stmt.order_by(Product.id.desc()).limit(limit)).all()
    return {
        "total": total,
        "items": [
            {
                "id": p.id,
                "external_id": p.external_id,
                "sku": p.sku,
                "name": p.name,
                "description": p.description,
                "classification": p.classification,
                "product_type_id": p.product_type_id,
                "state": p.state,
                "category": p.category,
                "unit": p.unit,
                "is_active": p.is_active,
                "variant_count": len(p.variants),
            }
            for p in items
        ],
    }


@admin_router.get("/data/branches")
def data_branches(tenant_id: int | None = None, db: Session = Depends(get_db)):
    tenant = _resolve_tenant(db, tenant_id)
    stmt = select(Branch).where(Branch.tenant_id == tenant.id)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    items = db.scalars(stmt.order_by(Branch.id)).all()
    return {
        "total": total,
        "items": [
            {
                "id": b.id,
                "external_id": b.external_id,
                "name": b.name,
                "description": b.description,
                "address": b.address,
                "country": b.country,
                "city": b.city,
                "municipality": b.municipality,
                "zip_code": b.zip_code,
                "cost_center": b.cost_center,
                "is_virtual": b.is_virtual,
                "state": b.state,
                "imagestion_cellar_id": b.imagestion_cellar_id,
                "code": b.code,
            }
            for b in items
        ],
    }


@admin_router.get("/data/document-types")
def data_document_types(limit: int = 50, tenant_id: int | None = None, db: Session = Depends(get_db)):
    tenant = _resolve_tenant(db, tenant_id)
    stmt = select(DocumentType).where(DocumentType.tenant_id == tenant.id)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    items = db.scalars(stmt.order_by(DocumentType.id.desc()).limit(limit)).all()
    return {
        "total": total,
        "items": [
            {
                "id": item.id,
                "external_id": item.external_id,
                "name": item.name,
                "initial_number": item.initial_number,
                "code_sii": item.code_sii,
                "use": item.use,
                "state": item.state,
                "is_electronic_document": item.is_electronic_document,
                "is_sales_note": item.is_sales_note,
                "is_exempt": item.is_exempt,
                "is_credit_note": item.is_credit_note,
                "use_client": item.use_client,
                "book_type_id": item.book_type_id,
            }
            for item in items
        ],
    }


@admin_router.get("/data/customers")
def data_customers(limit: int = 50, tenant_id: int | None = None, db: Session = Depends(get_db)):
    tenant = _resolve_tenant(db, tenant_id)
    stmt = select(Client).where(Client.tenant_id == tenant.id)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    items = db.scalars(stmt.order_by(Client.id.desc()).limit(limit)).all()
    return {
        "total": total,
        "items": [
            {
                "id": c.id,
                "external_id": c.external_id,
                "first_name": c.first_name,
                "last_name": c.last_name,
                "email": c.email,
                "code": c.code,
                "company": c.company,
                "phone": c.phone,
                "state": c.state,
                "activity": c.activity,
                "city": c.city,
                "municipality": c.municipality,
                "points": c.points,
                "office_external_id": c.office_external_id,
                "contact_count": len(c.contacts),
                "address_count": len(c.addresses),
                "attribute_count": len(c.attributes),
            }
            for c in items
        ],
    }


@admin_router.get("/data/stock")
def data_stock(limit: int = 50, tenant_id: int | None = None, db: Session = Depends(get_db)):
    tenant = _resolve_tenant(db, tenant_id)
    stmt = select(StockSnapshot).where(StockSnapshot.tenant_id == tenant.id)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    items = db.scalars(stmt.order_by(StockSnapshot.id.desc()).limit(limit)).all()
    return {
        "total": total,
        "items": [
            {
                "id": s.id,
                "product_external_id": s.product_external_id,
                "branch_external_id": s.branch_external_id,
                "quantity": float(s.quantity),
                "captured_at": s.captured_at.isoformat(),
            }
            for s in items
        ],
    }


@admin_router.get("/data/sales")
def data_sales(limit: int = 50, tenant_id: int | None = None, db: Session = Depends(get_db)):
    tenant = _resolve_tenant(db, tenant_id)
    stmt = select(SalesDocument).where(SalesDocument.tenant_id == tenant.id)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    items = db.scalars(stmt.order_by(SalesDocument.id.desc()).limit(limit)).all()
    return {
        "total": total,
        "items": [
            {
                "id": d.id,
                "external_id": d.external_id,
                "branch_external_id": d.branch_external_id,
                "issued_at": d.issued_at.isoformat(),
                "total_amount": float(d.total_amount),
                "customer_external_id": d.customer_external_id,
            }
            for d in items
        ],
    }


@connectors_router.get("/bsale", response_model=BsaleStatusResponse)
def get_bsale_status() -> BsaleStatusResponse:
    config = bsale_connector.config
    return BsaleStatusResponse(
        connector=config.name,
        mode=config.mode,
        base_url=config.base_url,
        api_key=_bsale_masked_api_key(),
        message="Conector configurado.",
    )


@connectors_router.patch("/bsale", response_model=BsaleStatusResponse)
def update_bsale(payload: BsaleUpdateRequest) -> BsaleStatusResponse:
    try:
        config = bsale_connector.update(mode=payload.mode, base_url=payload.base_url, api_key=payload.api_key)
    except ConnectorConfigurationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    connected = None
    message = "Configuracion guardada."
    if payload.check_connection:
        connected, message = bsale_connector.attempt_connection()

    return BsaleStatusResponse(
        connector=config.name,
        mode=config.mode,
        base_url=config.base_url,
        api_key=_bsale_masked_api_key(),
        connected=connected,
        message=message,
    )


router.include_router(admin_router)
router.include_router(connectors_router)
