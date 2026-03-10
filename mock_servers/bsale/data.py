PRODUCTS = [
    {
        "href": "https://api.bsale.io/v1/products/101.json",
        "id": 101,
        "name": "Azeite Extra Virgem",
        "description": "Aceite de oliva 500ml",
        "classification": 0,
        "ledgerAccount": "ACEITES",
        "costCenter": "ABARROTES",
        "allowDecimal": 0,
        "stockControl": 1,
        "printDetailPack": 0,
        "state": 0,
        "prestashopProductId": 0,
        "presashopAttributeId": 0,
        "product_type": {
            "href": "https://api.bsale.io/v1/product_types/1.json",
            "id": "1",
        },
        "product_taxes": {
            "href": "https://api.bsale.io/v1/products/101/product_taxes.json"
        },
    },
    {
        "href": "https://api.bsale.io/v1/products/102.json",
        "id": 102,
        "name": "Arroz Integral",
        "description": "Arroz integral 1kg",
        "classification": 0,
        "ledgerAccount": "GRANOS",
        "costCenter": "ABARROTES",
        "allowDecimal": 0,
        "stockControl": 1,
        "printDetailPack": 0,
        "state": 0,
        "prestashopProductId": 0,
        "presashopAttributeId": 0,
        "product_type": {
            "href": "https://api.bsale.io/v1/product_types/1.json",
            "id": "1",
        },
        "product_taxes": {
            "href": "https://api.bsale.io/v1/products/102/product_taxes.json"
        },
    },
    {
        "href": "https://api.bsale.io/v1/products/103.json",
        "id": 103,
        "name": "Leche Descremada",
        "description": "Leche descremada 1L",
        "classification": 0,
        "ledgerAccount": "LACTEOS",
        "costCenter": "REFRIGERADOS",
        "allowDecimal": 0,
        "stockControl": 1,
        "printDetailPack": 0,
        "state": 0,
        "prestashopProductId": 0,
        "presashopAttributeId": 0,
        "product_type": {
            "href": "https://api.bsale.io/v1/product_types/1.json",
            "id": "1",
        },
        "product_taxes": {
            "href": "https://api.bsale.io/v1/products/103/product_taxes.json"
        },
    },
]

PRODUCT_VARIANTS = {
    101: [
        {
            "href": "https://api.bsale.io/v1/variants/201.json",
            "id": 201,
            "description": "Azeite 500ml",
            "unlimitedStock": 0,
            "allowNegativeStock": 0,
            "state": 0,
            "barCode": "7801000000201",
            "code": "SKU-OLV-500",
            "serialNumber": 0,
            "prestashopCombinationId": 0,
            "prestashopValueId": 0,
            "product": {"href": "https://api.bsale.io/v1/products/101.json", "id": "101"},
            "attribute_values": {"href": "https://api.bsale.io/v1/variants/201/attribute_values.json"},
            "costs": {"href": "https://api.bsale.io/v1/variants/201/costs.json"},
        }
    ],
    102: [
        {
            "href": "https://api.bsale.io/v1/variants/202.json",
            "id": 202,
            "description": "Arroz Integral 1kg",
            "unlimitedStock": 0,
            "allowNegativeStock": 0,
            "state": 0,
            "barCode": "7801000000202",
            "code": "SKU-RICE-1",
            "serialNumber": 0,
            "prestashopCombinationId": 0,
            "prestashopValueId": 0,
            "product": {"href": "https://api.bsale.io/v1/products/102.json", "id": "102"},
            "attribute_values": {"href": "https://api.bsale.io/v1/variants/202/attribute_values.json"},
            "costs": {"href": "https://api.bsale.io/v1/variants/202/costs.json"},
        }
    ],
    103: [
        {
            "href": "https://api.bsale.io/v1/variants/203.json",
            "id": 203,
            "description": "Leche Descremada 1L",
            "unlimitedStock": 0,
            "allowNegativeStock": 0,
            "state": 0,
            "barCode": "7801000000203",
            "code": "SKU-MILK-1",
            "serialNumber": 0,
            "prestashopCombinationId": 0,
            "prestashopValueId": 0,
            "product": {"href": "https://api.bsale.io/v1/products/103.json", "id": "103"},
            "attribute_values": {"href": "https://api.bsale.io/v1/variants/203/attribute_values.json"},
            "costs": {"href": "https://api.bsale.io/v1/variants/203/costs.json"},
        }
    ],
}

