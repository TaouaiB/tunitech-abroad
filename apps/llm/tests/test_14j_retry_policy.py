from datetime import timedelta
from unittest.mock import Mock, patch

from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory, TestCase, override_settings
from django.utils import timezone

from apps.jobs.models import (
    ExperienceLevel,
    JobSource,
    JobStatus,
    JobType,
    NormalizedJob,
    RawJobRecord,
    RemoteType,
    SourceType,
)
from apps.jobs.admin import NormalizedJobAdmin, queue_selected_eligible_job_enrichments
from apps.llm.admin import JobEnrichmentAdmin, queue_selected_eligible_enrichments_action
from apps.llm.models import JobEnrichment
from apps.llm.services.job_enrichment import (
    is_enrichment_retry_eligible,
    queue_selected_eligible_enrichments,
)


def create_job(source_job_id="JOB-1", *, skill_signal_quality="strong"):
    now = timezone.now()
    source, _ = JobSource.objects.get_or_create(
        slug="france_travail",
        defaults={"name": "France Travail", "source_type": SourceType.API},
    )
    raw = RawJobRecord.objects.create(
        source=source,
        source_job_id=source_job_id,
        raw_payload_json={},
        payload_hash=f"raw-{source_job_id}",
        first_seen_at=now,
        last_seen_at=now,
        last_fetched_at=now,
    )
    return NormalizedJob.objects.create(
        source=source,
        raw_record=raw,
        source_job_id=source_job_id,
        title=f"Python Developer {source_job_id}",
        description="Build Django APIs with Python and PostgreSQL.",
        remote_type=RemoteType.HYBRID,
        job_type=JobType.FULL_TIME_JOB,
        experience_level=ExperienceLevel.JUNIOR,
        country="FR",
        status=JobStatus.ACTIVE,
        first_seen_at=now,
        last_seen_at=now,
        last_fetched_at=now,
        skill_signal_quality=skill_signal_quality,
        classification_json={"confidence": "high"},
    )


class EnrichmentRetryPolicyTests(TestCase):
    def test_retry_eligibility_categories(self):
        old = timezone.now() - timedelta(hours=2)
        stale_pending = JobEnrichment.objects.create(
            job=create_job("PENDING"),
            status=JobEnrichment.Status.PENDING,
            payload_hash="h1",
        )
        JobEnrichment.objects.filter(id=stale_pending.id).update(updated_at=old, created_at=old)
        stale_pending.refresh_from_db()
        self.assertTrue(is_enrichment_retry_eligible(stale_pending)[0])

        rate_limited = JobEnrichment.objects.create(
            job=create_job("RATE"),
            status=JobEnrichment.Status.FAILED,
            status_reason="rate_limited",
            last_error="HTTP Error 429: Rate limited",
            payload_hash="h2",
            completed_at=old,
        )
        self.assertTrue(is_enrichment_retry_eligible(rate_limited)[0])

        skipped_budget = JobEnrichment.objects.create(
            job=create_job("BUDGET"),
            status=JobEnrichment.Status.SKIPPED,
            status_reason="Daily enrichment limit reached",
            payload_hash="h3",
        )
        self.assertTrue(is_enrichment_retry_eligible(skipped_budget)[0])

        forbidden = JobEnrichment.objects.create(
            job=create_job("FORBID"),
            status=JobEnrichment.Status.FAILED,
            status_reason="forbidden/provider_blocked",
            last_error="HTTP Error 403: Forbidden",
            payload_hash="h4",
            completed_at=old,
        )
        self.assertFalse(is_enrichment_retry_eligible(forbidden)[0])

        key_daily_limit = JobEnrichment.objects.create(
            job=create_job("KEY-LIMIT"),
            status=JobEnrichment.Status.FAILED,
            status_reason="key_daily_limit_exceeded",
            last_error="HTTP Error 403: key_daily_limit_exceeded",
            payload_hash="h6",
            completed_at=old,
        )
        eligible, reason = is_enrichment_retry_eligible(key_daily_limit)
        self.assertFalse(eligible)
        self.assertEqual(reason, "key_daily_limit_exceeded")

        validation_error = JobEnrichment.objects.create(
            job=create_job("VALID"),
            status=JobEnrichment.Status.VALIDATION_ERROR,
            status_reason="validation_error",
            payload_hash="h5",
            completed_at=old,
        )
        self.assertFalse(is_enrichment_retry_eligible(validation_error)[0])

    @override_settings(
        JOB_ENRICHMENT_ENABLED=True,
        JOB_ENRICHMENT_RETRY_MAX_PER_RUN=10,
        JOB_ENRICHMENT_RETRY_COOLDOWN_MINUTES=60,
        JOB_ENRICHMENT_DAILY_LIMIT=100,
    )
    @patch("apps.llm.tasks.enrich_job_task.delay")
    def test_queue_selected_enqueues_only_eligible_records(self, mock_delay):
        old = timezone.now() - timedelta(hours=2)
        eligible = JobEnrichment.objects.create(
            job=create_job("ELIGIBLE"),
            status=JobEnrichment.Status.FAILED,
            status_reason="provider_error",
            last_error="Temporary upstream issue",
            payload_hash="h1",
            completed_at=old,
        )
        forbidden = JobEnrichment.objects.create(
            job=create_job("BLOCKED"),
            status=JobEnrichment.Status.FAILED,
            status_reason="forbidden/provider_blocked",
            last_error="HTTP Error 403: Forbidden",
            payload_hash="h2",
            completed_at=old,
        )
        key_daily_limit = JobEnrichment.objects.create(
            job=create_job("KEY-LIMIT-BLOCKED"),
            status=JobEnrichment.Status.FAILED,
            status_reason="key_daily_limit_exceeded",
            last_error="HTTP Error 403: key_daily_limit_exceeded",
            payload_hash="h3",
            completed_at=old,
        )

        queued = queue_selected_eligible_enrichments(enrichment_ids=[eligible.id, forbidden.id, key_daily_limit.id])

        self.assertEqual(queued, 1)
        mock_delay.assert_called_once_with(eligible.job_id)
        eligible.refresh_from_db()
        self.assertEqual(eligible.status, JobEnrichment.Status.PENDING)


