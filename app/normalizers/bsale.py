from datetime import datetime


SOURCE_SYSTEM = "bsale"


def _boolish(value) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    try:
        return bool(int(value))
    except (TypeError, ValueError):
        return bool(value)


def _intish(value) -> int | None:
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _floatish(value) -> float | None:
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _extract_ref_id(node) -> str | None:
    """Extract id from a Bsale reference node like {"href": "...", "id": "7"}."""
    if not node:
        return None
    if isinstance(node, dict):
        raw = node.get("id")
        return str(raw) if raw is not None else None
    return str(node)


def _extract_location_ref_id(payload: dict) -> str | None:
    office = payload.get("office") or payload.get("branch") or payload.get("location")
    resolved = _extract_ref_id(office)
    if resolved:
        return resolved
    for key in ("officeid", "officeId", "office_id", "branchid", "branchId", "locationid", "locationId"):
        raw = payload.get(key)
        if raw is not None and raw != "":
            return str(raw)
    return None


def _parse_bsale_timestamp(value, default=None) -> datetime | None:
    """Parse Bsale timestamp: either epoch integer or ISO string."""
    if value is None:
        return default if default is not None else datetime.utcnow()
    if isinstance(value, (int, float)):
        return datetime.utcfromtimestamp(value)
    if isinstance(value, str):
        if not value.strip():
            return default if default is not None else datetime.utcnow()
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            try:
                return datetime.utcfromtimestamp(int(value))
            except (TypeError, ValueError):
                return default if default is not None else datetime.utcnow()
    return default if default is not None else datetime.utcnow()


# ---------------------------------------------------------------------------
# Canonical normalizers — these produce dicts that map to canonical models
# ---------------------------------------------------------------------------


def normalize_variant(payload: dict, *, product_external_id: str | None = None) -> dict:
    """Bsale variant/SKU -> canonical Variant."""
    parent_product = payload.get("product") or {}
    resolved_product_external_id = product_external_id or _extract_ref_id(parent_product)
    return {
        "source_system": SOURCE_SYSTEM,
        "external_id": str(payload["id"]),
        "product_external_id": resolved_product_external_id,
        "sku": payload.get("code"),
        "name": payload.get("description") or payload.get("code") or f"Variant {payload['id']}",
        "barcode": payload.get("barCode"),
        "is_active": int(payload.get("state", 0) or 0) == 0,
        "allows_negative_stock": _boolish(payload.get("allowNegativeStock")),
        "unlimited_stock": _boolish(payload.get("unlimitedStock")),
    }


def normalize_product(payload: dict) -> dict:
    """Bsale product → canonical Product.

    Variants are normalized separately and returned nested to keep the
    provider contract centered on one root object per product payload.
    """
    variants_payload = payload.get("variants", [])
    if isinstance(variants_payload, dict):
        variants_payload = variants_payload.get("items", [])

    primary_variant = None
    for v in variants_payload:
        if v.get("code"):
            primary_variant = v
            break

    return {
        "source_system": SOURCE_SYSTEM,
        "external_id": str(payload["id"]),
        "sku": primary_variant.get("code") if primary_variant else None,
        "name": payload.get("name", "unknown"),
        "category_id": None,
        "brand": None,
        "unit_of_measure": None,
        "unit_cost": None,
        "unit_price": None,
        "weight_kg": None,
        "volume_m3": None,
        "is_active": int(payload.get("state", 0) or 0) == 0,
        "min_order_qty": None,
        "shelf_life_days": None,
        "variants": [normalize_variant(v, product_external_id=str(payload["id"])) for v in variants_payload],
    }


def normalize_location(payload: dict) -> dict:
    """Bsale office/branch → canonical Location."""
    return {
        "source_system": SOURCE_SYSTEM,
        "external_id": str(payload["id"]),
        "name": payload.get("name", "unknown"),
        "type": "STORE",
        "address": payload.get("address"),
        "city": payload.get("city"),
        "region": payload.get("country"),
        "is_active": int(payload.get("state", 0) or 0) == 0,
        "parent_location_id": None,
    }


def normalize_stock(payload: dict) -> dict:
    """Bsale stock → canonical Stock snapshot.

    Bsale only provides quantity on hand; reserved/available/in_transit
    are not available and default to 0.
    """
    variant_node = payload.get("variant")
    variant_ext_id = _extract_ref_id(variant_node)
    if not variant_ext_id:
        raw_variant_id = payload.get("variantid") or payload.get("variantId") or payload.get("productid")
        variant_ext_id = str(raw_variant_id)
    location_ext_id = _extract_location_ref_id(payload)
    if not location_ext_id:
        raise ValueError("stock payload missing office reference")
    qty = _floatish(payload.get("quantity")) or 0

    return {
        "source_system": SOURCE_SYSTEM,
        "external_id": f"{variant_ext_id}:{location_ext_id}",
        "variant_external_id": variant_ext_id,
        "location_external_id": location_ext_id,
        "quantity_on_hand": qty,
        "quantity_reserved": 0,
        "quantity_available": qty,
        "quantity_in_transit": 0,
    }


