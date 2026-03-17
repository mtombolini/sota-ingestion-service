"""Tenant CRUD endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import (
    AdminAuditLog,
    IntegrationConnection,
    IntegrationError,
    IntegrationJob,
    IntegrationJobRun,
    IntegrationMapping,
    IntegrationOutboxEvent,
    IntegrationRawObject,
    IntegrationSecret,
    Location,
    Product,
    SalesOrder,
    SalesOrderLine,
    Stock,
    Tenant,
)
from app.schemas.admin import (
    TenantCreateRequest,
    TenantResponse,
    TenantUpdateRequest,
)

router = APIRouter()


@router.get("/tenants", response_model=list[TenantResponse])
def list_tenants(db: Session = Depends(get_db)) -> list[TenantResponse]:
    tenants = db.scalars(select(Tenant).order_by(Tenant.name, Tenant.id)).all()
    return [TenantResponse(id=tenant.id, slug=tenant.slug, name=tenant.name, is_active=tenant.is_active) for tenant in tenants]


@router.post("/tenants", response_model=TenantResponse, status_code=201)
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


@router.patch("/tenants/{tenant_id}", response_model=TenantResponse)
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


@router.delete("/tenants/{tenant_id}")
def delete_tenant(tenant_id: int, force: bool = False, request: Request = None, db: Session = Depends(get_db)):
    tenant = db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
    conn_count = db.scalar(select(func.count(IntegrationConnection.id)).where(IntegrationConnection.tenant_id == tenant_id)) or 0
    if conn_count > 0 and not force:
        raise HTTPException(status_code=409, detail=f"No se puede eliminar: el tenant tiene {conn_count} conexion(es) asociada(s). Elimina las conexiones primero o usa force=true.")
    tenant_name = tenant.name
    tenant_slug = tenant.slug
    sales_order_ids = db.scalars(select(SalesOrder.id).where(SalesOrder.tenant_id == tenant_id)).all()
    if sales_order_ids:
        db.execute(SalesOrderLine.__table__.delete().where(SalesOrderLine.sales_order_id.in_(sales_order_ids)))
    for model in (SalesOrder, Stock, Product, Location, IntegrationError, IntegrationOutboxEvent, IntegrationMapping, IntegrationSecret, AdminAuditLog):
        db.execute(model.__table__.delete().where(model.tenant_id == tenant_id))
    job_ids = db.scalars(select(IntegrationJob.id).where(IntegrationJob.tenant_id == tenant_id)).all()
    if job_ids:
        run_ids = db.scalars(select(IntegrationJobRun.id).where(IntegrationJobRun.job_id.in_(job_ids))).all()
        if run_ids:
            db.execute(IntegrationRawObject.__table__.delete().where(IntegrationRawObject.job_run_id.in_(run_ids)))
        db.execute(IntegrationJobRun.__table__.delete().where(IntegrationJobRun.job_id.in_(job_ids)))
    db.execute(IntegrationJob.__table__.delete().where(IntegrationJob.tenant_id == tenant_id))
    db.execute(IntegrationConnection.__table__.delete().where(IntegrationConnection.tenant_id == tenant_id))
    db.delete(tenant)
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
