import asyncio

from app.core.database import SessionLocal
from app.services.ingestion_service import IngestionService
from app.workers.celery_app import celery_app


@celery_app.task(name="jobs.execute_run", bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def execute_run(self, run_id: int):
    db = SessionLocal()
    try:
        service = IngestionService(db)
        asyncio.run(service.execute_job_run(run_id))
    finally:
        db.close()
