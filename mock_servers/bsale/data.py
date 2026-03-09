PRODUCTS = [
    {"id": 101, "name": "Azeite Extra Virgem 500ml", "code": "SKU-OLV-500", "state": 0, "category": {"name": "Abarrotes"}, "unit": {"name": "UN"}},
    {"id": 102, "name": "Arroz Integral 1kg", "code": "SKU-RICE-1", "state": 0, "category": {"name": "Granos"}, "unit": {"name": "UN"}},
    {"id": 103, "name": "Leche Descremada 1L", "code": "SKU-MILK-1", "state": 0, "category": {"name": "Lácteos"}, "unit": {"name": "UN"}},
]

OFFICES = [
    {"id": 1, "name": "Casa Matriz Santiago", "code": "STGO"},
    {"id": 2, "name": "Sucursal Valparaíso", "code": "VAP"},
]

STOCKS = [
    {"id": 5001, "productid": 101, "officeid": 1, "quantity": 80},
    {"id": 5002, "productid": 102, "officeid": 1, "quantity": 120},
    {"id": 5003, "productid": 103, "officeid": 2, "quantity": 50},
]

# Documents matching real Bsale API structure
DOCUMENTS = [
    {
        "href": "https://api.bsale.io/v1/documents/9001.json",
        "id": 9001,
        "emissionDate": 1736935200,  # 2025-01-15 10:00 UTC
        "expirationDate": 1736935200,
        "generationDate": 1736935200,
        "number": 1001,
        "totalAmount": 39890.0,
        "netAmount": 33521.0,
        "taxAmount": 6369.0,
        "exemptAmount": 0.0,
        "state": 0,
        "document_type": {"href": "https://api.bsale.io/v1/document_types/1.json", "id": "1"},
        "client": {"href": "https://api.bsale.io/v1/clients/3001.json", "id": "3001"},
        "office": {"href": "https://api.bsale.io/v1/offices/1.json", "id": "1"},
        "user": {"href": "https://api.bsale.io/v1/users/1.json", "id": "1"},
        "details": {
            "href": "https://api.bsale.io/v1/documents/9001/details.json",
            "count": 2,
            "items": [
                {
                    "href": "https://api.bsale.io/v1/documents/9001/details/10001.json",
                    "id": 10001,
                    "lineNumber": 0,
                    "quantity": 2.0,
                    "netUnitValue": 8990.0,
                    "totalUnitValue": 10698.0,
                    "netAmount": 17980.0,
                    "taxAmount": 3416.0,
                    "totalAmount": 21396.0,
                    "netDiscount": 0.0,
                    "totalDiscount": 0.0,
                    "variant": {
                        "href": "https://api.bsale.io/v1/variants/201.json",
                        "id": 201,
                        "description": "Azeite 500ml",
                        "code": "SKU-OLV-500"
                    },
                    "note": "",
                    "relatedDetailId": 0
                },
                {
                    "href": "https://api.bsale.io/v1/documents/9001/details/10002.json",
                    "id": 10002,
                    "lineNumber": 1,
                    "quantity": 1.0,
                    "netUnitValue": 15541.0,
                    "totalUnitValue": 18494.0,
                    "netAmount": 15541.0,
                    "taxAmount": 2953.0,
                    "totalAmount": 18494.0,
                    "netDiscount": 0.0,
                    "totalDiscount": 0.0,
                    "variant": {
                        "href": "https://api.bsale.io/v1/variants/202.json",
                        "id": 202,
                        "description": "Arroz Integral 1kg",
                        "code": "SKU-RICE-1"
                    },
                    "note": "",
                    "relatedDetailId": 0
                }
            ]
        },
    },
    {
        "href": "https://api.bsale.io/v1/documents/9002.json",
        "id": 9002,
        "emissionDate": 1736964000,  # 2025-01-15 18:20 UTC
        "expirationDate": 1736964000,
        "generationDate": 1736964000,
        "number": 1002,
        "totalAmount": 10200.0,
        "netAmount": 8571.0,
        "taxAmount": 1629.0,
        "exemptAmount": 0.0,
        "state": 0,
        "document_type": {"href": "https://api.bsale.io/v1/document_types/1.json", "id": "1"},
        "client": {"href": "https://api.bsale.io/v1/clients/3002.json", "id": "3002"},
        "office": {"href": "https://api.bsale.io/v1/offices/2.json", "id": "2"},
        "user": {"href": "https://api.bsale.io/v1/users/1.json", "id": "1"},
        "details": {
            "href": "https://api.bsale.io/v1/documents/9002/details.json",
            "count": 1,
            "items": [
                {
                    "href": "https://api.bsale.io/v1/documents/9002/details/10003.json",
                    "id": 10003,
                    "lineNumber": 0,
                    "quantity": 4.0,
                    "netUnitValue": 2143.0,
                    "totalUnitValue": 2550.0,
                    "netAmount": 8571.0,
                    "taxAmount": 1629.0,
                    "totalAmount": 10200.0,
                    "netDiscount": 0.0,
                    "totalDiscount": 0.0,
                    "variant": {
                        "href": "https://api.bsale.io/v1/variants/203.json",
                        "id": 203,
                        "description": "Leche Descremada 1L",
                        "code": "SKU-MILK-1"
                    },
                    "note": "",
                    "relatedDetailId": 0
                }
            ]
        },
    },
]
