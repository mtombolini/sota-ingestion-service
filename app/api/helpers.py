"""Shared helpers used across API route modules."""

from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session

from app.connectors.base import ConnectorMode
from app.core.utils import clean_string
from app.models import (
    AdminAuditLog,
    IntegrationConnection,
    IntegrationError,
    IntegrationJob,
    IntegrationJobRun,
    IntegrationMapping,
    IntegrationRawObject,
    Tenant,
)
from app.providers import provider_registry
from app.schemas.admin import (
    AdminConnectionResponse,
    JobResponse,
    JobRunResponse,
)


JOB_LABELS = {
    "sync_product_catalog": "Catalogo",
    "sync_locations": "Ubicaciones",
    "sync_stock": "Stock",
    "sync_sales_orders": "Ventas",
    "sync_customers": "Clientes (raw)",
    "sync_document_types": "Tipos de documento (raw)",
}


class ConnectionHealthStats(BaseModel):
    jobs_total: int
    jobs_enabled: int
    successful_runs: int
    failed_runs: int
    recent_error_count: int
    last_sync_at: datetime | None
    last_run_status: str | None


def parse_mode_or_400(value: str) -> ConnectorMode:
    try:
        return ConnectorMode(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="mode must be 'mock' or 'real'") from exc


def resolve_tenant(db: Session, tenant_id: int | None) -> Tenant:
    if tenant_id is not None:
        tenant = db.get(Tenant, tenant_id)
        if tenant is None:
            raise HTTPException(status_code=404, detail=f"tenant {tenant_id} not found")
        return tenant

    tenant = db.scalar(select(Tenant).where(Tenant.is_active.is_(True)).order_by(Tenant.id))
    if tenant is None:
        raise HTTPException(status_code=404, detail="no tenants configured")
    return tenant


def connection_for_tenant(db: Session, tenant_id: int, conn_id: int) -> IntegrationConnection:
    conn = db.get(IntegrationConnection, conn_id)
    if conn is None or conn.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="connector not found")
    return conn


def provider_or_400(provider_key: str):
    try:
        return provider_registry.get(provider_key)
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def actor_name(request: Request) -> str:
    return request.headers.get("x-actor", "ui")


