from datetime import datetime


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


def _normalize_product_variant(payload: dict) -> dict:
    return {
        "external_id": str(payload["id"]),
        "description": payload.get("description"),
        "code": payload.get("code"),
        "bar_code": payload.get("barCode"),
        "unlimited_stock": _boolish(payload.get("unlimitedStock")),
        "allow_negative_stock": _boolish(payload.get("allowNegativeStock")),
        "state": int(payload.get("state", 0) or 0),
        "serial_number": payload.get("serialNumber"),
        "prestashop_combination_id": payload.get("prestashopCombinationId"),
        "prestashop_value_id": payload.get("prestashopValueId"),
    }


def _normalize_product_tax(payload: dict) -> dict:
    return {
        "external_id": str(payload["id"]),
        "tax_external_id": _extract_ref_id(payload.get("tax")) or "0",
    }


def normalize_product(payload: dict) -> dict:
    variants_payload = payload.get("variants", [])
    if isinstance(variants_payload, dict):
        variants_payload = variants_payload.get("items", [])

    product_taxes_payload = payload.get("product_taxes_items") or payload.get("product_taxes", [])
    if isinstance(product_taxes_payload, dict):
        product_taxes_payload = product_taxes_payload.get("items", [])

    variants = [_normalize_product_variant(variant) for variant in variants_payload]
    primary_variant = next((variant for variant in variants if variant.get("code")), None)

    return {
        "external_id": str(payload["id"]),
        "sku": primary_variant.get("code") if primary_variant else None,
        "name": payload.get("name", "unknown"),
        "description": payload.get("description"),
        "classification": int(payload.get("classification", 0) or 0),
        "ledger_account": payload.get("ledgerAccount"),
        "cost_center": payload.get("costCenter"),
        "allow_decimal": _boolish(payload.get("allowDecimal")),
        "stock_control": _boolish(payload.get("stockControl")),
        "print_detail_pack": _boolish(payload.get("printDetailPack")),
        "product_type_id": _extract_ref_id(payload.get("product_type")),
        "state": int(payload.get("state", 0) or 0),
        "prestashop_product_id": payload.get("prestashopProductId"),
        "prestashop_attribute_id": payload.get("presashopAttributeId"),
        "category": None,
        "unit": None,
        "is_active": bool(payload.get("state", 0) == 0),
        "variants": variants,
        "product_taxes": [_normalize_product_tax(product_tax) for product_tax in product_taxes_payload],
    }


def _normalize_client_contact(payload: dict) -> dict:
    return {
        "external_id": str(payload["id"]),
        "first_name": payload.get("firstName"),
        "last_name": payload.get("lastName"),
        "phone": payload.get("phone"),
        "email": payload.get("email"),
    }


def _normalize_client_address(payload: dict) -> dict:
    return {
        "external_id": str(payload["id"]),
        "address_name": payload.get("addressName"),
        "address": payload.get("address"),
        "city": payload.get("city"),
        "municipality": payload.get("municipality"),
        "state": int(payload.get("state", 0) or 0),
    }


def _normalize_client_attribute(payload: dict) -> dict:
    return {
        "external_id": str(payload["id"]),
        "name": payload.get("name"),
        "value": None if payload.get("value") is None else str(payload.get("value")),
    }


