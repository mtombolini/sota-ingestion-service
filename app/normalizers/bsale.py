from datetime import datetime


def normalize_product(payload: dict) -> dict:
    return {
        "external_id": str(payload["id"]),
        "sku": payload.get("code"),
        "name": payload.get("name", "unknown"),
        "category": payload.get("category", {}).get("name") if payload.get("category") else None,
        "unit": payload.get("unit", {}).get("name") if payload.get("unit") else None,
        "is_active": bool(payload.get("state", 0) == 0),
    }


def normalize_branch(payload: dict) -> dict:
    return {
        "external_id": str(payload["id"]),
        "name": payload.get("name", "unknown"),
        "code": payload.get("code"),
    }


def normalize_stock(payload: dict) -> dict:
    return {
        "product_external_id": str(payload["productid"]),
        "branch_external_id": str(payload["officeid"]),
        "quantity": payload.get("quantity", 0),
    }


def _parse_bsale_timestamp(value) -> datetime:
    """Parse Bsale timestamp: either epoch integer or ISO string."""
    if value is None:
        return datetime.utcnow()
    if isinstance(value, (int, float)):
        return datetime.utcfromtimestamp(value)
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return datetime.utcfromtimestamp(int(value))
    return datetime.utcnow()


def _extract_ref_id(node) -> str | None:
    """Extract id from a Bsale reference node like {"href": "...", "id": "7"}."""
    if not node:
        return None
    if isinstance(node, dict):
        raw = node.get("id")
        return str(raw) if raw is not None else None
    return str(node)


def _normalize_detail(detail: dict) -> dict:
    """Normalize a single document detail line from Bsale format."""
    variant = detail.get("variant") or {}
    variant_id = _extract_ref_id(variant)
    variant_code = variant.get("code") if isinstance(variant, dict) else None
    # Fallback: some mock/old formats use flat variantId/productId
    if not variant_id:
        variant_id = str(detail.get("variantId") or detail.get("productId") or "0")
    return {
        "line_number": detail.get("lineNumber"),
        "variant_external_id": variant_id,
        "variant_code": variant_code,
        "product_external_id": variant_id,  # best proxy until variants are synced separately
        "quantity": detail.get("quantity", 0),
        "unit_price": detail.get("netUnitValue", 0),
        "net_amount": detail.get("netAmount"),
        "tax_amount": detail.get("taxAmount"),
        "total_amount": detail.get("totalAmount"),
        "discount": detail.get("netDiscount", 0),
    }


def normalize_sales_document(payload: dict) -> dict:
    emission = payload.get("emissionDate") or payload.get("emissiondate")
    dt = _parse_bsale_timestamp(emission)

    # Extract office id from reference node or flat field
    office = payload.get("office") or {}
    branch_id = _extract_ref_id(office) or (str(payload["officeid"]) if payload.get("officeid") else None)

    # Extract client id
    client = payload.get("client") or {}
    customer_id = _extract_ref_id(client)

    # Extract document type id
    doc_type = payload.get("document_type") or {}
    document_type_id = _extract_ref_id(doc_type)

    # Details: can be inline list (expanded) or nested {"items": [...]}
    raw_details = payload.get("details", [])
    if isinstance(raw_details, dict):
        raw_details = raw_details.get("items", [])

    return {
        "external_id": str(payload["id"]),
        "document_type_id": document_type_id,
        "number": payload.get("number"),
        "branch_external_id": branch_id,
        "issued_at": dt,
        "customer_external_id": customer_id,
        "net_amount": payload.get("netAmount"),
        "tax_amount": payload.get("taxAmount"),
        "exempt_amount": payload.get("exemptAmount"),
        "total_amount": payload.get("totalAmount") or payload.get("totalamount", 0),
        "state": payload.get("state", 0),
        "lines": [_normalize_detail(d) for d in raw_details],
    }
