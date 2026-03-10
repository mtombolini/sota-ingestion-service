from app.normalizers.bsale import (
    normalize_location,
    normalize_product,
    normalize_sales_order,
    normalize_stock,
    normalize_stock_consumption,
    normalize_stock_reception,
)


def test_normalize_product():
    payload = {
        "id": 10,
        "name": "Prod",
        "description": "Desc",
        "classification": 1,
        "ledgerAccount": "VENTAS",
        "costCenter": "SERV",
        "allowDecimal": 1,
        "stockControl": 0,
        "printDetailPack": 0,
        "state": 0,
        "prestashopProductId": 0,
        "presashopAttributeId": 0,
        "product_type": {"id": "3"},
        "variants": [
            {
                "id": 500,
                "description": "Variante base",
                "code": "SKU-500",
                "barCode": "780500",
                "unlimitedStock": 0,
                "allowNegativeStock": 0,
                "state": 0,
                "serialNumber": 0,
                "prestashopCombinationId": 0,
                "prestashopValueId": 0,
            }
        ],
        "product_taxes_items": [{"id": "99", "tax": {"id": "1"}}],
    }
    out = normalize_product(payload)
    assert out["external_id"] == "10"
    assert out["source_system"] == "bsale"
    assert out["name"] == "Prod"
    assert out["sku"] == "SKU-500"
    assert out["is_active"] is True
    assert len(out["variants"]) == 1
    assert out["variants"][0]["external_id"] == "500"
    assert out["variants"][0]["product_external_id"] == "10"
    assert out["variants"][0]["sku"] == "SKU-500"
    # Bsale-specific fields like classification and taxes are NOT in the canonical output
    assert "classification" not in out
    assert "product_taxes" not in out
    # Canonical fields that Bsale doesn't provide
    assert out["brand"] is None
    assert out["unit_of_measure"] is None
    assert out["unit_cost"] is None


def test_normalize_location():
    payload = {
        "id": 1,
        "name": "Casa Matriz Santiago",
        "description": "Sucursal principal",
        "address": "Av. Italia 1234",
        "latitude": "-33.4372",
        "longitude": "-70.6506",
        "isVirtual": 0,
        "country": "Chile",
        "municipality": "Providencia",
        "city": "Santiago",
        "zipCode": "7500000",
        "costCenter": "CC-SCL",
        "state": 0,
        "imagestionCellarId": 11,
    }

    out = normalize_location(payload)

    assert out["external_id"] == "1"
    assert out["source_system"] == "bsale"
    assert out["name"] == "Casa Matriz Santiago"
    assert out["type"] == "STORE"
    assert out["city"] == "Santiago"
    assert out["region"] == "Chile"
    assert out["is_active"] is True
    # Bsale-specific fields are NOT in canonical output
    assert "imagestion_cellar_id" not in out
    assert "is_virtual" not in out


def test_normalize_stock():
    payload = {
        "variantid": 201,
        "officeid": 1,
        "quantity": 42.5,
    }

    out = normalize_stock(payload)

    assert out["source_system"] == "bsale"
    assert out["external_id"] == "201:1"
    assert out["variant_external_id"] == "201"
    assert out["location_external_id"] == "1"
    assert out["quantity_on_hand"] == 42.5
    assert out["quantity_available"] == 42.5
    assert out["quantity_reserved"] == 0
    assert out["quantity_in_transit"] == 0


def test_normalize_stock_accepts_office_object():
    payload = {
        "variant": {"id": "201"},
        "office": {"id": "1"},
        "quantity": 42.5,
    }

    out = normalize_stock(payload)

    assert out["external_id"] == "201:1"
    assert out["variant_external_id"] == "201"
    assert out["location_external_id"] == "1"


def test_normalize_sales_order():
    payload = {
        "id": 5001,
        "emissionDate": 1700000000,
        "office": {"id": "1"},
        "client": {"id": "3001"},
        "document_type": {"id": "2"},
        "totalAmount": 15000,
        "netAmount": 12605,
        "taxAmount": 2395,
        "exemptAmount": 0,
        "state": 0,
        "details": [
            {
                "lineNumber": 1,
                "variant": {"id": "201", "code": "SKU-OLV-500"},
                "quantity": 2,
                "netUnitValue": 6000,
                "netDiscount": 0,
                "totalAmount": 14280,
            }
        ],
    }

    out = normalize_sales_order(payload)

    assert out["source_system"] == "bsale"
    assert out["external_id"] == "5001"
    assert out["location_external_id"] == "1"
    assert out["customer_ref"] == "3001"
    assert out["total_amount"] == 15000
    assert out["currency"] == "CLP"
    assert out["channel"] == "STORE"
    assert out["status"] == "CONFIRMED"
    assert len(out["lines"]) == 1
    line = out["lines"][0]
    assert line["variant_external_id"] == "201"
    assert line["quantity"] == 2
    assert line["unit_price"] == 6000
    assert line["discount_pct"] == 0


def test_normalize_sales_order_cancelled():
    payload = {
        "id": 5002,
        "emissionDate": 1700000000,
        "office": {"id": "1"},
        "totalAmount": 5000,
        "state": 1,
        "details": [],
    }

    out = normalize_sales_order(payload)
    assert out["status"] == "CANCELLED"


def test_normalize_stock_reception():
    payload = {
        "id": 7001,
        "receptionDate": 1700000000,
        "office": {"id": "1"},
        "details": [
            {"id": 1, "variant": {"id": "201"}, "quantity": 5, "cost": 1200},
        ],
    }

    out = normalize_stock_reception(payload)

    assert len(out["movements"]) == 1
    movement = out["movements"][0]
    assert movement["movement_type"] == "RECEPTION_IN"
    assert movement["variant_external_id"] == "201"
    assert movement["location_external_id"] == "1"
    assert movement["quantity"] == 5


def test_normalize_stock_reception_accepts_lowercase_officeid():
    payload = {
        "id": 7001,
        "receptionDate": 1700000000,
        "officeid": 1,
        "details": [
            {"id": 1, "variant": {"id": "201"}, "quantity": 5, "cost": 1200},
        ],
    }

    out = normalize_stock_reception(payload)

    assert out["movements"][0]["location_external_id"] == "1"


def test_normalize_stock_consumption():
    payload = {
        "id": 8001,
        "consumptionDate": 1700000000,
        "office": {"id": "2"},
        "details": [
            {"id": 1, "variant": {"id": "203"}, "quantity": 3, "cost": 900},
        ],
    }

    out = normalize_stock_consumption(payload)

    assert len(out["movements"]) == 1
    movement = out["movements"][0]
    assert movement["movement_type"] == "CONSUMPTION_OUT"
    assert movement["variant_external_id"] == "203"
    assert movement["location_external_id"] == "2"
    assert movement["quantity"] == -3


def test_normalize_stock_consumption_accepts_lowercase_officeid():
    payload = {
        "id": 8001,
        "consumptionDate": 1700000000,
        "officeid": 2,
        "details": [
            {"id": 1, "variant": {"id": "203"}, "quantity": 3, "cost": 900},
        ],
    }

    out = normalize_stock_consumption(payload)

    assert out["movements"][0]["location_external_id"] == "2"
