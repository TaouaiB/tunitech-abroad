from unittest.mock import patch
from django.test import TestCase, override_settings
from django.utils import timezone
from apps.jobs.models import (
    JobIngestionConfig,
    JobIngestionRun,
    JobSource,
    SourceType,
    RawJobRecord,
    NormalizedJob,
    RemoteType,
    JobType,
    ExperienceLevel
)
from apps.llm.models import JobEnrichment
from apps.jobs.services.ingestion import JobIngestionService

@override_settings(JOB_ENRICHMENT_MAX_PER_INGESTION_RUN=1000)
class BudgetControlsTests(TestCase):
    def setUp(self):
        self.config = JobIngestionConfig.objects.create(
            name="test_config",
            enrichment_limit_per_run=100  # High default config limit
        )
        self.source = JobSource.objects.create(
            name="FT", slug="france_travail", source_type=SourceType.API
        )

    @override_settings(JOB_ENRICHMENT_MAX_PER_INGESTION_RUN=2, JOB_ENRICHMENT_ENABLED=True)
    def test_enrichment_run_hard_cap(self):
        # We process 5 jobs, but only 2 should get enriched due to the hard cap
        run_log = JobIngestionRun.objects.create(config=self.config, trigger="test")
        
        with patch('apps.jobs.services.ingestion.enrich_job_task.delay') as mock_delay:
            for i in range(5):
                job_id = f"JOB{i}"
                job_data = {"id": job_id, "title": f"Test {i}"}
                
                raw = RawJobRecord.objects.create(
                    source=self.source,
                    source_job_id=job_id,
                    raw_payload_json=job_data,
                    payload_hash=f"hash{i}",
                    first_seen_at=timezone.now(),
                    last_seen_at=timezone.now(),
                    last_fetched_at=timezone.now()
                )
                
                # Mock JobNormalizationService to return a dummy job
                with patch('apps.jobs.services.normalization.JobNormalizationService.normalize') as mock_norm:
                    norm_job = NormalizedJob.objects.create(
                        source=self.source,
                        raw_record=raw,
                        source_job_id=job_id,
                        title=f"Test {i}",
                        description="IT job",
                        remote_type=RemoteType.UNKNOWN,
                        job_type=JobType.UNKNOWN,
                        experience_level=ExperienceLevel.UNKNOWN,
                        first_seen_at=timezone.now(),
                        last_seen_at=timezone.now(),
                        last_fetched_at=timezone.now(),
                        skill_signal_quality="strong",
                        classification_json={"confidence": "high"}
                    )
                    mock_norm.return_value = norm_job
                    
                    JobIngestionService._process_job(
                        job_data=job_data,
                        job_id=job_id,
                        source=self.source,
                        run_log=run_log,
                        normalize=True,
                        enrichment_enabled=True,
                        enrich_every_fetched_it_job=True,
                        sync_enrichment=False,
                        config=self.config
                    )
            
            # Since the setting is 2, it should only queue 2 enrichments
            self.assertEqual(mock_delay.call_count, 2)
            self.assertEqual(run_log.enrichment_queued_count, 2)
            self.assertEqual(run_log.enrichment_skipped_count, 3)
            self.assertEqual(run_log.error_count, 0)
            self.assertEqual(run_log.error_summary, "")

    @override_settings(JOB_ENRICHMENT_MIN_RELEVANCE="strong", JOB_ENRICHMENT_ENABLED=True)
    def test_enrichment_relevance_filter(self):
        run_log = JobIngestionRun.objects.create(config=self.config, trigger="test")
        
        with patch('apps.jobs.services.ingestion.enrich_job_task.delay') as mock_delay:
            # Job 1: Strong (should queue)
            raw1 = RawJobRecord.objects.create(
                source=self.source, source_job_id="J1", raw_payload_json={},
                payload_hash="h1", first_seen_at=timezone.now(), last_seen_at=timezone.now(),
                last_fetched_at=timezone.now()
            )
            norm1 = NormalizedJob.objects.create(
                source=self.source, raw_record=raw1, source_job_id="J1", title="J1",
                description="desc", remote_type=RemoteType.UNKNOWN, job_type=JobType.UNKNOWN,
                experience_level=ExperienceLevel.UNKNOWN, first_seen_at=timezone.now(),
                last_seen_at=timezone.now(), last_fetched_at=timezone.now(),
                skill_signal_quality="strong", classification_json={"confidence": "high"}
            )
            
            # Job 2: Partial (should skip)
            raw2 = RawJobRecord.objects.create(
                source=self.source, source_job_id="J2", raw_payload_json={},
                payload_hash="h2", first_seen_at=timezone.now(), last_seen_at=timezone.now(),
                last_fetched_at=timezone.now()
            )
            norm2 = NormalizedJob.objects.create(
                source=self.source, raw_record=raw2, source_job_id="J2", title="J2",
                description="desc", remote_type=RemoteType.UNKNOWN, job_type=JobType.UNKNOWN,
                experience_level=ExperienceLevel.UNKNOWN, first_seen_at=timezone.now(),
                last_seen_at=timezone.now(), last_fetched_at=timezone.now(),
                skill_signal_quality="partial", classification_json={"confidence": "high"}
            )

            # Job 3: Missing (should skip)
            raw3 = RawJobRecord.objects.create(
                source=self.source, source_job_id="J3", raw_payload_json={},
                payload_hash="h3", first_seen_at=timezone.now(), last_seen_at=timezone.now(),
                last_fetched_at=timezone.now()
            )
            norm3 = NormalizedJob.objects.create(
                source=self.source, raw_record=raw3, source_job_id="J3", title="J3",
                description="desc", remote_type=RemoteType.UNKNOWN, job_type=JobType.UNKNOWN,
                experience_level=ExperienceLevel.UNKNOWN, first_seen_at=timezone.now(),
                last_seen_at=timezone.now(), last_fetched_at=timezone.now(),
                skill_signal_quality="missing", classification_json={"confidence": "high"}
            )

            JobIngestionService._queue_enrichment(norm1, run_log, False, self.config)
            JobIngestionService._queue_enrichment(norm2, run_log, False, self.config)
            JobIngestionService._queue_enrichment(norm3, run_log, False, self.config)

            self.assertEqual(mock_delay.call_count, 1)
            self.assertEqual(run_log.enrichment_queued_count, 1)
            self.assertEqual(run_log.enrichment_skipped_count, 2)
            self.assertEqual(run_log.error_count, 0)
            self.assertEqual(run_log.error_summary, "")
