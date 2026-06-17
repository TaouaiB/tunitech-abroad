from unittest.mock import patch, MagicMock
from django.core.management import call_command
from django.test import TestCase
from io import StringIO
from types import SimpleNamespace
from apps.jobs.models import JobIngestionConfig, JobIngestionRun, RawJobRecord, NormalizedJob, JobStatus, JobSource
from apps.jobs.services.broad_it_preset import get_preset_keywords
from apps.jobs.services.ingestion import JobIngestionService
from apps.jobs.services.expiry import JobExpiryService
from apps.llm.models import JobEnrichment
from django.utils import timezone
from datetime import timedelta
import hashlib

class TestAutomatedITIngestion(TestCase):

    def test_default_config_values(self):
        # 1. default config has enrichment_enabled=True and enrich_every_fetched_it_job=True.
        config = JobIngestionConfig.objects.create(name="test_default")
        self.assertEqual(config.limit_per_keyword, 50)
        self.assertEqual(config.max_total_per_run, 1000)
        self.assertEqual(config.nightly_max_total, 2000)
        self.assertTrue(config.enrichment_enabled)
        self.assertTrue(config.enrich_every_fetched_it_job)

    def test_broad_preset_contains_broad_it_families(self):
        keywords = get_preset_keywords("broad_it")
        self.assertIn("développeur", keywords)
        self.assertIn("data engineer", keywords)

    @patch("apps.jobs.services.france_travail.client.FranceTravailClient.search_offers")
    def test_ingestion_service_deduplication_and_limits(self, mock_search):
        config = JobIngestionConfig.objects.create(
            name="test_dedup",
            limit_per_keyword=2,
            max_total_per_run=3,
            max_pages_per_keyword=1,
            enrichment_enabled=False
        )

        mock_search.return_value = {
            "resultats": [
                {"id": "job1", "intitule": "Job 1", "description": "desc 1", "entreprise": {}},
                {"id": "job2", "intitule": "Job 2", "description": "desc 2", "entreprise": {}}
            ]
        }

        overrides = {
            "custom_keywords": ["kw1", "kw2"],
            "preset": ""
        }

        run_log = JobIngestionService.run(config, trigger="test", overrides=overrides)

        self.assertEqual(run_log.status, "success")
        self.assertEqual(run_log.fetched_count, 2)
        self.assertEqual(run_log.duplicates_skipped_count, 2)
        self.assertEqual(RawJobRecord.objects.count(), 2)
        self.assertEqual(NormalizedJob.objects.count(), 2)

    @patch("apps.jobs.services.ingestion.JobIngestionService.run")
    def test_management_command_respects_limits(self, mock_run):
        mock_run.return_value = SimpleNamespace(
            status="success",
            fetched_count=0,
            created_raw_count=0,
            updated_raw_count=0,
            normalized_count=0,
            duplicates_skipped_count=0,
            enrichment_queued_count=0,
            enrichment_skipped_count=0,
            error_count=0,
            error_summary="",
        )
        call_command(
            'sync_france_travail_it_jobs',
            '--preset',
            'broad_it',
            '--limit-per-keyword',
            '60',
            '--max-total',
            '1200',
            '--enqueue-enrichment',
        )

        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        overrides = kwargs['overrides']

        self.assertEqual(overrides['limit_per_keyword'], 60)
        self.assertEqual(overrides['max_total'], 1200)
        self.assertTrue(overrides['enrichment_enabled'])
        self.assertTrue(overrides['enrich_every_fetched_it_job'])

    @patch("apps.jobs.services.ingestion.JobIngestionService.run")
    def test_management_command_outputs_run_counters(self, mock_run):
        mock_run.return_value = SimpleNamespace(
            status="success",
            fetched_count=6,
            created_raw_count=1,
            updated_raw_count=5,
            normalized_count=6,
            duplicates_skipped_count=2,
            enrichment_queued_count=3,
            enrichment_skipped_count=3,
            error_count=0,
            error_summary="",
        )
        stdout = StringIO()

        call_command('sync_france_travail_it_jobs', stdout=stdout)
        output = stdout.getvalue()

        self.assertIn("Fetched: 6", output)
        self.assertIn("Created raw: 1", output)
        self.assertIn("Updated raw: 5", output)
        self.assertIn("Normalized: 6", output)
        self.assertIn("Duplicates skipped: 2", output)
        self.assertIn("Enrichment queued: 3", output)
        self.assertIn("Enrichment skipped: 3", output)
        self.assertIn("Errors: 0", output)

    def test_expiry_service(self):
        source = JobSource.objects.create(name="test", slug="test")
        now = timezone.now()

        raw_job = RawJobRecord.objects.create(
            source=source, source_job_id="stale_job", raw_payload_json={},
            first_seen_at=now, last_seen_at=now, last_fetched_at=now
        )
        norm_job = NormalizedJob.objects.create(
            source=source, raw_record=raw_job, title="Stale Job", status=JobStatus.ACTIVE,
            first_seen_at=now, last_seen_at=now - timedelta(days=25), last_fetched_at=now
        )

        expired_count = JobExpiryService.mark_stale_jobs(21)
        self.assertEqual(expired_count, 1)

        norm_job.refresh_from_db()
        self.assertEqual(norm_job.status, JobStatus.STALE)

    @patch("apps.jobs.services.france_travail.client.FranceTravailClient.search_offers")
    @patch("apps.jobs.services.ingestion.enrich_job_task.delay")
    @patch("apps.jobs.services.ingestion.job_qualifies_for_enrichment_with_reason")
    def test_enrichment_queues_and_skips(self, mock_qualify, mock_enrich_task, mock_search):
        # We test:
        # 2. queues enrichment for updated existing jobs
        # 3. existing successful same hash is skipped and counted.
        # 4. pending duplicate is skipped and counted.
        # 5. run counters match command output.

        config = JobIngestionConfig.objects.create(
            name="test_enrich",
            limit_per_keyword=5,
            max_total_per_run=5,
            enrichment_enabled=True,
            enrich_every_fetched_it_job=True,
            preset=""
        )

        # Prepare 3 jobs in search response
        mock_search.return_value = {
            "resultats": [
                {"id": "job_new", "intitule": "New Job", "description": "desc"},
                {"id": "job_success", "intitule": "Success Job", "description": "desc"},
                {"id": "job_pending", "intitule": "Pending Job", "description": "desc"}
            ]
        }

        # Make them all qualify
        mock_qualify.return_value = (True, "")

        # Create the source
        source = JobSource.objects.create(name="FT", slug="france_travail", source_type="api")
        now = timezone.now()

        # Job 2: Existing successful
        raw_success = RawJobRecord.objects.create(
            source=source, source_job_id="job_success", raw_payload_json={},
            payload_hash="old", first_seen_at=now, last_seen_at=now, last_fetched_at=now
        )
        norm_success = NormalizedJob.objects.create(
            source=source, raw_record=raw_success, source_job_id="job_success", title="Success Job", description="desc",
            first_seen_at=now, last_seen_at=now, last_fetched_at=now
        )
        hash_success = hashlib.md5("Success Job\ndesc".encode()).hexdigest()
        JobEnrichment.objects.create(job=norm_success, status=JobEnrichment.Status.SUCCESS, payload_hash=hash_success)

        # Job 3: Existing pending
        raw_pending = RawJobRecord.objects.create(
            source=source, source_job_id="job_pending", raw_payload_json={},
            payload_hash="old", first_seen_at=now, last_seen_at=now, last_fetched_at=now
        )
        norm_pending = NormalizedJob.objects.create(
            source=source, raw_record=raw_pending, source_job_id="job_pending", title="Pending Job", description="desc",
            first_seen_at=now, last_seen_at=now, last_fetched_at=now
        )
        hash_pending = hashlib.md5("Pending Job\ndesc".encode()).hexdigest()
        JobEnrichment.objects.create(job=norm_pending, status=JobEnrichment.Status.PENDING, payload_hash=hash_pending)

        overrides = {"custom_keywords": ["python"], "preset": ""}
        run_log = JobIngestionService.run(config, trigger="test", overrides=overrides)

        self.assertEqual(run_log.fetched_count, 3)
        self.assertEqual(run_log.created_raw_count, 1) # job_new
        self.assertEqual(run_log.updated_raw_count, 2) # job_success, job_pending
        self.assertEqual(run_log.normalized_count, 3)

        # Enrichment queued should be 1 (job_new), skipped should be 2
        self.assertEqual(run_log.enrichment_queued_count, 1)
        self.assertEqual(run_log.enrichment_skipped_count, 2)

        # Verify it queued for the new one (proving #2 since updated jobs like pending/success were evaluated and skipped, not ignored)
        mock_enrich_task.assert_called_once()
        args, kwargs = mock_enrich_task.call_args

        new_job = NormalizedJob.objects.get(source_job_id="job_new")
        self.assertEqual(args[0], new_job.id)

    @patch("apps.jobs.services.france_travail.client.FranceTravailClient.search_offers")
    @patch("apps.jobs.services.ingestion.enrich_job_task.delay")
    @patch("apps.jobs.services.ingestion.job_qualifies_for_enrichment_with_reason")
    def test_enrichment_queues_updated_existing_job_without_prior_enrichment(
        self,
        mock_qualify,
        mock_enrich_task,
        mock_search,
    ):
        config = JobIngestionConfig.objects.create(
            name="test_updated_queue",
            limit_per_keyword=1,
            max_total_per_run=1,
            enrichment_enabled=True,
            enrich_every_fetched_it_job=True,
            preset="",
        )
        source = JobSource.objects.create(name="FT", slug="france_travail", source_type="api")
        now = timezone.now()
        raw = RawJobRecord.objects.create(
            source=source,
            source_job_id="job_existing",
            raw_payload_json={"id": "job_existing", "intitule": "Python Dev", "description": "old"},
            payload_hash="old",
            first_seen_at=now,
            last_seen_at=now,
            last_fetched_at=now,
        )
        NormalizedJob.objects.create(
            source=source,
            raw_record=raw,
            source_job_id="job_existing",
            title="Python Dev",
            description="old",
            first_seen_at=now,
            last_seen_at=now,
            last_fetched_at=now,
            classification_json={"confidence": "high", "is_it": True},
        )
        mock_search.return_value = {
            "resultats": [
                {"id": "job_existing", "intitule": "Python Dev Updated", "description": "new Django role"}
            ]
        }
        mock_qualify.return_value = (True, "")

        run_log = JobIngestionService.run(
            config,
            trigger="test",
            overrides={"custom_keywords": ["python"], "preset": "", "enrichment_enabled": True},
        )

        self.assertEqual(run_log.fetched_count, 1)
        self.assertEqual(run_log.updated_raw_count, 1)
        self.assertEqual(run_log.normalized_count, 1)
        self.assertEqual(run_log.enrichment_queued_count, 1)
        self.assertEqual(run_log.enrichment_skipped_count, 0)
        updated_job = NormalizedJob.objects.get(source_job_id="job_existing")
        mock_enrich_task.assert_called_once_with(updated_job.id)

    @patch("apps.jobs.services.france_travail.client.FranceTravailClient.search_offers")
    def test_no_hidden_min_limit_cap(self, mock_search):
        # 6. no hidden min(limit, 10) cap exists
        config = JobIngestionConfig.objects.create(
            name="test_no_cap",
            limit_per_keyword=20,
            max_total_per_run=20,
            enrichment_enabled=False
        )

        # Return 20 jobs
        jobs = [{"id": f"job{i}", "intitule": f"Job {i}", "description": "desc"} for i in range(20)]
        mock_search.return_value = {"resultats": jobs}

        run_log = JobIngestionService.run(config, trigger="test", overrides={"custom_keywords": ["python"], "preset": ""})

        self.assertEqual(run_log.fetched_count, 20)

    def test_daily_limit_default_is_1000(self):
        config = JobIngestionConfig.objects.create(name="test_daily_limit_default")
        self.assertEqual(config.daily_enrichment_limit, 1000)

    @patch("apps.jobs.services.france_travail.client.FranceTravailClient.search_offers")
    @patch("apps.jobs.services.ingestion.enrich_job_task.delay")
    @patch("apps.jobs.services.normalization.JobNormalizationService.normalize")
    def test_daily_limit_allows_20_job_sync(self, mock_normalize, mock_enrich_task, mock_search):
        config = JobIngestionConfig.objects.create(
            name="test_daily_limit_20",
            limit_per_keyword=20,
            max_total_per_run=20,
            enrichment_enabled=True,
            enrich_every_fetched_it_job=True,
            daily_enrichment_limit=1000
        )
        jobs = [{"id": f"job{i}", "intitule": f"Job {i}", "description": "desc"} for i in range(20)]
        mock_search.return_value = {"resultats": jobs}

        def fake_normalize(raw_record):
            now = timezone.now()
            norm = NormalizedJob.objects.create(
                source=raw_record.source,
                raw_record=raw_record,
                source_job_id=raw_record.source_job_id,
                title=raw_record.raw_payload_json.get("intitule", ""),
                first_seen_at=now, last_seen_at=now, last_fetched_at=now,
                status=JobStatus.ACTIVE, country="FR",
                classification_json={"confidence": "high"}
            )
            return norm
        mock_normalize.side_effect = fake_normalize

        run_log = JobIngestionService.run(config, trigger="test", overrides={"custom_keywords": ["python"], "preset": ""})

        self.assertEqual(run_log.fetched_count, 20)
        self.assertEqual(run_log.enrichment_queued_count, 20)
        self.assertEqual(mock_enrich_task.call_count, 20)

    @patch("apps.jobs.services.france_travail.client.FranceTravailClient.search_offers")
    @patch("apps.jobs.services.ingestion.enrich_job_task.delay")
    @patch("apps.jobs.services.normalization.JobNormalizationService.normalize")
    def test_skipped_rows_do_not_consume_daily_limit(self, mock_normalize, mock_enrich_task, mock_search):
        config = JobIngestionConfig.objects.create(
            name="test_daily_limit_skipped",
            limit_per_keyword=5,
            max_total_per_run=5,
            enrichment_enabled=True,
            enrich_every_fetched_it_job=True,
            daily_enrichment_limit=2
        )
        source = JobSource.objects.create(name="FT", slug="france_travail", source_type="api")
        now = timezone.now()

        # Create 10 skipped enrichments today
        for i in range(10):
            raw = RawJobRecord.objects.create(
                source=source, source_job_id=f"skipped_{i}", raw_payload_json={},
                payload_hash=f"hash_{i}", first_seen_at=now, last_seen_at=now, last_fetched_at=now
            )
            norm = NormalizedJob.objects.create(
                source=source, raw_record=raw, source_job_id=f"skipped_{i}", title=f"Skipped {i}",
                first_seen_at=now, last_seen_at=now, last_fetched_at=now, status=JobStatus.ACTIVE, country="FR",
                classification_json={"confidence": "high"}
            )
            JobEnrichment.objects.create(job=norm, status=JobEnrichment.Status.SKIPPED, payload_hash=f"hash_{i}")

        jobs = [{"id": f"job_new_{i}", "intitule": f"Job New {i}", "description": "desc"} for i in range(3)]
        mock_search.return_value = {"resultats": jobs}

        def fake_normalize(raw_record):
            now = timezone.now()
            norm = NormalizedJob.objects.create(
                source=raw_record.source,
                raw_record=raw_record,
                source_job_id=raw_record.source_job_id,
                title=raw_record.raw_payload_json.get("intitule", ""),
                first_seen_at=now, last_seen_at=now, last_fetched_at=now,
                status=JobStatus.ACTIVE, country="FR",
                classification_json={"confidence": "high"}
            )
            return norm
        mock_normalize.side_effect = fake_normalize

        run_log = JobIngestionService.run(config, trigger="test", overrides={"custom_keywords": ["python"], "preset": ""})

        # Daily limit is 2. 10 skipped rows do not count, but queued rows are
        # reserved as PENDING during this run.
        self.assertEqual(run_log.fetched_count, 3)
        self.assertEqual(run_log.enrichment_queued_count, 2)
        self.assertEqual(run_log.enrichment_skipped_count, 1)

    @patch("apps.jobs.services.france_travail.client.FranceTravailClient.search_offers")
    @patch("apps.jobs.services.ingestion.enrich_job_task.delay")
    @patch("apps.jobs.services.normalization.JobNormalizationService.normalize")
    def test_daily_limit_blocks_after_actual_attempted_reach_limit(self, mock_normalize, mock_enrich_task, mock_search):
        config = JobIngestionConfig.objects.create(
            name="test_daily_limit_blocks",
            limit_per_keyword=5,
            max_total_per_run=5,
            enrichment_enabled=True,
            enrich_every_fetched_it_job=True,
            daily_enrichment_limit=2
        )
        source = JobSource.objects.create(name="FT", slug="france_travail", source_type="api")
        now = timezone.now()

        # Create 2 SUCCESS enrichments today (reaches limit)
        for i in range(2):
            raw = RawJobRecord.objects.create(
                source=source, source_job_id=f"success_{i}", raw_payload_json={},
                payload_hash=f"shash_{i}", first_seen_at=now, last_seen_at=now, last_fetched_at=now
            )
            norm = NormalizedJob.objects.create(
                source=source, raw_record=raw, source_job_id=f"success_{i}", title=f"Success {i}",
                first_seen_at=now, last_seen_at=now, last_fetched_at=now, status=JobStatus.ACTIVE, country="FR",
                classification_json={"confidence": "high"}
            )
            JobEnrichment.objects.create(job=norm, status=JobEnrichment.Status.SUCCESS, payload_hash=f"shash_{i}")

        jobs = [{"id": f"job_new_{i}", "intitule": f"Job New {i}", "description": "desc"} for i in range(2)]
        mock_search.return_value = {"resultats": jobs}

        def fake_normalize(raw_record):
            now = timezone.now()
            norm = NormalizedJob.objects.create(
                source=raw_record.source,
                raw_record=raw_record,
                source_job_id=raw_record.source_job_id,
                title=raw_record.raw_payload_json.get("intitule", ""),
                first_seen_at=now, last_seen_at=now, last_fetched_at=now,
                status=JobStatus.ACTIVE, country="FR",
                classification_json={"confidence": "high"}
            )
            return norm
        mock_normalize.side_effect = fake_normalize

        run_log = JobIngestionService.run(config, trigger="test", overrides={"custom_keywords": ["python"], "preset": ""})

        # Daily limit is 2. 2 success exist. So 0 should be queued, 2 skipped.
        self.assertEqual(run_log.fetched_count, 2)
        self.assertEqual(run_log.enrichment_queued_count, 0)
        self.assertEqual(run_log.enrichment_skipped_count, 2)