PRODUCT_TAXES = {
    101: [
        {
            "href": "https://api.bsale.io/v1/products/101/product_taxes/1001.json",
            "id": "1001",
            "tax": {"href": "https://api.bsale.io/v1/taxes/1.json", "id": "1"},
        }
    ],
    102: [
        {
            "href": "https://api.bsale.io/v1/products/102/product_taxes/1002.json",
            "id": "1002",
            "tax": {"href": "https://api.bsale.io/v1/taxes/1.json", "id": "1"},
        }
    ],
    103: [
        {
            "href": "https://api.bsale.io/v1/products/103/product_taxes/1003.json",
            "id": "1003",
            "tax": {"href": "https://api.bsale.io/v1/taxes/1.json", "id": "1"},
        }
    ],
}

OFFICES = [
    {
        "href": "https://api.bsale.io/v1/offices/1.json",
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
    },
    {
        "href": "https://api.bsale.io/v1/offices/2.json",
        "id": 2,
        "name": "Sucursal Valparaiso",
        "description": "Punto de venta costa",
        "address": "Errázuriz 456",
        "latitude": "-33.0458",
        "longitude": "-71.6197",
        "isVirtual": 0,
        "country": "Chile",
        "municipality": "Valparaiso",
        "city": "Valparaiso",
        "zipCode": "2340000",
        "costCenter": "CC-VAP",
        "state": 0,
        "imagestionCellarId": 12,
    },
]

DOCUMENT_TYPES = [
    {
        "href": "https://api.bsale.io/v1/document_types/1.json",
        "id": 1,
        "name": "NOTA VENTA",
        "initialNumber": 1,
        "codeSii": "",
        "isElectronicDocument": 0,
        "breakdownTax": 1,
        "use": 0,
        "isSalesNote": 1,
        "isExempt": 0,
        "restrictsTax": 0,
        "useClient": 1,
        "messageBodyFormat": None,
        "thermalPrinter": 1,
        "state": 0,
        "copyNumber": 3,
        "isCreditNote": 0,
        "continuedHigh": 0,
        "ledgerAccount": None,
        "ipadPrint": 0,
        "ipadPrintHigh": "0",
    },
    {
        "href": "https://api.bsale.io/v1/document_types/2.json",
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
        "book_type": {"href": "https://api.bsale.io/v1/book_types/1.json", "id": "1"},
    },
    {
        "href": "https://api.bsale.io/v1/document_types/3.json",
        "id": 3,
        "name": "NOTA CREDITO ELECTRONICA",
        "initialNumber": 43,
        "codeSii": "61",
        "isElectronicDocument": 1,
        "breakdownTax": 1,
        "use": 1,
        "isSalesNote": 0,
        "isExempt": 0,
        "restrictsTax": 0,
        "useClient": 1,
        "messageBodyFormat": "",
        "thermalPrinter": 1,
        "state": 0,
        "copyNumber": 0,
        "isCreditNote": 1,
        "continuedHigh": 0,
        "ledgerAccount": None,
        "ipadPrint": 0,
        "ipadPrintHigh": "0",
        "book_type": {"href": "https://api.bsale.io/v1/book_types/1.json", "id": "1"},
    },
]

STOCKS = [
    {"id": 5001, "productid": 101, "variantid": 201, "officeid": 1, "quantity": 80},
    {"id": 5002, "productid": 102, "variantid": 202, "officeid": 1, "quantity": 120},
    {"id": 5003, "productid": 103, "variantid": 203, "officeid": 2, "quantity": 50},
]

STOCK_RECEPTIONS = [
    {
        "href": "https://api.bsale.io/v1/stocks/receptions/7001.json",
        "id": 7001,
        "receptionDate": 1736852400,
        "office": {"href": "https://api.bsale.io/v1/offices/1.json", "id": "1"},
        "details": {
            "count": 2,
            "items": [
                {
                    "id": 71001,
                    "lineNumber": 0,
                    "quantity": 40,
                    "cost": 5200,
                    "variant": {"href": "https://api.bsale.io/v1/variants/201.json", "id": "201"},
                },
                {
                    "id": 71002,
                    "lineNumber": 1,
                    "quantity": 30,
                    "cost": 1200,
                    "variant": {"href": "https://api.bsale.io/v1/variants/202.json", "id": "202"},
                },
            ],
        },
    }
]

