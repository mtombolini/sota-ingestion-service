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


def normalize_sales_document(payload: dict) -> dict:
    issued_at = payload.get("emissiondate") or payload.get("createdate")
    dt = datetime.fromisoformat(issued_at.replace("Z", "+00:00")) if issued_at else datetime.utcnow()
    return {
        "external_id": str(payload["id"]),
        "branch_external_id": str(payload.get("officeid")) if payload.get("officeid") else None,
        "issued_at": dt,
        "customer_external_id": str(payload.get("client", {}).get("id")) if payload.get("client") else None,
        "total_amount": payload.get("totalamount", 0),
        "lines": [
            {
                "product_external_id": str(line.get("variantId") or line.get("productId") or "0"),
                "quantity": line.get("quantity", 0),
                "unit_price": line.get("netUnitValue", 0),
            }
            for line in payload.get("details", [])
        ],
    }
