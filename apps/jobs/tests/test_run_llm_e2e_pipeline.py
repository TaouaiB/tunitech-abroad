from django.test import TestCase
from unittest.mock import patch, call
from django.core.management import call_command
from django.utils import timezone
from apps.jobs.models import JobStatus, NormalizedJob, JobSource, RawJobRecord

class RunLlmE2EPipelineTests(TestCase):
    def setUp(self):
        self.source = JobSource.objects.create(name="Test Source", slug="test-source", source_type="fixture")
        self.raw1 = RawJobRecord.objects.create(
            source=self.source,
            source_job_id="test1",
            first_seen_at=timezone.now(),
            last_seen_at=timezone.now(),
            last_fetched_at=timezone.now(),
            payload_hash="hash1",
            raw_payload_json={}
        )
        self.job1 = NormalizedJob.objects.create(
            source=self.source,
            raw_record=self.raw1,
            source_job_id="test1",
            title="Senior Python Developer",
            description="We need a Python developer.",
            country="FR",
            status=JobStatus.ACTIVE,
            published_at=timezone.now(),
            first_seen_at=timezone.now(),
            last_seen_at=timezone.now(),
            last_fetched_at=timezone.now(),
            classification_json={"confidence": "high", "family": "software"},
            skill_signal_quality="strong",
        )
        
        self.raw2 = RawJobRecord.objects.create(
            source=self.source,
            source_job_id="test2",
            first_seen_at=timezone.now(),
            last_seen_at=timezone.now(),
            last_fetched_at=timezone.now(),
            payload_hash="hash2",
            raw_payload_json={}
        )
        self.job2 = NormalizedJob.objects.create(
            source=self.source,
            raw_record=self.raw2,
            source_job_id="test2",
            title="Junior Java Developer",
            description="We need a Java developer.",
            country="FR",
            status=JobStatus.ACTIVE,
            published_at=timezone.now(),
            first_seen_at=timezone.now(),
            last_seen_at=timezone.now(),
            last_fetched_at=timezone.now(),
            classification_json={"confidence": "high", "family": "software"},
            skill_signal_quality="strong",
        )

    @patch("apps.jobs.management.commands.run_llm_e2e_pipeline.enrich_job")
    @patch("apps.jobs.management.commands.run_llm_e2e_pipeline.call_command")
    def test_e2e_pipeline_command_mocked_provider(self, mock_call_command, mock_enrich_job):
        class MockEnrichment:
            status = "success"
            attempt_count = 1
            total_tokens = 100
            status_reason = "success"
        
        mock_enrich_job.return_value = MockEnrichment()
        
        call_command("run_llm_e2e_pipeline", force_llm_count=2, min_llm_success=2, apply=True)
        
        # Check that enrich_job was called twice with correct flags
        self.assertEqual(mock_enrich_job.call_count, 2)
        mock_enrich_job.assert_has_calls([
            call(self.job2, force=True, force_provider_call=False),
            call(self.job1, force=True, force_provider_call=False)
        ], any_order=True)
        
        # Check that call_command was called for other parts
        self.assertEqual(mock_call_command.call_count, 6)

    @patch("apps.jobs.management.commands.run_llm_e2e_pipeline.enrich_job")
    @patch("apps.jobs.management.commands.run_llm_e2e_pipeline.call_command")
    def test_e2e_pipeline_command_fails_target(self, mock_call_command, mock_enrich_job):
        class MockEnrichment:
            status = "failed"
            attempt_count = 1
            total_tokens = 100
            status_reason = "rate_limited"
        
        mock_enrich_job.return_value = MockEnrichment()
        
        with self.assertRaises(SystemExit) as excinfo:
            call_command("run_llm_e2e_pipeline", force_llm_count=1, min_llm_success=1, apply=True)
            
        self.assertEqual(excinfo.exception.code, 1)
