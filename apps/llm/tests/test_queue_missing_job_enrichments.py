import uuid
from unittest.mock import patch
from io import StringIO
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.jobs.models import (
    JobSource, SourceType, RawJobRecord, NormalizedJob, JobStatus,
    NormalizationStatus, RemoteType, JobType, ExperienceLevel
)
from apps.llm.models import JobEnrichment

class QueueMissingJobEnrichmentsTest(TestCase):
    def setUp(self):
        self.source = JobSource.objects.create(
            name="France Travail",
            slug="france_travail",
            source_type=SourceType.API,
            is_active=True
        )

    def _create_job(self, status=JobStatus.ACTIVE, country="FR", confidence="high", quality="strong", with_enrichment=False):
        now = timezone.now()
        raw = RawJobRecord.objects.create(
            source=self.source,
            source_job_id=f"TEST-{uuid.uuid4().hex[:8]}",
            normalization_status=NormalizationStatus.SUCCESS,
            payload_hash=f"hash-{uuid.uuid4().hex[:8]}",
            raw_payload_json={"test": "data"},
            first_seen_at=now,
            last_seen_at=now,
            last_fetched_at=now,
        )
        job = NormalizedJob.objects.create(
            source=self.source,
            raw_record=raw,
            source_job_id=raw.source_job_id,
            title="Test Job",
            description="Test Description",
            remote_type=RemoteType.UNKNOWN,
            job_type=JobType.FULL_TIME_JOB,
            experience_level=ExperienceLevel.JUNIOR,
            country=country,
            status=status,
            classification_json={"confidence": confidence},
            first_seen_at=now,
            last_seen_at=now,
            last_fetched_at=now,
        )
        NormalizedJob.objects.filter(id=job.id).update(skill_signal_quality=quality)
        job.refresh_from_db()
        
        if with_enrichment:
            JobEnrichment.objects.create(
                job=job,
                status=JobEnrichment.Status.SUCCESS,
                payload_hash="some-hash",
            )
        return job

    @patch("apps.llm.management.commands.queue_missing_job_enrichments.queue_selected_eligible_enrichments")
    @override_settings(JOB_ENRICHMENT_ENABLED=True, JOB_ENRICHMENT_MIN_RELEVANCE="partial")
    def test_queue_missing_job_enrichments(self, mock_queue):
        mock_queue.return_value = 1
        
        # 1. Eligible job
        j1 = self._create_job(status=JobStatus.ACTIVE, country="FR", confidence="high", quality="strong")
        
        # 2. Ineligible (bad country)
        j2 = self._create_job(status=JobStatus.ACTIVE, country="US", confidence="high", quality="strong")
        
        # 3. Ineligible (low confidence)
        j3 = self._create_job(status=JobStatus.ACTIVE, country="FR", confidence="low", quality="strong")
        
        # 4. Ineligible (low quality, not in 'strong', 'partial')
        j4 = self._create_job(status=JobStatus.ACTIVE, country="FR", confidence="high", quality="missing")
        
        # 5. Already enriched
        j5 = self._create_job(status=JobStatus.ACTIVE, country="FR", confidence="high", quality="strong", with_enrichment=True)

        out = StringIO()
        call_command("queue_missing_job_enrichments", stdout=out)

        mock_queue.assert_called_once()
        kwargs = mock_queue.call_args[1]
        self.assertEqual(kwargs["job_ids"], [j1.id])
        self.assertEqual(kwargs["limit"], 10)
        
        out_text = out.getvalue()
        self.assertIn("eligible: 1", out_text)
        self.assertIn("skipped_low_relevance: 2", out_text)
        self.assertIn("queued: 1", out_text)

    @patch("apps.llm.management.commands.queue_missing_job_enrichments.queue_selected_eligible_enrichments")
    @override_settings(JOB_ENRICHMENT_ENABLED=True, JOB_ENRICHMENT_MIN_RELEVANCE="partial")
    def test_queue_dry_run(self, mock_queue):
        j1 = self._create_job(status=JobStatus.ACTIVE, country="FR", confidence="high", quality="strong")
        
        out = StringIO()
        call_command("queue_missing_job_enrichments", "--dry-run", stdout=out)
        
        mock_queue.assert_not_called()
        self.assertIn("[DRY-RUN]", out.getvalue())
        self.assertIn("eligible: 1", out.getvalue())
        self.assertIn("queued: 0", out.getvalue())

    @patch("apps.llm.management.commands.queue_missing_job_enrichments.queue_selected_eligible_enrichments")
    @override_settings(
        JOB_ENRICHMENT_ENABLED=True,
        JOB_ENRICHMENT_MIN_RELEVANCE="partial",
        JOB_ENRICHMENT_RETRY_MAX_PER_RUN=2,
    )
    def test_queue_caps_limit_by_retry_max_per_run(self, mock_queue):
        mock_queue.return_value = 2
        jobs = [
            self._create_job(status=JobStatus.ACTIVE, country="FR", confidence="high", quality="strong")
            for _ in range(4)
        ]

        out = StringIO()
        call_command("queue_missing_job_enrichments", "--limit", "10", stdout=out)

        kwargs = mock_queue.call_args[1]
        self.assertEqual(kwargs["job_ids"], [jobs[0].id, jobs[1].id])
        self.assertEqual(kwargs["limit"], 2)
        self.assertIn("eligible: 4", out.getvalue())

    @patch("apps.llm.management.commands.queue_missing_job_enrichments.queue_selected_eligible_enrichments")
    @override_settings(JOB_ENRICHMENT_ENABLED=False)
    def test_queue_respects_disabled_flag(self, mock_queue):
        self._create_job(status=JobStatus.ACTIVE, country="FR", confidence="high", quality="strong")

        out = StringIO()
        call_command("queue_missing_job_enrichments", stdout=out)

        mock_queue.assert_not_called()
        self.assertIn("JOB_ENRICHMENT_ENABLED is False", out.getvalue())
        self.assertIn("eligible: 0", out.getvalue())
        self.assertIn("skipped_low_relevance: 0", out.getvalue())
        self.assertIn("queued: 0", out.getvalue())

    @patch("apps.llm.management.commands.queue_missing_job_enrichments.queue_selected_eligible_enrichments")
    @override_settings(JOB_ENRICHMENT_ENABLED=True, JOB_ENRICHMENT_MIN_RELEVANCE="partial")
    def test_queue_does_not_queue_provider_blocked_rows(self, mock_queue):
        blocked = self._create_job(status=JobStatus.ACTIVE, country="FR", confidence="high", quality="strong")
        JobEnrichment.objects.create(
            job=blocked,
            status=JobEnrichment.Status.FAILED,
            status_reason="forbidden/provider_blocked",
            last_error="HTTP Error 403: Forbidden",
            payload_hash="blocked-hash",
        )

        out = StringIO()
        call_command("queue_missing_job_enrichments", stdout=out)

        mock_queue.assert_not_called()
        self.assertIn("eligible: 0", out.getvalue())
        self.assertIn("queued: 0", out.getvalue())