STOCK_CONSUMPTIONS = [
    {
        "href": "https://api.bsale.io/v1/stocks/consumptions/8001.json",
        "id": 8001,
        "consumptionDate": 1736940000,
        "office": {"href": "https://api.bsale.io/v1/offices/2.json", "id": "2"},
        "details": {
            "count": 1,
            "items": [
                {
                    "id": 81001,
                    "lineNumber": 0,
                    "quantity": 3,
                    "cost": 1500,
                    "variant": {"href": "https://api.bsale.io/v1/variants/203.json", "id": "203"},
                }
            ],
        },
    }
]

CLIENTS = [
    {
        "href": "https://api.bsale.io/v1/clients/3001.json",
        "id": 3001,
        "firstName": "Pedro",
        "lastName": "Lopez",
        "email": "pedro@donpedro.cl",
        "code": "76123456-7",
        "phone": "+56911111111",
        "company": "Minimarket Don Pedro",
        "note": "Cliente frecuente",
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
        "office": {"href": "https://api.bsale.io/v1/offices/1.json", "id": "1"},
        "contacts": {"href": "https://api.bsale.io/v1/clients/3001/contacts.json"},
        "attributes": {"href": "https://api.bsale.io/v1/clients/3001/attributes.json"},
        "addresses": {"href": "https://api.bsale.io/v1/clients/3001/addresses.json"},
    },
    {
        "href": "https://api.bsale.io/v1/clients/3002.json",
        "id": 3002,
        "firstName": "Ana",
        "lastName": "Costa",
        "email": "compras@lacosta.cl",
        "code": "76999999-1",
        "phone": "+56922222222",
        "company": "Restaurante La Costa",
        "note": "",
        "facebook": "",
        "twitter": "",
        "hasCredit": 0,
        "maxCredit": "0.0",
        "state": 0,
        "activity": "Restaurant",
        "city": "Valparaiso",
        "municipality": "Valparaiso",
        "address": "Errázuriz 456",
        "companyOrPerson": 1,
        "points": 300,
        "pointsUpdated": "",
        "accumulatePoints": 0,
        "sendDte": 1,
        "prestashopClienId": 0,
        "office": {"href": "https://api.bsale.io/v1/offices/2.json", "id": "2"},
        "contacts": {"href": "https://api.bsale.io/v1/clients/3002/contacts.json"},
        "attributes": {"href": "https://api.bsale.io/v1/clients/3002/attributes.json"},
        "addresses": {"href": "https://api.bsale.io/v1/clients/3002/addresses.json"},
    },
]

CLIENT_CONTACTS = {
    3001: [
        {
            "href": "https://api.bsale.io/v1/clients/3001/contacts/31.json",
            "id": 31,
            "firstName": "Pedro",
            "lastName": "Lopez",
            "phone": "+56911111111",
            "email": "pedro@donpedro.cl",
        }
    ],
    3002: [
        {
            "href": "https://api.bsale.io/v1/clients/3002/contacts/32.json",
            "id": 32,
            "firstName": "Ana",
            "lastName": "Costa",
            "phone": "+56922222222",
            "email": "compras@lacosta.cl",
        },
        {
            "href": "https://api.bsale.io/v1/clients/3002/contacts/33.json",
            "id": 33,
            "firstName": "Miguel",
            "lastName": "Rojas",
            "phone": "+56933333333",
            "email": "bodega@lacosta.cl",
        },
    ],
}

CLIENT_ADDRESSES = {
    3001: [
        {
            "href": "https://api.bsale.io/v1/clients/3001/addresses/8.json",
            "id": 8,
            "addressName": "Casa matriz",
            "address": "Av. Italia 1234",
            "city": "Santiago",
            "municipality": "Providencia",
            "state": 0,
        }
    ],
    3002: [
        {
            "href": "https://api.bsale.io/v1/clients/3002/addresses/9.json",
            "id": 9,
            "addressName": "Sucursal puerto",
            "address": "Errázuriz 456",
            "city": "Valparaiso",
            "municipality": "Valparaiso",
            "state": 0,
        }
    ],
}

CLIENT_ATTRIBUTES = {
    3001: [
        {
            "href": "https://api.bsale.io/v1/dynamic_attributes/44.json",
            "id": 44,
            "name": "Segmento",
            "value": "Mayorista",
        }
    ],
    3002: [
        {
            "href": "https://api.bsale.io/v1/dynamic_attributes/45.json",
            "id": 45,
            "name": "Canal",
            "value": "Food Service",
        }
    ],
}

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

SALES = DOCUMENTS
