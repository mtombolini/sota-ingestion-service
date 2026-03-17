"""Data exploration endpoints (products, locations, stock, sales)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Location, Product, SalesOrder, Stock, Variant

from app.api.helpers import resolve_tenant

router = APIRouter()


@router.get("/data/products")
def data_products(limit: int = 50, tenant_id: int | None = None, db: Session = Depends(get_db)):
    tenant = resolve_tenant(db, tenant_id)
    stmt = select(Product).where(Product.tenant_id == tenant.id)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    items = db.scalars(stmt.order_by(Product.id.desc()).limit(limit)).all()
    variant_counts = {
        product_id: count
        for product_id, count in db.execute(
            select(Variant.product_id, func.count(Variant.id))
            .where(Variant.tenant_id == tenant.id)
            .group_by(Variant.product_id)
        ).all()
    }
    return {
        "total": total,
        "items": [
            {
                "id": p.id,
                "source_system": p.source_system,
                "external_id": p.external_id,
                "sku": p.sku,
                "name": p.name,
                "brand": p.brand,
                "unit_of_measure": p.unit_of_measure,
                "unit_cost": float(p.unit_cost) if p.unit_cost is not None else None,
                "unit_price": float(p.unit_price) if p.unit_price is not None else None,
                "is_active": p.is_active,
                "category_id": p.category_id,
                "variant_count": variant_counts.get(p.id, 0),
            }
            for p in items
        ],
    }


@router.get("/data/locations")
def data_locations(tenant_id: int | None = None, db: Session = Depends(get_db)):
    tenant = resolve_tenant(db, tenant_id)
    stmt = select(Location).where(Location.tenant_id == tenant.id)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    items = db.scalars(stmt.order_by(Location.id)).all()
    return {
        "total": total,
        "items": [
            {
                "id": loc.id,
                "source_system": loc.source_system,
                "external_id": loc.external_id,
                "name": loc.name,
                "type": loc.type,
                "address": loc.address,
                "city": loc.city,
                "region": loc.region,
                "is_active": loc.is_active,
            }
            for loc in items
        ],
    }


@router.get("/data/stock")
def data_stock(limit: int = 50, tenant_id: int | None = None, db: Session = Depends(get_db)):
    tenant = resolve_tenant(db, tenant_id)
    stmt = select(Stock).where(Stock.tenant_id == tenant.id)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    items = db.scalars(stmt.order_by(Stock.id.desc()).limit(limit)).all()
    variant_ids = {item.variant_external_id for item in items}
    location_ids = {item.location_external_id for item in items}
    variants = db.scalars(
        select(Variant).where(Variant.tenant_id == tenant.id, Variant.external_id.in_(variant_ids))
    ).all() if variant_ids else []
    variant_names = {variant.external_id: variant.name for variant in variants}
    variants_by_external_id = {variant.external_id: variant for variant in variants}
    product_ids = {variant.product_id for variant in variants if variant.product_id is not None}
    products_by_id = {
        product.id: product
        for product in db.scalars(select(Product).where(Product.tenant_id == tenant.id, Product.id.in_(product_ids))).all()
    } if product_ids else {}
    location_names = {
        loc.external_id: loc.name
        for loc in db.scalars(
            select(Location).where(Location.tenant_id == tenant.id, Location.external_id.in_(location_ids))
        ).all()
    } if location_ids else {}
    return {
        "total": total,
        "items": [
            {
                "id": s.id,
                "source_system": s.source_system,
                "variant_external_id": s.variant_external_id,
                "variant_name": variant_names.get(s.variant_external_id),
                "product_name": (
                    products_by_id.get(variants_by_external_id[s.variant_external_id].product_id).name
                    if s.variant_external_id in variants_by_external_id
                    and variants_by_external_id[s.variant_external_id].product_id in products_by_id
                    else None
                ),
                "location_external_id": s.location_external_id,
                "location_name": location_names.get(s.location_external_id),
                "quantity_on_hand": float(s.quantity_on_hand),
                "quantity_available": float(s.quantity_available),
                "quantity_reserved": float(s.quantity_reserved),
                "quantity_in_transit": float(s.quantity_in_transit),
                "last_updated": s.last_updated.isoformat(),
            }
            for s in items
        ],
    }


@router.get("/data/sales")
def data_sales(limit: int = 50, tenant_id: int | None = None, db: Session = Depends(get_db)):
    tenant = resolve_tenant(db, tenant_id)
    stmt = select(SalesOrder).where(SalesOrder.tenant_id == tenant.id)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    items = db.scalars(stmt.order_by(SalesOrder.id.desc()).limit(limit)).all()
    location_ids = {item.location_external_id for item in items if item.location_external_id}
    location_names = {
        loc.external_id: loc.name
        for loc in db.scalars(
            select(Location).where(Location.tenant_id == tenant.id, Location.external_id.in_(location_ids))
        ).all()
    } if location_ids else {}
    return {
        "total": total,
        "items": [
            {
                "id": d.id,
                "source_system": d.source_system,
                "external_id": d.external_id,
                "location_external_id": d.location_external_id,
                "location_name": location_names.get(d.location_external_id),
                "order_date": d.order_date.isoformat(),
                "total_amount": float(d.total_amount),
                "currency": d.currency,
                "channel": d.channel,
                "status": d.status,
                "customer_ref": d.customer_ref,
                "line_count": len(d.lines),
            }
            for d in items
        ],
    }
