# Bsale API Doc (subset usado)

Se utiliza un subconjunto consistente para primera fase de ingesta:

- `GET /v1/products.json`
- `GET /v1/stocks.json`
- `GET /v1/offices.json`
- `GET /v1/documents/sales.json`

Contrato de autenticación usado: header `access_token`.

Respuestas simuladas en mock:
```json
{"items": [...], "count": 3}
```

Se asume paginación opcional para fase futura.