def normalize_client(payload: dict) -> dict:
    contacts_payload = payload.get("contacts_items", [])
    if isinstance(contacts_payload, dict):
        contacts_payload = contacts_payload.get("items", [])

    addresses_payload = payload.get("addresses_items", [])
    if isinstance(addresses_payload, dict):
        addresses_payload = addresses_payload.get("items", [])

    attributes_payload = payload.get("attributes_items", [])
    if isinstance(attributes_payload, dict):
        attributes_payload = attributes_payload.get("items", [])

    office_external_id = _extract_ref_id(payload.get("office"))
    points_updated_at = _parse_bsale_timestamp(payload.get("pointsUpdated"), default=None)

    return {
        "external_id": str(payload["id"]),
        "first_name": payload.get("firstName"),
        "last_name": payload.get("lastName"),
        "email": payload.get("email"),
        "code": payload.get("code"),
        "phone": payload.get("phone"),
        "company": payload.get("company"),
        "note": payload.get("note"),
        "facebook": payload.get("facebook"),
        "twitter": payload.get("twitter"),
        "has_credit": _boolish(payload.get("hasCredit")),
        "max_credit": _floatish(payload.get("maxCredit")),
        "state": int(payload.get("state", 0) or 0),
        "activity": payload.get("activity"),
        "city": payload.get("city"),
        "municipality": payload.get("municipality"),
        "address": payload.get("address"),
        "company_or_person": _intish(payload.get("companyOrPerson")),
        "points": _intish(payload.get("points")),
        "points_updated_at": points_updated_at,
        "accumulate_points": _boolish(payload.get("accumulatePoints")),
        "send_dte": _boolish(payload.get("sendDte")),
        "prestashop_client_id": None if payload.get("prestashopClienId") is None else str(payload.get("prestashopClienId")),
        "office_external_id": office_external_id,
        "is_active": int(payload.get("state", 0) or 0) == 0,
        "contacts": [_normalize_client_contact(contact) for contact in contacts_payload],
        "addresses": [_normalize_client_address(address) for address in addresses_payload],
        "attributes": [_normalize_client_attribute(attribute) for attribute in attributes_payload],
    }


def normalize_branch(payload: dict) -> dict:
    return {
        "external_id": str(payload["id"]),
        "name": payload.get("name", "unknown"),
        "description": payload.get("description"),
        "address": payload.get("address"),
        "latitude": payload.get("latitude"),
        "longitude": payload.get("longitude"),
        "is_virtual": _boolish(payload.get("isVirtual")),
        "country": payload.get("country"),
        "municipality": payload.get("municipality"),
        "city": payload.get("city"),
        "zip_code": payload.get("zipCode"),
        "cost_center": payload.get("costCenter"),
        "state": int(payload.get("state", 0) or 0),
        "imagestion_cellar_id": _intish(payload.get("imagestionCellarId")),
        "code": payload.get("code"),
    }


def normalize_document_type(payload: dict) -> dict:
    return {
        "external_id": str(payload["id"]),
        "name": payload.get("name", "unknown"),
        "initial_number": _intish(payload.get("initialNumber")),
        "code_sii": payload.get("codeSii"),
        "is_electronic_document": _boolish(payload.get("isElectronicDocument")),
        "breakdown_tax": _boolish(payload.get("breakdownTax")),
        "use": _intish(payload.get("use")),
        "is_sales_note": _boolish(payload.get("isSalesNote")),
        "is_exempt": _boolish(payload.get("isExempt")),
        "restricts_tax": _boolish(payload.get("restrictsTax")),
        "use_client": _boolish(payload.get("useClient")),
        "message_body_format": payload.get("messageBodyFormat"),
        "thermal_printer": _boolish(payload.get("thermalPrinter")),
        "state": int(payload.get("state", 0) or 0),
        "copy_number": _intish(payload.get("copyNumber")),
        "is_credit_note": _boolish(payload.get("isCreditNote")),
        "continued_high": _boolish(payload.get("continuedHigh")),
        "ledger_account": payload.get("ledgerAccount"),
        "ipad_print": _boolish(payload.get("ipadPrint")),
        "ipad_print_high": _boolish(payload.get("ipadPrintHigh")),
        "book_type_id": _extract_ref_id(payload.get("book_type")),
        "is_active": int(payload.get("state", 0) or 0) == 0,
    }


def normalize_stock(payload: dict) -> dict:
    return {
        "product_external_id": str(payload["productid"]),
        "branch_external_id": str(payload["officeid"]),
        "quantity": payload.get("quantity", 0),
    }


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
