from celery import shared_task

from .services.request_runner import run_llm_request


@shared_task
def run_llm_request_task(user_id, purpose, messages, model=None):
    """
    Background task wrapper for the LLM request service.
    """
    return run_llm_request(user_id, purpose, messages, model=model)

import logging
from apps.jobs.models import NormalizedJob
from apps.llm.services.job_enrichment import enrich_job

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def enrich_job_task(self, job_id, force=False):
    try:
        job = NormalizedJob.objects.get(id=job_id)
        enrichment = enrich_job(job, force=force)
        return enrichment.status
    except NormalizedJob.DoesNotExist:
        logger.warning(f"NormalizedJob {job_id} not found for enrichment.")
        return "skipped"
    except Exception as exc:
        logger.error(f"Error enriching job {job_id}: {exc}")
        self.retry(exc=exc)
