"""
Phase 14J — Ingestion observability tests.

Tests that:
- Successful ingestion updates JobSource.last_successful_sync_at
- Failed ingestion does NOT update JobSource.last_successful_sync_at
- Scheduled (celery) trigger uses conservative keyword defaults
"""
from unittest.mock import patch, MagicMock
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone

from apps.jobs.models import (
    JobIngestionConfig,
    JobIngestionRun,
    JobSource,
    SourceType,
    RawJobRecord,
)
from apps.jobs.services.ingestion import JobIngestionService
from apps.jobs.services.broad_it_preset import (
    SCHEDULED_IT_KEYWORDS,
    BROAD_IT_KEYWORDS,
    get_scheduled_keywords,
    get_preset_keywords,
)


def _make_ft_result(count: int = 5) -> dict:
    """Build a fake France Travail API response with *count* job dicts."""
    return {
        "resultats": [
            {
                "id": f"FT-TEST-{i}",
                "intitule": f"Test Job {i}",
                "entreprise": {"nom": "TestCorp"},
                "lieuTravail": {"libelle": "Paris"},
                "typeContrat": "CDI",
                "description": "Test description for job listing.",
            }
            for i in range(count)
        ]
    }


class ScheduledKeywordsTest(TestCase):
    """Verify the curated scheduled keyword subset."""

    def test_scheduled_keywords_is_subset_of_broad_it(self):
        for kw in SCHEDULED_IT_KEYWORDS:
            self.assertIn(kw, BROAD_IT_KEYWORDS)

    def test_scheduled_keywords_reasonable_count(self):
        """Scheduled keyword list should be small (5-15) for conservative API usage."""
        self.assertGreaterEqual(len(SCHEDULED_IT_KEYWORDS), 5)
        self.assertLessEqual(len(SCHEDULED_IT_KEYWORDS), 15)

    def test_get_scheduled_keywords_returns_list(self):
        result = get_scheduled_keywords()
        self.assertIsInstance(result, list)
        self.assertEqual(result, SCHEDULED_IT_KEYWORDS)


class IngestionJobSourceSyncTest(TestCase):
    """Test that ingestion updates JobSource.last_successful_sync_at."""

    def setUp(self):
        self.config = JobIngestionConfig.objects.create(
            name="test_config",
            enabled=True,
            preset="broad_it",
            limit_per_keyword=5,
            max_total_per_run=10,
            max_pages_per_keyword=1,
            normalize_after_fetch=False,
            enrichment_enabled=False,
            dry_run=False,
        )
        # Pre-create the source so we can check its state
        self.source = JobSource.objects.create(
            slug="france_travail",
            name="France Travail",
            base_url="https://candidat.francetravail.fr/offres/recherche",
            source_type=SourceType.API,
            is_active=True,
        )

    @patch("apps.jobs.services.ingestion.FranceTravailClient")
    def test_successful_ingestion_updates_job_source_last_sync(self, MockClient):
        """Successful ingestion should set JobSource.last_successful_sync_at."""
        mock_client = MockClient.return_value
        mock_client.search_offers.return_value = _make_ft_result(3)

        self.assertIsNone(self.source.last_successful_sync_at)

        run_log = JobIngestionService.run(
            self.config,
            trigger="manual",
            overrides={"custom_keywords": ["test"]},
        )

        self.assertIn(run_log.status, ["success", "partial_success"])

        self.source.refresh_from_db()
        self.assertIsNotNone(self.source.last_successful_sync_at)

    @patch("apps.jobs.services.ingestion.FranceTravailClient")
    def test_successful_ingestion_finalizes_run(self, MockClient):
        mock_client = MockClient.return_value
        mock_client.search_offers.return_value = _make_ft_result(1)

        run_log = JobIngestionService.run(
            self.config,
            trigger="celery",
            overrides={"custom_keywords": ["python"]},
        )

        self.assertEqual(run_log.status, "success")
        self.assertIsNotNone(run_log.finished_at)

    def test_exception_finalizes_run_as_failed(self):
        with patch.object(JobIngestionService, "_run_with_log", side_effect=RuntimeError("boom")):
            with self.assertRaises(RuntimeError):
                JobIngestionService.run(self.config, trigger="celery")

        run_log = JobIngestionRun.objects.latest("started_at")
        self.assertEqual(run_log.status, "failed")
        self.assertIsNotNone(run_log.finished_at)
        self.assertIn("Unhandled ingestion error", run_log.error_summary)

    @patch("apps.jobs.services.ingestion.FranceTravailClient")
    def test_failed_ingestion_does_not_update_job_source_last_sync(self, MockClient):
        """Failed ingestion should NOT set JobSource.last_successful_sync_at."""
        mock_client = MockClient.return_value
        mock_client.search_offers.side_effect = Exception("API down")

        run_log = JobIngestionService.run(
            self.config,
            trigger="manual",
            overrides={"custom_keywords": ["test"]},
        )

        self.assertEqual(run_log.status, "failed")

        self.source.refresh_from_db()
        self.assertIsNone(self.source.last_successful_sync_at)

    @patch("apps.jobs.services.ingestion.FranceTravailClient")
    def test_successful_ingestion_updates_config_last_success(self, MockClient):
        """Successful run should also update JobIngestionConfig.last_success_at."""
        mock_client = MockClient.return_value
        mock_client.search_offers.return_value = _make_ft_result(2)

        self.assertIsNone(self.config.last_success_at)

        JobIngestionService.run(
            self.config,
            trigger="manual",
            overrides={"custom_keywords": ["test"]},
        )

        self.config.refresh_from_db()
        self.assertIsNotNone(self.config.last_success_at)

    @patch("apps.jobs.services.ingestion.FranceTravailClient")
    def test_partial_success_scheduled_ingestion_updates_job_source_last_sync(self, MockClient):
        """Partial-success scheduled ingestion still counts as a successful source sync."""
        mock_client = MockClient.return_value
        mock_client.search_offers.side_effect = [
            _make_ft_result(1),
            Exception("temporary API failure"),
        ]

        run_log = JobIngestionService.run(
            self.config,
            trigger="celery",
            overrides={"custom_keywords": ["python", "django"]},
        )

        self.assertEqual(run_log.status, "partial_success")
        self.source.refresh_from_db()
        self.assertIsNotNone(self.source.last_successful_sync_at)

    @patch("apps.jobs.services.ingestion.FranceTravailClient")
    def test_partial_success_updates_job_source_last_sync(self, MockClient):
        mock_client = MockClient.return_value
        mock_client.search_offers.side_effect = [
            _make_ft_result(1),
            Exception("temporary API failure"),
        ]

        run_log = JobIngestionService.run(
            self.config,
            trigger="manual",
            overrides={"custom_keywords": ["python", "django"]},
        )

        self.assertEqual(run_log.status, "partial_success")
        self.source.refresh_from_db()
        self.assertIsNotNone(self.source.last_successful_sync_at)

    def test_repair_france_travail_source_sync_from_successful_runs(self):
        finished = timezone.now() - timedelta(hours=1)
        run = JobIngestionRun.objects.create(
            config=self.config,
            status="success",
            trigger="celery",
            finished_at=finished,
        )

        repaired = JobIngestionService.repair_france_travail_source_sync_from_runs()

        self.assertTrue(repaired)
        self.source.refresh_from_db()
        self.assertEqual(self.source.last_successful_sync_at, run.finished_at)


