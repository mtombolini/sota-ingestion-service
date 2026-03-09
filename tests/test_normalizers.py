from app.normalizers.bsale import normalize_branch, normalize_client, normalize_document_type, normalize_product


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
    assert out["name"] == "Prod"
    assert out["description"] == "Desc"
    assert out["classification"] == 1
    assert out["allow_decimal"] is True
    assert out["product_type_id"] == "3"
    assert out["sku"] == "SKU-500"
    assert out["variants"][0]["external_id"] == "500"
    assert out["product_taxes"][0]["tax_external_id"] == "1"


def test_normalize_client():
    payload = {
        "id": 3001,
        "firstName": "Pedro",
        "lastName": "Lopez",
        "email": "pedro@example.com",
        "code": "76123456-7",
        "phone": "+56911111111",
        "company": "Don Pedro",
        "note": "Frecuente",
        "facebook": "",
        "twitter": "",
        "hasCredit": 1,
        "maxCredit": "150000.0",
        "state": 0,
        "activity": "Retail",
        "city": "Santiago",
        "municipality": "Providencia",
        "address": "Av. Italia 1234",
        "companyOrPerson": 1,
        "points": 1200,
        "pointsUpdated": 1736935200,
        "accumulatePoints": 1,
        "sendDte": 1,
        "prestashopClienId": 0,
        "office": {"id": "1"},
        "contacts_items": [{"id": 31, "firstName": "Pedro", "lastName": "Lopez", "phone": "1", "email": "a@b.cl"}],
        "addresses_items": [{"id": 8, "addressName": "Casa matriz", "address": "Dir", "city": "SCL", "municipality": "Prov", "state": 0}],
        "attributes_items": [{"id": 44, "name": "Segmento", "value": "Mayorista"}],
    }

    out = normalize_client(payload)

    assert out["external_id"] == "3001"
    assert out["has_credit"] is True
    assert out["office_external_id"] == "1"
    assert out["points"] == 1200
    assert out["contacts"][0]["external_id"] == "31"
    assert out["addresses"][0]["address_name"] == "Casa matriz"
    assert out["attributes"][0]["name"] == "Segmento"


def test_normalize_branch():
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

    out = normalize_branch(payload)

    assert out["external_id"] == "1"
    assert out["is_virtual"] is False
    assert out["city"] == "Santiago"
    assert out["imagestion_cellar_id"] == 11
    assert out["code"] is None


def test_normalize_document_type():
    payload = {
        "id": 2,
        "name": "FACTURA ELECTRONICA",
        "initialNumber": 100,
        "codeSii": "33",
        "isElectronicDocument": 1,
        "breakdownTax": 1,
        "use": 0,
        "isSalesNote": 0,
        "isExempt": 0,
        "restrictsTax": 0,
        "useClient": 1,
        "messageBodyFormat": "",
        "thermalPrinter": 1,
        "state": 0,
        "copyNumber": 2,
        "isCreditNote": 0,
        "continuedHigh": 0,
        "ledgerAccount": None,
        "ipadPrint": 0,
        "ipadPrintHigh": "0",
        "book_type": {"id": "1"},
    }

    out = normalize_document_type(payload)

    assert out["external_id"] == "2"
    assert out["code_sii"] == "33"
    assert out["is_electronic_document"] is True
    assert out["use_client"] is True
    assert out["book_type_id"] == "1"
    assert out["is_active"] is True
