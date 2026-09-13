import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import update

from app.db.session import async_session_factory
from app.models.pipeline import ProcessingJob
from app.pipeline.services import pipeline_service
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.tasks.pipeline_tasks.process_survey_pipeline_task", max_retries=2)
def process_survey_pipeline_task(
    self,
    survey_id_str: str,
    job_id_str: str,
    sss_file_id_str: Optional[str] = None,
) -> dict:
    """
    Celery background worker task for side-scan sonar preprocessing.
    Orchestrates the 9 pure stages, persists artifacts, updates database progress,
    and prepares overlapping tiles for AI inference (Prompt G).
    """
    survey_id = UUID(survey_id_str)
    job_id = UUID(job_id_str)
    sss_file_id = UUID(sss_file_id_str) if sss_file_id_str else None

    logger.info(f"[Celery] Received task {self.request.id} for survey {survey_id}, job {job_id}")

    async def _run():
        async with async_session_factory() as db:
            # Record Celery task id
            await db.execute(
                update(ProcessingJob)
                .where(ProcessingJob.id == job_id)
                .values(celery_task_id=self.request.id)
            )
            await db.commit()

            try:
                # Execute full scientific preprocessing pipeline
                await pipeline_service.execute_survey_pipeline(
                    db=db,
                    survey_id=survey_id,
                    job_id=job_id,
                    sss_file_id=sss_file_id,
                )
            except Exception as exc:
                logger.error(f"[Celery] Pipeline execution failed for job {job_id}: {exc}", exc_info=True)
                await db.execute(
                    update(ProcessingJob)
                    .where(ProcessingJob.id == job_id)
                    .values(
                        status="failed",
                        error_message=str(exc),
                        completed_at=datetime.now(timezone.utc),
                    )
                )
                await db.commit()
                raise exc

    # Run in asyncio event loop
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_running():
        # Running inside another loop (e.g. test environment)
        future = asyncio.ensure_future(_run())
        return {"status": "dispatched", "job_id": job_id_str}
    else:
        loop.run_until_complete(_run())
        return {"status": "completed", "job_id": job_id_str, "survey_id": survey_id_str}
