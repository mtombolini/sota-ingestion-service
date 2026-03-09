# Bsale API – Endpoints integrados

## Autenticación
Header `access_token` en todas las peticiones.

## Endpoints activos

### 1. Productos – `GET /v1/products.json`
- **Job:** `sync_product_catalog`
- **Tabla canónica:** `products`
- **Campos:** external_id, sku, name, category, unit, is_active

### 2. Sucursales – `GET /v1/offices.json`
- **Job:** `sync_branches`
- **Tabla canónica:** `branches`
- **Campos:** external_id, name, code

### 3. Stock – `GET /v1/stocks.json`
- **Job:** `sync_stock_snapshot`
- **Tabla canónica:** `stock_snapshots`
- **Campos:** product_external_id, branch_external_id, quantity, captured_at

### 4. Documentos – `GET /v1/documents.json?expand=details&state=0`
- **Job:** `sync_sales_documents`
- **Tablas canónicas:** `sales_documents` + `sales_document_lines`
- **Campos documento:** external_id, document_type_id, number (folio), branch_external_id, issued_at, customer_external_id, net_amount, tax_amount, exempt_amount, total_amount, state
- **Campos línea:** line_number, variant_external_id, variant_code, product_external_id, quantity, unit_price, net_amount, tax_amount, total_amount, discount
- **Nota:** `emissionDate` de Bsale es epoch integer. Se parsea a datetime. Los detalles vienen expandidos inline con referencia a variant (id, code, description).

## Endpoints evaluados y descartados (no operacionales)
- `POST/PUT/DELETE /v1/documents.json` – Solo ingesta, no creamos documentos.
- `GET /v1/documents/{id}/references.json` – Compliance SII, no operacional.
- `GET /v1/documents/{id}/document_taxes.json` – Ya capturamos taxAmount agregado.
- `GET /v1/documents/{id}/sellers.json` – No relevante para operaciones.
- `GET /v1/documents/{id}/attributes.json` – Atributos dinámicos custom.
- `GET /v1/documents/summary.json` – Resúmenes que podemos computar.
- `GET /v1/documents/count.json` – Auxiliar.

## Endpoints pendientes de evaluación
- `GET /v1/documents/costs.json` – Costo por variante por venta. Requiere llamada por documento. Evaluar si se implementa como enriquecimiento posterior.

## Paginación
Mock soporta `limit` y `offset`. Real API: limit max 50, offset paginado.
