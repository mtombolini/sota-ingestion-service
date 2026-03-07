# SotA Ingestion Service

## Arquitectura
- API administrativa para operación y monitoreo.
- Orquestación asíncrona de corridas de ingesta.
- Conector Bsale con contrato HTTP compatible en modo mock.
- Persistencia en PostgreSQL mediante SQLAlchemy + Alembic.
- Redis/Celery para ejecución de jobs reintentables.

## Modelo canónico mínimo
- products
- branches
- stock_snapshots
- sales_documents y sales_document_lines

## Integración
- integration_connections
- integration_jobs
- integration_job_runs
- integration_mappings
- integration_raw_objects
- integration_errors
- integration_watermarks
- integration_outbox_events
