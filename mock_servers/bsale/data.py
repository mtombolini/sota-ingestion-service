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

SALES = [
    {
        "id": 9001,
        "officeid": 1,
        "emissiondate": "2025-01-15T10:00:00Z",
        "totalamount": 39890,
        "client": {"id": 3001, "name": "Minimarket Don Pedro"},
        "details": [
            {"lineNumber": 1, "variantId": 101, "quantity": 2, "netUnitValue": 8990},
            {"lineNumber": 2, "variantId": 102, "quantity": 1, "netUnitValue": 21910},
        ],
    },
    {
        "id": 9002,
        "officeid": 2,
        "emissiondate": "2025-01-15T18:20:00Z",
        "totalamount": 10200,
        "client": {"id": 3002, "name": "Restaurante La Costa"},
        "details": [
            {"lineNumber": 1, "variantId": 103, "quantity": 4, "netUnitValue": 2550}
        ],
    },
]
