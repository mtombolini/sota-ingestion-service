# Instruction

Este repositorio implementa un servicio de ingesta independiente para SotA con:
- API administrativa FastAPI
- Worker Celery
- Conector Bsale con modo real/mock
- Persistencia raw + canónica + outbox
- Observabilidad básica y trazabilidad por job_run
