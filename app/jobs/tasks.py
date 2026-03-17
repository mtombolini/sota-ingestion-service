import asyncio
import logging
import time

from app.core.database import SessionLocal
from app.services.ingestion_service import IngestionService
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="jobs.execute_run", bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def execute_run(self, run_id: int):
    logger.info("Starting job run %d (attempt %d/%d)", run_id, self.request.retries + 1, self.max_retries + 1)
    t0 = time.monotonic()
    db = SessionLocal()
    try:
        service = IngestionService(db)
        asyncio.run(service.execute_job_run(run_id))
        elapsed_ms = int((time.monotonic() - t0) * 1000)
        logger.info("Job run %d completed in %dms", run_id, elapsed_ms)
    except Exception:
        elapsed_ms = int((time.monotonic() - t0) * 1000)
        logger.exception("Job run %d failed after %dms", run_id, elapsed_ms)
        raise
    finally:
        db.close()
