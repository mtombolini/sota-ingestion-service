# sota-ingestion-service

Servicio de ingesta para SotA (Python/FastAPI) con soporte Bsale en **modo real** y **modo mock**.

## Qué incluye
- API administrativa (`/admin/*`)
- Jobs de ingesta reintentables (Celery)
- Persistencia raw + canónica + outbox
- Mock server Bsale compatible por contrato en endpoints críticos
- Docker Compose para ambiente local completo

## Estructura
- `app/` API, dominio de ingesta, conectores, jobs, normalizadores.
- `mock_servers/bsale/` mock API local Bsale.
- `alembic/` migraciones.
- `scripts/` utilidades de ejecución y seed.
- `tests/` pruebas mínimas.

## Quickstart
1. Copia variables:
   ```bash
   cp .env.example .env
   ```
2. Levanta stack:
   ```bash
   make up
   ```
3. Healthcheck:
   ```bash
   curl http://localhost:8000/admin/health
   ```
4. Listar jobs:
   ```bash
   curl http://localhost:8000/admin/jobs
   ```
5. Disparar job manual:
   ```bash
   curl -X POST http://localhost:8000/admin/jobs/1/runs
   ```
6. Revisar corridas y errores:
   ```bash
   curl http://localhost:8000/admin/runs
   curl http://localhost:8000/admin/errors
   ```

## Modo mock vs real
La conexión se define en `integration_connections.mode`.
- `mock`: usar `base_url=http://mock-bsale-api:8010/v1`
- `real`: configurar `base_url` y token real de Bsale

La implementación del conector usa el mismo cliente HTTP y endpoints; cambia solo URL/token.

## Endpoints administrativos
- `GET /admin/health`
- `GET /admin/connectors`
- `GET /admin/jobs`
- `POST /admin/jobs/{job_id}/runs`
- `GET /admin/runs`
- `GET /admin/errors`
- `GET /admin/mappings`

## Jobs disponibles
- `sync_product_catalog`
- `sync_stock_snapshot`
- `sync_sales_documents`
- `sync_branches`

## Notas de diseño
- Mappings versionados en `integration_mappings` (estrategia estática aprobada)
- Raw landing trazable por checksum y endpoint
- Outbox PostgreSQL en `integration_outbox_events`
- Espacio preparado para watermarks y mejoras de incrementalidad