def _normalize_sales_line(detail: dict) -> dict:
    """Normalize a single Bsale document detail → canonical SalesOrderLine."""
    variant = detail.get("variant") or {}
    variant_id = _extract_ref_id(variant)
    if not variant_id:
        variant_id = str(detail.get("variantId") or detail.get("productId") or "0")

    unit_price = _floatish(detail.get("netUnitValue")) or 0
    quantity = _floatish(detail.get("quantity")) or 0
    total = _floatish(detail.get("totalAmount")) or 0

    # Convert discount amount to percentage
    discount_amount = _floatish(detail.get("netDiscount")) or 0
    gross = unit_price * quantity if quantity else 0
    discount_pct = (discount_amount / gross * 100) if gross else 0

    return {
        "variant_external_id": variant_id,
        "quantity": quantity,
        "unit_price": unit_price,
        "discount_pct": round(discount_pct, 2),
    }


def normalize_sales_order(payload: dict) -> dict:
    """Bsale document → canonical SalesOrder + SalesOrderLines."""
    emission = payload.get("emissionDate") or payload.get("emissiondate")
    dt = _parse_bsale_timestamp(emission)

    location_ext_id = _extract_location_ref_id(payload)

    client = payload.get("client") or {}
    customer_ref = _extract_ref_id(client)

    # Bsale state: 0 = active, 1 = cancelled
    bsale_state = int(payload.get("state", 0) or 0)
    status = "CANCELLED" if bsale_state == 1 else "CONFIRMED"

    raw_details = payload.get("details", [])
    if isinstance(raw_details, dict):
        raw_details = raw_details.get("items", [])

    return {
        "source_system": SOURCE_SYSTEM,
        "external_id": str(payload["id"]),
        "location_external_id": location_ext_id,
        "order_date": dt,
        "customer_ref": customer_ref,
        "total_amount": _floatish(payload.get("totalAmount") or payload.get("totalamount")) or 0,
        "currency": "CLP",
        "channel": "STORE",
        "status": status,
        "lines": [_normalize_sales_line(d) for d in raw_details],
    }


def _normalize_stock_movement_line(
    detail: dict,
    *,
    reception_or_consumption_id: str,
    location_external_id: str | None,
    movement_date: datetime,
    movement_type: str,
    reference_type: str,
) -> dict:
    variant = detail.get("variant") or {}
    variant_external_id = _extract_ref_id(variant)
    if not variant_external_id:
        variant_external_id = str(detail.get("variantId") or detail.get("productId") or "0")
    quantity = _floatish(detail.get("quantity")) or 0
    if movement_type.endswith("_OUT"):
        quantity *= -1

    return {
        "source_system": SOURCE_SYSTEM,
        "external_id": f"{reference_type.lower()}:{reception_or_consumption_id}:{detail.get('id') or detail.get('lineNumber') or variant_external_id}",
        "variant_external_id": variant_external_id,
        "location_external_id": location_external_id,
        "movement_type": movement_type,
        "quantity": quantity,
        "reference_type": reference_type,
        "reference_id": reception_or_consumption_id,
        "movement_date": movement_date,
        "unit_cost": _floatish(detail.get("netUnitValue") or detail.get("cost")) or None,
    }


def normalize_stock_reception(payload: dict) -> dict:
    reception_id = str(payload["id"])
    movement_date = _parse_bsale_timestamp(
        payload.get("receptionDate") or payload.get("generationDate") or payload.get("emissionDate")
    )
    location_external_id = _extract_location_ref_id(payload)
    details = payload.get("details", [])
    if isinstance(details, dict):
        details = details.get("items", [])
    return {
        "movements": [
            _normalize_stock_movement_line(
                detail,
                reception_or_consumption_id=reception_id,
                location_external_id=location_external_id,
                movement_date=movement_date,
                movement_type="RECEPTION_IN",
                reference_type="STOCK_RECEPTION",
            )
            for detail in details
        ]
    }


def normalize_stock_consumption(payload: dict) -> dict:
    consumption_id = str(payload["id"])
    movement_date = _parse_bsale_timestamp(
        payload.get("consumptionDate") or payload.get("generationDate") or payload.get("emissionDate")
    )
    location_external_id = _extract_location_ref_id(payload)
    details = payload.get("details", [])
    if isinstance(details, dict):
        details = details.get("items", [])
    return {
        "movements": [
            _normalize_stock_movement_line(
                detail,
                reception_or_consumption_id=consumption_id,
                location_external_id=location_external_id,
                movement_date=movement_date,
                movement_type="CONSUMPTION_OUT",
                reference_type="STOCK_CONSUMPTION",
            )
            for detail in details
        ]
    }
