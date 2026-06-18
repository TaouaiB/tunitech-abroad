from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.utils import timezone
from apps.jobs.models import JobIngestionConfig, JobIngestionRun, RawJobRecord, JobSource, SourceType
from apps.jobs.services.ingestion import JobIngestionService
from django.db import IntegrityError

class IngestionIdempotencyTests(TestCase):
    def setUp(self):
        self.ingestion_config = JobIngestionConfig.objects.create(name="test_config", max_total_per_run=10)
        self.ft_source = JobSource.objects.create(
            name="France Travail", slug="france_travail", source_type=SourceType.API
        )

    def test_ingestion_idempotency_duplicate_in_same_run(self):
        # Mock the API client to return the same job ID multiple times
        mock_client = MagicMock()
        mock_client.search_offers.return_value = {
            "resultats": [
                {"id": "DUP123", "title": "Job A"},
                {"id": "DUP123", "title": "Job A"},
                {"id": "DUP123", "title": "Job A"}
            ]
        }
        
        with patch("apps.jobs.services.ingestion.FranceTravailClient", return_value=mock_client):
            run_log = JobIngestionService.run(self.ingestion_config, trigger="manual", overrides={"custom_keywords": ["python"], "limit_per_keyword": 5})
            
        self.assertIn(run_log.status, ["success", "partial_success"])
        self.assertEqual(RawJobRecord.objects.filter(source_job_id="DUP123").count(), 1)
        self.assertEqual(run_log.duplicates_skipped_count, 2)
        self.assertEqual(run_log.created_raw_count, 1)
        
    def test_ingestion_concurrent_creation_protection(self):
        job_data = {"id": "RACE123", "title": "Job B"}

        get_call_count = [0]
        original_get = RawJobRecord.objects.get
        original_create = RawJobRecord.objects.create

        def get_side_effect(*args, **kwargs):
            if get_call_count[0] == 0:
                get_call_count[0] += 1
                raise RawJobRecord.DoesNotExist
            if not RawJobRecord.objects.filter(source=self.ft_source, source_job_id="RACE123").exists():
                original_create(
                    source=self.ft_source,
                    source_job_id="RACE123",
                    raw_payload_json={"concurrent": True},
                    payload_hash="concurrent-hash",
                    first_seen_at=timezone.now(),
                    last_seen_at=timezone.now(),
                    last_fetched_at=timezone.now(),
                )
            return original_get(*args, **kwargs)

        def create_side_effect(*args, **kwargs):
            raise IntegrityError("duplicate key value violates unique constraint")

        run_log = JobIngestionRun.objects.create(config=self.ingestion_config, trigger="test")

        with patch('apps.jobs.models.RawJobRecord.objects.get', side_effect=get_side_effect), \
             patch('apps.jobs.models.RawJobRecord.objects.create', side_effect=create_side_effect):
            JobIngestionService._process_job(
                job_data=job_data,
                job_id="RACE123",
                source=self.ft_source,
                run_log=run_log,
                normalize=False,
                enrichment_enabled=False,
                enrich_every_fetched_it_job=False,
                sync_enrichment=False,
                config=self.ingestion_config
            )
            
        self.assertEqual(RawJobRecord.objects.filter(source_job_id="RACE123").count(), 1)
        job = RawJobRecord.objects.get(source_job_id="RACE123")
        self.assertEqual(job.raw_payload_json, job_data)
        self.assertEqual(run_log.updated_raw_count, 1)
        self.assertEqual(get_call_count[0], 1)