class EnrichmentAdminActionTests(TestCase):
    @override_settings(
        JOB_ENRICHMENT_ENABLED=True,
        JOB_ENRICHMENT_RETRY_MAX_PER_RUN=10,
        JOB_ENRICHMENT_RETRY_COOLDOWN_MINUTES=60,
        JOB_ENRICHMENT_DAILY_LIMIT=100,
    )
    @patch("apps.llm.tasks.enrich_job_task.delay")
    def test_normalized_job_admin_action_queues_selected_eligible_jobs(self, mock_delay):
        job = create_job("ADMIN-JOB")
        modeladmin = NormalizedJobAdmin(NormalizedJob, AdminSite())
        modeladmin.message_user = Mock()
        request = RequestFactory().post("/")

        queue_selected_eligible_job_enrichments(modeladmin, request, NormalizedJob.objects.filter(id=job.id))

        mock_delay.assert_called_once_with(job.id)
        modeladmin.message_user.assert_called()

    @override_settings(
        JOB_ENRICHMENT_ENABLED=True,
        JOB_ENRICHMENT_RETRY_MAX_PER_RUN=10,
        JOB_ENRICHMENT_RETRY_COOLDOWN_MINUTES=60,
        JOB_ENRICHMENT_DAILY_LIMIT=100,
    )
    @patch("apps.llm.tasks.enrich_job_task.delay")
    def test_job_enrichment_admin_action_respects_permanent_failures(self, mock_delay):
        enrichment = JobEnrichment.objects.create(
            job=create_job("ADMIN-BLOCKED"),
            status=JobEnrichment.Status.FAILED,
            status_reason="forbidden/provider_blocked",
            last_error="HTTP Error 403: Forbidden",
            payload_hash="blocked",
            completed_at=timezone.now() - timedelta(hours=2),
        )
        modeladmin = JobEnrichmentAdmin(JobEnrichment, AdminSite())
        modeladmin.message_user = Mock()
        request = RequestFactory().post("/")

        queue_selected_eligible_enrichments_action(
            modeladmin,
            request,
            JobEnrichment.objects.filter(id=enrichment.id),
        )

        mock_delay.assert_not_called()
        modeladmin.message_user.assert_called()
