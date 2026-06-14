from django.test import TestCase
from unittest.mock import patch
from apps.jobs.models import JobSource, SourceType
from apps.jobs.tasks import normalize_raw_job_record, mark_stale_and_expired_jobs, ingest_fixture_jobs


class JobTasksTest(TestCase):
    def setUp(self):
        self.source = JobSource.objects.create(
            name="Test Source", slug="test_source", source_type=SourceType.FIXTURE
        )

    def test_normalize_raw_job_record_task(self):
        with patch(
            "apps.jobs.tasks.JobNormalizationService.normalize_record_by_id",
            return_value="Normalized raw record 123 into job 456",
        ) as normalize_record_by_id:
            result = normalize_raw_job_record(123)

        normalize_record_by_id.assert_called_once_with(123)
        self.assertIn("Normalized raw record", result)

    def test_normalize_raw_job_record_missing_id(self):
        result = normalize_raw_job_record(999999)
        self.assertIn("does not exist", result)

    def test_mark_stale_and_expired_jobs_task(self):
        with patch(
            "apps.jobs.tasks.JobFreshnessService.mark_stale_and_expired",
            return_value={"expired_count": 0, "removed_count": 0, "stale_count": 0, "active_count": 0},
        ) as mark_stale_and_expired:
            result = mark_stale_and_expired_jobs()

        mark_stale_and_expired.assert_called_once_with()
        self.assertIn("Freshness results", result)

    def test_ingest_fixture_jobs_task_calls_service(self):
        with patch(
            "apps.jobs.tasks.JobFixtureIngestionService.ingest_fixture_and_dispatch_normalization",
            return_value="Fixture ingestion complete: success. Fetched 1.",
        ) as ingest_fixture_and_dispatch_normalization:
            result = ingest_fixture_jobs("fixture.json", source_slug="france_travail")

        ingest_fixture_and_dispatch_normalization.assert_called_once_with(
            "fixture.json",
            source_slug="france_travail",
        )
        self.assertIn("Fixture ingestion complete", result)