def record_audit(
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


def count_provider_connections(db: Session, tenant_id: int, provider_key: str) -> int:
    return int(
        db.scalar(
            select(func.count())
            .select_from(IntegrationConnection)
            .where(IntegrationConnection.tenant_id == tenant_id, IntegrationConnection.provider == provider_key)
        )
        or 0
    )


def next_connection_name(db: Session, tenant_id: int, provider_key: str) -> str:
    provider = provider_or_400(provider_key)
    ordinal = count_provider_connections(db, tenant_id, provider_key) + 1
    return provider.default_connection_name(ordinal=ordinal)


def ensure_unique_connection_name(db: Session, tenant_id: int, provider_key: str, name: str, *, exclude_id: int | None = None) -> None:
    stmt = select(IntegrationConnection).where(
        IntegrationConnection.tenant_id == tenant_id,
        IntegrationConnection.provider == provider_key,
        IntegrationConnection.name == name,
    )
    if exclude_id is not None:
        stmt = stmt.where(IntegrationConnection.id != exclude_id)
    if db.scalar(stmt) is not None:
        raise HTTPException(status_code=400, detail=f"connection name '{name}' already exists for provider '{provider_key}'")


def set_primary_connection(db: Session, conn: IntegrationConnection, *, make_primary: bool) -> None:
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


def has_primary_connection(db: Session, tenant_id: int, provider_key: str) -> bool:
    return bool(
        db.scalar(
            select(IntegrationConnection.id).where(
                IntegrationConnection.tenant_id == tenant_id,
                IntegrationConnection.provider == provider_key,
                IntegrationConnection.is_primary.is_(True),
            )
        )
    )


def provision_jobs_for_connection(db: Session, conn: IntegrationConnection, *, enabled: bool) -> list[IntegrationJob]:
    provider = provider_or_400(conn.provider)
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


def legacy_job_aliases_for_provider(provider_key: str) -> dict[str, str]:
    if provider_key == "bsale":
        return {
            "sync_branches": "sync_locations",
            "sync_stock_snapshot": "sync_stock",
            "sync_sales_documents": "sync_sales_orders",
            "sync_stock_receptions": "sync_stock",
            "sync_stock_consumptions": "sync_stock",
        }
    return {}


def delete_job_with_artifacts(db: Session, job: IntegrationJob) -> int:
    run_ids = db.scalars(select(IntegrationJobRun.id).where(IntegrationJobRun.job_id == job.id)).all()
    if run_ids:
        db.execute(IntegrationRawObject.__table__.delete().where(IntegrationRawObject.job_run_id.in_(run_ids)))
        db.execute(IntegrationError.__table__.delete().where(IntegrationError.job_run_id.in_(run_ids)))
        db.execute(IntegrationJobRun.__table__.delete().where(IntegrationJobRun.id.in_(run_ids)))
    db.execute(IntegrationJob.__table__.delete().where(IntegrationJob.id == job.id))
    return 1


def prune_jobs_for_connection(db: Session, conn: IntegrationConnection) -> int:
    provider = provider_or_400(conn.provider)
    supported_job_types = {job.job_type for job in provider.jobs}
    alias_map = legacy_job_aliases_for_provider(conn.provider)
    jobs = db.scalars(select(IntegrationJob).where(IntegrationJob.connection_id == conn.id).order_by(IntegrationJob.id)).all()

    canonical_jobs = {
        job.job_type: job
        for job in jobs
        if job.job_type in supported_job_types
    }

    changes = 0
    for job in jobs:
        target_job_type = alias_map.get(job.job_type, job.job_type if job.job_type in supported_job_types else None)
        if target_job_type is None:
            changes += delete_job_with_artifacts(db, job)
            continue

        canonical = canonical_jobs.get(target_job_type)
        if canonical is None:
            continue
        if canonical.id == job.id:
            continue

        canonical.is_enabled = canonical.is_enabled or job.is_enabled
        db.execute(IntegrationJobRun.__table__.update().where(IntegrationJobRun.job_id == job.id).values(job_id=canonical.id))
        db.execute(IntegrationJob.__table__.delete().where(IntegrationJob.id == job.id))
        changes += 1

    return changes


def reconcile_jobs_for_connections(db: Session, connections: list[IntegrationConnection], *, enabled: bool = False) -> int:
    changes = 0
    for conn in connections:
        changes += len(provision_jobs_for_connection(db, conn, enabled=enabled))
        changes += prune_jobs_for_connection(db, conn)
    return changes


def jobs_for_connection(db: Session, conn: IntegrationConnection) -> list[IntegrationJob]:
    provider = provider_or_400(conn.provider)
    supported_job_types = {job.job_type for job in provider.jobs}
    jobs = db.scalars(select(IntegrationJob).where(IntegrationJob.connection_id == conn.id).order_by(IntegrationJob.id.desc())).all()

    canonical_by_type: dict[str, IntegrationJob] = {}
    for job in jobs:
        if job.job_type not in supported_job_types:
            continue
        canonical_by_type.setdefault(job.job_type, job)

    provider_order = {job.job_type: idx for idx, job in enumerate(provider.jobs)}
    return sorted(
        canonical_by_type.values(),
        key=lambda job: (provider_order.get(job.job_type, 999), job.id),
    )


def connection_health_stats(db: Session, conn: IntegrationConnection) -> ConnectionHealthStats:
    jobs = jobs_for_connection(db, conn)
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


def build_onboarding(conn: IntegrationConnection, stats: ConnectionHealthStats):
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


def connection_to_response(
    db: Session,
    conn: IntegrationConnection,
    *,
    connected: bool | None = None,
    message: str | None = None,
) -> AdminConnectionResponse:
    provider = provider_or_400(conn.provider)
    stats = connection_health_stats(db, conn)
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
        onboarding=build_onboarding(conn, stats),
        connected=connected,
        message=message,
    )


def job_response(db: Session, job: IntegrationJob) -> JobResponse:
    conn = db.get(IntegrationConnection, job.connection_id)
    provider = provider_or_400(conn.provider)
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


def run_response(db: Session, run: IntegrationJobRun) -> JobRunResponse:
    job = db.get(IntegrationJob, run.job_id)
    conn = db.get(IntegrationConnection, job.connection_id)
    provider = provider_or_400(conn.provider)
    return JobRunResponse(
        id=run.id,
        job_id=run.job_id,
        connection_id=conn.id,
        connection_name=conn.name,
        provider=conn.provider,
        provider_label=provider.display_name,
        job_type=job.job_type,
        job_label=JOB_LABELS.get(job.job_type, job.job_type),
        status=run.status,
        correlation_id=run.correlation_id,
        started_at=run.started_at,
        finished_at=run.finished_at,
        records_raw=run.records_raw,
        records_normalized=run.records_normalized,
    )


def record_connection_error(db: Session, conn: IntegrationConnection, *, message: str) -> None:
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
