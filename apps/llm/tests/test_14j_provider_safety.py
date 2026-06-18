from datetime import timedelta
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase, override_settings
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
from apps.llm.models import JobEnrichment
from apps.llm.services.job_enrichment import (
    enqueue_job_enrichment,
    enrich_job,
    force_retry_provider_blocked_enrichments,
    get_openrouter_circuit_status,
)


def create_job(source_job_id="JOB-1"):
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
        skill_signal_quality="strong",
        classification_json={"confidence": "high"},
    )


def create_provider_failure(job, index=0):
    return JobEnrichment.objects.create(
        job=job,
        status=JobEnrichment.Status.FAILED,
        status_reason="rate_limited",
        last_error="HTTP Error 429: Rate limited",
        payload_hash=f"failed-{index}",
        completed_at=timezone.now() - timedelta(minutes=1),
    )


class OpenRouterProviderSafetyTests(TestCase):
    @override_settings(
        OPENROUTER_CIRCUIT_BREAKER_ENABLED=True,
        OPENROUTER_CIRCUIT_BREAKER_FAILURE_THRESHOLD=2,
        OPENROUTER_CIRCUIT_BREAKER_WINDOW_MINUTES=30,
        OPENROUTER_CIRCUIT_BREAKER_COOLDOWN_MINUTES=60,
    )
    def test_circuit_opens_from_recent_provider_failures(self):
        create_provider_failure(create_job("FAIL-1"), 1)
        create_provider_failure(create_job("FAIL-2"), 2)

        status = get_openrouter_circuit_status()

        self.assertEqual(status["status"], "open")
        self.assertTrue(status["is_open"])
        self.assertEqual(status["recent_failure_count"], 2)

    @override_settings(
        JOB_ENRICHMENT_ENABLED=True,
        OPENROUTER_CIRCUIT_BREAKER_ENABLED=True,
        OPENROUTER_CIRCUIT_BREAKER_FAILURE_THRESHOLD=1,
        OPENROUTER_CIRCUIT_BREAKER_WINDOW_MINUTES=30,
        OPENROUTER_CIRCUIT_BREAKER_COOLDOWN_MINUTES=60,
    )
    def test_circuit_open_prevents_openrouter_call(self):
        create_provider_failure(create_job("FAIL-CALL"), 1)
        job = create_job("NO-CALL")

        with patch("apps.llm.services.client.OpenRouterClient._make_request") as mock_request:
            enrichment = enrich_job(job, force=True)

        mock_request.assert_not_called()
        self.assertEqual(enrichment.status, JobEnrichment.Status.SKIPPED)
        self.assertEqual(enrichment.status_reason, "provider_circuit_open")

    @override_settings(
        JOB_ENRICHMENT_ENABLED=True,
        OPENROUTER_CIRCUIT_BREAKER_ENABLED=True,
        OPENROUTER_CIRCUIT_BREAKER_FAILURE_THRESHOLD=1,
        OPENROUTER_CIRCUIT_BREAKER_WINDOW_MINUTES=30,
        OPENROUTER_CIRCUIT_BREAKER_COOLDOWN_MINUTES=60,
    )
    @patch("apps.llm.tasks.enrich_job_task.delay")
    def test_circuit_open_prevents_queueing(self, mock_delay):
        create_provider_failure(create_job("FAIL-QUEUE"), 1)
        job = create_job("NO-QUEUE")

        queued = enqueue_job_enrichment(job)

        self.assertFalse(queued)
        mock_delay.assert_not_called()
        enrichment = JobEnrichment.objects.get(job=job)
        self.assertEqual(enrichment.status_reason, "provider_circuit_open")

    @override_settings(OPENROUTER_ENRICHMENT_RATE_LIMIT="3/m", OPENROUTER_ENRICHMENT_QUEUE="llm")
    def test_enrichment_task_has_rate_limit_and_route_settings(self):
        from django.conf import settings
        from apps.llm.tasks import enrich_job_task

        self.assertEqual(enrich_job_task.rate_limit, "3/m")
        self.assertEqual(
            settings.CELERY_TASK_ROUTES["apps.llm.tasks.enrich_job_task"]["queue"],
            "llm",
        )


class ProviderBlockedCanaryTests(TestCase):
    @override_settings(JOB_ENRICHMENT_FORCE_PROVIDER_BLOCKED_RETRY=False)
    @patch("apps.llm.services.job_enrichment.enqueue_job_enrichment")
    def test_force_retry_provider_blocked_default_disabled(self, mock_enqueue):
        result = force_retry_provider_blocked_enrichments(limit=1, dry_run=False)

        self.assertFalse(result["enabled"])
        self.assertEqual(result["queued"], 0)
        mock_enqueue.assert_not_called()

    @override_settings(JOB_ENRICHMENT_FORCE_PROVIDER_BLOCKED_RETRY=False)
    def test_management_command_default_disabled(self):
        out = StringIO()

        call_command("force_retry_provider_blocked_enrichments", stdout=out)

        output = out.getvalue()
        self.assertIn("provider_blocked retries can burn OpenRouter credits", output)
        self.assertIn("JOB_ENRICHMENT_FORCE_PROVIDER_BLOCKED_RETRY is False", output)
        self.assertIn("queued: 0", output)

    @override_settings(JOB_ENRICHMENT_FORCE_PROVIDER_BLOCKED_RETRY=True)
    @patch("apps.llm.services.job_enrichment.enqueue_job_enrichment", return_value=True)
    def test_force_retry_provider_blocked_is_hard_capped_and_service_only(self, mock_enqueue):
        for index in range(5):
            job = create_job(f"BLOCKED-{index}")
            JobEnrichment.objects.create(
                job=job,
                status=JobEnrichment.Status.FAILED,
                status_reason="forbidden/provider_blocked",
                last_error="HTTP Error 403: forbidden/provider_blocked",
                payload_hash=f"blocked-{index}",
            )

        result = force_retry_provider_blocked_enrichments(limit=99, dry_run=False)

        self.assertTrue(result["enabled"])
        self.assertEqual(result["effective_limit"], 3)
        self.assertEqual(result["candidate_count"], 3)
        self.assertEqual(result["queued"], 3)
        self.assertEqual(mock_enqueue.call_count, 3)

    @override_settings(JOB_ENRICHMENT_FORCE_PROVIDER_BLOCKED_RETRY=True)
    @patch("apps.llm.services.job_enrichment.enqueue_job_enrichment", return_value=True)
    def test_force_retry_provider_blocked_excludes_key_daily_limit(self, mock_enqueue):
        retry_job = create_job("BLOCKED-RETRY")
        JobEnrichment.objects.create(
            job=retry_job,
            status=JobEnrichment.Status.FAILED,
            status_reason="forbidden/provider_blocked",
            last_error="HTTP Error 403: forbidden/provider_blocked",
            payload_hash="blocked-retry",
        )
        key_limit_job = create_job("KEY-LIMIT-NO-RETRY")
        JobEnrichment.objects.create(
            job=key_limit_job,
            status=JobEnrichment.Status.FAILED,
            status_reason="key_daily_limit_exceeded",
            last_error="HTTP Error 403: key_daily_limit_exceeded",
            payload_hash="key-limit-no-retry",
        )

        result = force_retry_provider_blocked_enrichments(limit=3, dry_run=False)

        self.assertEqual(result["candidate_count"], 1)
        self.assertEqual(result["queued"], 1)
        mock_enqueue.assert_called_once_with(retry_job.enrichment.job, force=True)
