from celery import shared_task

from apps.jobs.services.normalization import JobNormalizationService
from apps.jobs.services.freshness import JobFreshnessService
from apps.jobs.services.fixture_ingestion import JobFixtureIngestionService


@shared_task
def normalize_raw_job_record(raw_record_id: int):
    return JobNormalizationService.normalize_record_by_id(raw_record_id)


@shared_task
def mark_stale_and_expired_jobs():
    results = JobFreshnessService.mark_stale_and_expired()
    return f"Freshness results: {results}"


@shared_task
def ingest_fixture_jobs(path: str, source_slug: str = "france_travail"):
    return JobFixtureIngestionService.ingest_fixture_and_dispatch_normalization(path, source_slug=source_slug)