class ScheduledTriggerDefaultsTest(TestCase):
    """Test that celery trigger uses conservative defaults."""

    def setUp(self):
        self.config = JobIngestionConfig.objects.create(
            name="scheduled_test",
            enabled=True,
            preset="broad_it",
            limit_per_keyword=50,
            max_total_per_run=1000,
            max_pages_per_keyword=10,
            normalize_after_fetch=False,
            enrichment_enabled=False,
            dry_run=False,
        )
        JobSource.objects.get_or_create(
            slug="france_travail",
            defaults={
                "name": "France Travail",
                "base_url": "https://candidat.francetravail.fr/offres/recherche",
                "source_type": SourceType.API,
                "is_active": True,
            },
        )

    @patch("apps.jobs.services.ingestion.FranceTravailClient")
    def test_celery_trigger_uses_scheduled_keywords(self, MockClient):
        """When trigger='celery', should use SCHEDULED_IT_KEYWORDS not full preset."""
        mock_client = MockClient.return_value
        mock_client.search_offers.return_value = _make_ft_result(2)

        run_log = JobIngestionService.run(self.config, trigger="celery")

        # The run should have used the scheduled keywords
        self.assertEqual(run_log.keywords_json, SCHEDULED_IT_KEYWORDS)

    @patch("apps.jobs.services.ingestion.FranceTravailClient")
    def test_manual_trigger_uses_full_preset(self, MockClient):
        """When trigger='manual', should use the full broad_it preset."""
        mock_client = MockClient.return_value
        mock_client.search_offers.return_value = _make_ft_result(2)

        run_log = JobIngestionService.run(
            self.config,
            trigger="manual",
        )

        self.assertEqual(run_log.keywords_json, BROAD_IT_KEYWORDS)

    @patch("apps.jobs.services.ingestion.FranceTravailClient")
    def test_celery_with_custom_keywords_override(self, MockClient):
        """Celery trigger with explicit custom_keywords should use those."""
        mock_client = MockClient.return_value
        mock_client.search_offers.return_value = _make_ft_result(2)

        custom = ["python", "django"]
        run_log = JobIngestionService.run(
            self.config,
            trigger="celery",
            overrides={"custom_keywords": custom},
        )

        self.assertEqual(run_log.keywords_json, custom)
