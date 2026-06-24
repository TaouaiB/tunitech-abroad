"""
Phase 14J — Admin operations metrics tests.

Tests that the AdminMetricsService includes all required ingestion pipeline
and enrichment metrics, and that the operations dashboard view works.
"""
import uuid
from datetime import timedelta
from django.test import TestCase, RequestFactory, override_settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.cache import cache

from apps.analytics.services.admin_metrics import AdminMetricsService
from apps.jobs.tasks import CELERY_HEARTBEAT_CACHE_KEY
from apps.jobs.models import (
    JobIngestionConfig,
    JobIngestionRun,
    JobSource,
    SourceType,
    RawJobRecord,
    NormalizedJob,
    NormalizationStatus,
    JobStatus,
    RemoteType,
    JobType,
    ExperienceLevel,
)
from apps.llm.models import JobEnrichment

User = get_user_model()


def _create_source():
    source, _ = JobSource.objects.get_or_create(
        slug="france_travail",
        defaults={
            "name": "France Travail",
            "base_url": "https://candidat.francetravail.fr",
            "source_type": SourceType.API,
            "is_active": True,
        },
    )
    return source


def _create_raw_record(source, job_id=None, norm_status=NormalizationStatus.PENDING):
    now = timezone.now()
    return RawJobRecord.objects.create(
        source=source,
        source_job_id=job_id or f"TEST-{uuid.uuid4().hex[:8]}",
        raw_payload_json={"test": True},
        payload_hash="abc123",
        first_seen_at=now,
        last_seen_at=now,
        last_fetched_at=now,
        normalization_status=norm_status,
    )


def _create_normalized_job(source, raw_record, status=JobStatus.ACTIVE):
    now = timezone.now()
    return NormalizedJob.objects.create(
        source=source,
        raw_record=raw_record,
        source_job_id=raw_record.source_job_id,
        title=f"Test Job {raw_record.source_job_id}",
        description="A test job description.",
        remote_type=RemoteType.UNKNOWN,
        job_type=JobType.FULL_TIME_JOB,
        experience_level=ExperienceLevel.JUNIOR,
        country="FR",
        status=status,
        first_seen_at=now,
        last_seen_at=now,
        last_fetched_at=now,
    )


class IngestionPipelineMetricsTest(TestCase):
    """Test that ingestion pipeline metrics are present and correct."""

    def test_metrics_include_ingestion_keys_with_no_data(self):
        """All ingestion metric keys should be present even with empty DB."""
        metrics = AdminMetricsService.get_dashboard_metrics()

        expected_keys = [
            'ingestion_latest_run_time',
            'ingestion_latest_run_status',
            'ingestion_latest_run_trigger',
            'ingestion_latest_run_fetched',
            'ingestion_latest_run_created',
            'ingestion_latest_run_updated',
            'ingestion_latest_run_normalized',
            'ingestion_latest_run_errors',
            'ingestion_latest_run_error_summary',
            'ingestion_latest_run_warning_summary',
            'ingestion_latest_run_enrichment_skipped',
            'ingestion_last_success_time',
            'ingestion_hours_since_success',
            'ingestion_last_failure_time',
            'ingestion_last_failure_error',
            'raw_records_pending_normalization',
            'raw_records_failed_normalization',
            'job_source_last_sync',
            'ingestion_stale_running_count',
            'ingestion_stale_running_age_hours',
        ]
        for key in expected_keys:
            self.assertIn(key, metrics, f"Missing metric key: {key}")

    def test_latest_run_metrics(self):
        """Latest ingestion run metrics should reflect the most recent run."""
        config = JobIngestionConfig.objects.create(
            name="test", enabled=True,
        )
        now = timezone.now()
        run = JobIngestionRun.objects.create(
            config=config,
            status="success",
            trigger="celery",
            fetched_count=50,
            created_raw_count=20,
            updated_raw_count=30,
            normalized_count=50,
            error_count=1,
            error_summary="One keyword failed",
        )

        metrics = AdminMetricsService.get_dashboard_metrics()

        self.assertEqual(metrics['ingestion_latest_run_status'], 'success')
        self.assertEqual(metrics['ingestion_latest_run_trigger'], 'celery')
        self.assertEqual(metrics['ingestion_latest_run_fetched'], 50)
        self.assertEqual(metrics['ingestion_latest_run_created'], 20)
        self.assertEqual(metrics['ingestion_latest_run_updated'], 30)
        self.assertEqual(metrics['ingestion_latest_run_normalized'], 50)
        self.assertEqual(metrics['ingestion_latest_run_errors'], 1)
        self.assertIn("keyword failed", metrics['ingestion_latest_run_error_summary'])

    def test_latest_run_enrichment_skips_are_warnings_not_errors_when_error_count_zero(self):
        config = JobIngestionConfig.objects.create(name="warning_split", enabled=True)
        JobIngestionRun.objects.create(
            config=config,
            status="success",
            trigger="celery",
            fetched_count=2,
            normalized_count=2,
            enrichment_skipped_count=2,
            error_count=0,
            error_summary=(
                "Enrichment skipped for 209YWFP: Job skill signal quality 'unknown' "
                "does not meet minimum relevance threshold 'partial'\n"
            ),
        )

        metrics = AdminMetricsService.get_dashboard_metrics()

        self.assertEqual(metrics["ingestion_latest_run_error_summary"], "")
        self.assertIn("Enrichment skipped for 2 job(s)", metrics["ingestion_latest_run_warning_summary"])
        self.assertIn("209YWFP", metrics["ingestion_latest_run_warning_summary"])

    def test_hours_since_last_success(self):
        """Should correctly compute hours since last successful ingestion."""
        config = JobIngestionConfig.objects.create(
            name="hours_test", enabled=True,
        )
        six_hours_ago = timezone.now() - timedelta(hours=6)
        JobIngestionRun.objects.create(
            config=config,
            status="success",
            trigger="celery",
            finished_at=six_hours_ago,
        )

        metrics = AdminMetricsService.get_dashboard_metrics()

        self.assertIsNotNone(metrics['ingestion_hours_since_success'])
        # Should be approximately 6 hours (allow 0.5h tolerance for test execution)
        self.assertAlmostEqual(
            metrics['ingestion_hours_since_success'], 6.0, delta=0.5
        )

    def test_failed_ingestion_metrics(self):
        """Should show last failed ingestion time and error."""
        config = JobIngestionConfig.objects.create(
            name="fail_test", enabled=True,
        )
        JobIngestionRun.objects.create(
            config=config,
            status="failed",
            trigger="celery",
            error_summary="API rate limit exceeded",
            finished_at=timezone.now(),
        )

        metrics = AdminMetricsService.get_dashboard_metrics()

        self.assertIsNotNone(metrics['ingestion_last_failure_time'])
        self.assertIn("rate limit", metrics['ingestion_last_failure_error'])

    def test_raw_records_normalization_counts(self):
        """Should count pending and failed normalization records."""
        source = _create_source()
        _create_raw_record(source, "pending-1", NormalizationStatus.PENDING)
        _create_raw_record(source, "pending-2", NormalizationStatus.PENDING)
        _create_raw_record(source, "failed-1", NormalizationStatus.FAILED)
        _create_raw_record(source, "success-1", NormalizationStatus.SUCCESS)

        metrics = AdminMetricsService.get_dashboard_metrics()

        self.assertEqual(metrics['raw_records_pending_normalization'], 2)
        self.assertEqual(metrics['raw_records_failed_normalization'], 1)

    def test_job_source_last_sync(self):
        """Should show JobSource.last_successful_sync_at."""
        source = _create_source()
        now = timezone.now()
        source.last_successful_sync_at = now
        source.save(update_fields=["last_successful_sync_at"])

        metrics = AdminMetricsService.get_dashboard_metrics()
        self.assertEqual(metrics['job_source_last_sync'], now)

    def test_stale_running_ingestion_metric(self):
        config = JobIngestionConfig.objects.create(name="stale_running", enabled=True)
        run = JobIngestionRun.objects.create(
            config=config,
            status="running",
            trigger="celery",
        )
        old = timezone.now() - timedelta(hours=2)
        JobIngestionRun.objects.filter(id=run.id).update(started_at=old)

        metrics = AdminMetricsService.get_dashboard_metrics()

        self.assertEqual(metrics["ingestion_stale_running_count"], 1)
        self.assertGreaterEqual(metrics["ingestion_stale_running_age_hours"], 1.9)


class EnrichmentMetricsTest(TestCase):
    """Test that enrichment metrics are present and correct."""

    def test_metrics_include_enrichment_keys_with_no_data(self):
        """All enrichment metric keys should be present even with empty DB."""
        metrics = AdminMetricsService.get_dashboard_metrics()

        expected_keys = [
            'enrichment_pending',
            'enrichment_processing',
            'enrichment_success',
            'enrichment_failed',
            'enrichment_validation_error',
            'enrichment_skipped',
            'enrichment_total',
            'enrichment_latest_success_time',
            'enrichment_latest_success_job',
            'enrichment_latest_failure_time',
            'enrichment_latest_failure_job',
            'enrichment_latest_failure_error',
            'jobs_without_enrichment',
            'enrichment_stale_processing',
            'enrichment_latest_forbidden_error',
            'active_jobs_without_enrichment_eligible',
            'active_jobs_without_enrichment_skipped',
            'active_jobs_without_enrichment_skipped_low_relevance',
            'active_jobs_without_enrichment_skipped_low_confidence',
            'active_jobs_without_enrichment_skipped_non_fr',
            'active_jobs_without_enrichment_skipped_existing_pending',
            'active_jobs_without_enrichment_other',
            'active_jobs_without_enrichment_bucket_total',
            'enrichment_retry_eligible_count',
            'enrichment_permanent_blocked_count',
        ]
        for key in expected_keys:
            self.assertIn(key, metrics, f"Missing enrichment metric key: {key}")

    def test_enrichment_status_counts(self):
        """Should correctly count enrichments by status."""
        source = _create_source()

        for i, status in enumerate([
            JobEnrichment.Status.SUCCESS,
            JobEnrichment.Status.SUCCESS,
            JobEnrichment.Status.FAILED,
            JobEnrichment.Status.PENDING,
        ]):
            raw = _create_raw_record(source, f"enrich-{i}")
            job = _create_normalized_job(source, raw)
            JobEnrichment.objects.create(
                job=job,
                status=status,
                payload_hash=f"hash-{i}",
                completed_at=timezone.now() if status != JobEnrichment.Status.PENDING else None,
            )

        metrics = AdminMetricsService.get_dashboard_metrics()

        self.assertEqual(metrics['enrichment_success'], 2)
        self.assertEqual(metrics['enrichment_failed'], 1)
        self.assertEqual(metrics['enrichment_pending'], 1)
        self.assertEqual(metrics['enrichment_total'], 4)

    def test_enrichment_latest_success(self):
        """Should show the most recent successful enrichment."""
        source = _create_source()
        raw = _create_raw_record(source, "success-latest")
        job = _create_normalized_job(source, raw)
        now = timezone.now()
        JobEnrichment.objects.create(
            job=job,
            status=JobEnrichment.Status.SUCCESS,
            payload_hash="hash-success",
            completed_at=now,
        )

        metrics = AdminMetricsService.get_dashboard_metrics()

        self.assertEqual(metrics['enrichment_latest_success_time'], now)
        self.assertIn("Test Job", metrics['enrichment_latest_success_job'])

    def test_enrichment_latest_success_uses_updated_at_when_completed_at_missing(self):
        source = _create_source()
        raw = _create_raw_record(source, "success-no-completed")
        job = _create_normalized_job(source, raw)
        enrichment = JobEnrichment.objects.create(
            job=job,
            status=JobEnrichment.Status.SUCCESS,
            payload_hash="hash-success-no-completed",
        )

        metrics = AdminMetricsService.get_dashboard_metrics()

        self.assertEqual(metrics['enrichment_latest_success_time'], enrichment.updated_at)
        self.assertIn("Test Job", metrics['enrichment_latest_success_job'])

    def test_enrichment_latest_failure(self):
        """Should show the most recent failed enrichment."""
        source = _create_source()
        raw = _create_raw_record(source, "fail-latest")
        job = _create_normalized_job(source, raw)
        now = timezone.now()
        JobEnrichment.objects.create(
            job=job,
            status=JobEnrichment.Status.FAILED,
            payload_hash="hash-fail",
            completed_at=now,
            last_error="LLM timeout after 30s",
        )

        metrics = AdminMetricsService.get_dashboard_metrics()

        self.assertEqual(metrics['enrichment_latest_failure_time'], now)
        self.assertIn("timeout", metrics['enrichment_latest_failure_error'])

    def test_enrichment_old_raw_403_is_sanitized_and_visible_as_provider_block(self):
        source = _create_source()
        raw = _create_raw_record(source, "forbidden-latest")
        job = _create_normalized_job(source, raw)
        JobEnrichment.objects.create(
            job=job,
            status=JobEnrichment.Status.FAILED,
            status_reason="provider_error",
            payload_hash="hash-forbidden",
            completed_at=timezone.now(),
            last_error="HTTP Error 403: Forbidden",
        )

        metrics = AdminMetricsService.get_dashboard_metrics()

        self.assertEqual(metrics['enrichment_latest_failure_error'], "forbidden/provider_blocked")
        self.assertEqual(metrics['enrichment_latest_forbidden_error'], "forbidden/provider_blocked")
        self.assertIsNotNone(metrics['enrichment_latest_forbidden_time'])

    def test_enrichment_key_daily_limit_is_sanitized_and_visible_separately(self):
        source = _create_source()
        raw = _create_raw_record(source, "key-limit-latest")
        job = _create_normalized_job(source, raw)
        now = timezone.now()
        JobEnrichment.objects.create(
            job=job,
            status=JobEnrichment.Status.FAILED,
            status_reason="key_daily_limit_exceeded",
            payload_hash="hash-key-limit",
            completed_at=now,
            last_error="HTTP Error 403: key_daily_limit_exceeded",
        )

        metrics = AdminMetricsService.get_dashboard_metrics()

        self.assertEqual(metrics['enrichment_latest_failure_error'], "key_daily_limit_exceeded")
        self.assertEqual(metrics['enrichment_latest_key_limit_error'], "key_daily_limit_exceeded")
        self.assertEqual(metrics['enrichment_latest_key_limit_time'], now)
        self.assertEqual(metrics['enrichment_latest_forbidden_error'], "")
        self.assertEqual(metrics["openrouter_circuit_latest_failure_reason"], "key_daily_limit_exceeded")

    @override_settings(JOB_ENRICHMENT_MIN_RELEVANCE="partial")
    def test_active_jobs_without_enrichment_split_by_relevance(self):
        source = _create_source()

        raw_eligible = _create_raw_record(source, "eligible-no-enrich")
        eligible = _create_normalized_job(source, raw_eligible)
        NormalizedJob.objects.filter(id=eligible.id).update(
            classification_json={"confidence": "high"},
            skill_signal_quality="strong",
        )

        raw_skipped = _create_raw_record(source, "skipped-no-enrich")
        skipped = _create_normalized_job(source, raw_skipped)
        NormalizedJob.objects.filter(id=skipped.id).update(
            classification_json={"confidence": "high"},
            skill_signal_quality="missing",
        )

        raw_low_confidence = _create_raw_record(source, "low-confidence-no-enrich")
        low_confidence = _create_normalized_job(source, raw_low_confidence)
        NormalizedJob.objects.filter(id=low_confidence.id).update(
            classification_json={"confidence": "low"},
            skill_signal_quality="strong",
        )

        raw_us = _create_raw_record(source, "us-no-enrich")
        us_job = _create_normalized_job(source, raw_us)
        NormalizedJob.objects.filter(id=us_job.id).update(
            country="US",
            classification_json={"confidence": "high"},
            skill_signal_quality="strong",
        )

        raw_pending = _create_raw_record(source, "pending-reservation")
        pending_job = _create_normalized_job(source, raw_pending)
        NormalizedJob.objects.filter(id=pending_job.id).update(
            classification_json={"confidence": "high"},
            skill_signal_quality="strong",
        )
        JobEnrichment.objects.create(
            job=pending_job,
            status=JobEnrichment.Status.PENDING,
            payload_hash="pending-hash",
        )

        raw_failed = _create_raw_record(source, "failed-other")
        failed_job = _create_normalized_job(source, raw_failed)
        NormalizedJob.objects.filter(id=failed_job.id).update(
            classification_json={"confidence": "high"},
            skill_signal_quality="strong",
        )
        JobEnrichment.objects.create(
            job=failed_job,
            status=JobEnrichment.Status.FAILED,
            status_reason="forbidden/provider_blocked",
            payload_hash="failed-hash",
        )

        metrics = AdminMetricsService.get_dashboard_metrics()

        self.assertEqual(metrics["jobs_without_enrichment"], 6)
        self.assertEqual(metrics["active_jobs_without_enrichment_eligible"], 1)
        self.assertEqual(metrics["active_jobs_without_enrichment_skipped_low_relevance"], 1)
        self.assertEqual(metrics["active_jobs_without_enrichment_skipped_low_confidence"], 1)
        self.assertEqual(metrics["active_jobs_without_enrichment_skipped_non_fr"], 1)
        self.assertEqual(metrics["active_jobs_without_enrichment_skipped_existing_pending"], 1)
        self.assertEqual(metrics["active_jobs_without_enrichment_failed_enrichment"], 1)
        self.assertEqual(metrics["active_jobs_without_enrichment_other"], 0)
        self.assertEqual(metrics["active_jobs_without_enrichment_bucket_total"], metrics["jobs_without_enrichment"])

    @override_settings(JOB_ENRICHMENT_RETRY_COOLDOWN_MINUTES=60)
    def test_enrichment_retry_and_permanent_blocked_counts(self):
        source = _create_source()
        old = timezone.now() - timedelta(hours=2)

        retry_job = _create_normalized_job(source, _create_raw_record(source, "retry-enrichment"))
        retry = JobEnrichment.objects.create(
            job=retry_job,
            status=JobEnrichment.Status.FAILED,
            status_reason="rate_limited",
            payload_hash="retry-hash",
            completed_at=old,
        )

        fresh_job = _create_normalized_job(source, _create_raw_record(source, "fresh-enrichment"))
        fresh = JobEnrichment.objects.create(
            job=fresh_job,
            status=JobEnrichment.Status.FAILED,
            status_reason="rate_limited",
            payload_hash="fresh-hash",
            completed_at=timezone.now(),
        )

        blocked_job = _create_normalized_job(source, _create_raw_record(source, "blocked-enrichment"))
        JobEnrichment.objects.create(
            job=blocked_job,
            status=JobEnrichment.Status.FAILED,
            status_reason="forbidden/provider_blocked",
            last_error="HTTP Error 403: Forbidden",
            payload_hash="blocked-hash",
            completed_at=old,
        )

        metrics = AdminMetricsService.get_dashboard_metrics()

        self.assertEqual(metrics["enrichment_retry_eligible_count"], 1)
        self.assertEqual(metrics["enrichment_permanent_blocked_count"], 1)


class CeleryHealthMetricsTest(TestCase):
    def tearDown(self):
        cache.delete(CELERY_HEARTBEAT_CACHE_KEY)

    def test_healthy_heartbeat_metric(self):
        cache.set(CELERY_HEARTBEAT_CACHE_KEY, timezone.now().isoformat(), timeout=300)

        metrics = AdminMetricsService.get_dashboard_metrics()

        self.assertEqual(metrics["celery_status"], "healthy")
        self.assertLess(metrics["celery_heartbeat_age_minutes"], 1)

    def test_stale_heartbeat_metric(self):
        stale = timezone.now() - timedelta(hours=1)
        cache.set(CELERY_HEARTBEAT_CACHE_KEY, stale.isoformat(), timeout=300)

        metrics = AdminMetricsService.get_dashboard_metrics()

        self.assertEqual(metrics["celery_status"], "stale")

    def test_unknown_heartbeat_with_pending_cv_warning(self):
        source = _create_source()
        user = User.objects.create_user(username="cv_user", email="cv@test.test")
        from django.core.files.uploadedfile import SimpleUploadedFile
        from apps.cvs.models import CVUpload

        cv = CVUpload.objects.create(
            user=user,
            file=SimpleUploadedFile("cv.pdf", b"test"),
            original_filename="cv.pdf",
            file_hash="cvhash",
            file_size=4,
            parse_status="pending",
        )
        old = timezone.now() - timedelta(hours=1)
        CVUpload.all_objects.filter(id=cv.id).update(uploaded_at=old)

        metrics = AdminMetricsService.get_dashboard_metrics()

        self.assertEqual(metrics["celery_status"], "unknown")
        self.assertEqual(metrics["cv_parses_pending"], 1)
        self.assertEqual(metrics["cv_parses_pending_stuck"], 1)

    def test_jobs_without_enrichment(self):
        """Should count active jobs that have no enrichment record."""
        source = _create_source()

        # 3 active jobs, 1 has enrichment
        for i in range(3):
            raw = _create_raw_record(source, f"no-enrich-{i}")
            job = _create_normalized_job(source, raw)
            if i == 0:
                JobEnrichment.objects.create(
                    job=job,
                    status=JobEnrichment.Status.SUCCESS,
                    payload_hash="hash",
                )

        # 1 expired job without enrichment — should NOT count
        raw_exp = _create_raw_record(source, "expired-no-enrich")
        _create_normalized_job(source, raw_exp, status=JobStatus.EXPIRED)

        metrics = AdminMetricsService.get_dashboard_metrics()

        # 3 active - 1 enriched = 2 without enrichment
        self.assertEqual(metrics['jobs_without_enrichment'], 2)


class OperationsViewTest(TestCase):
    """Test that the operations dashboard view is accessible to staff."""

    def setUp(self):
        self.staff_user = User.objects.create_user(
            username="ops_staff",
            email="ops@test.test",
            password="testpass123",
            is_staff=True,
        )

    def test_operations_view_returns_200_for_staff(self):
        self.client.force_login(self.staff_user)
        response = self.client.get("/admin/operations/")
        self.assertEqual(response.status_code, 200)

    def test_operations_view_redirects_non_staff(self):
        regular_user = User.objects.create_user(
            username="regular",
            email="regular@test.test",
            password="testpass123",
        )
        self.client.force_login(regular_user)
        response = self.client.get("/admin/operations/")
        # staff_member_required redirects to admin login
        self.assertNotEqual(response.status_code, 200)

    def test_operations_view_contains_ingestion_section(self):
        self.client.force_login(self.staff_user)
        response = self.client.get("/admin/operations/")
        content = response.content.decode()
        self.assertIn("Ingestion Pipeline", content)
        self.assertIn("Latest Ingestion Run", content)
        self.assertIn("Ingestion Health", content)

    def test_operations_view_contains_latest_run_error_summary(self):
        config = JobIngestionConfig.objects.create(name="view_error", enabled=True)
        JobIngestionRun.objects.create(
            config=config,
            status="partial_success",
            trigger="celery",
            error_count=1,
            error_summary="France Travail timeout on keyword python",
        )

        self.client.force_login(self.staff_user)
        response = self.client.get("/admin/operations/")
        content = response.content.decode()

        self.assertIn("Latest Run Error", content)
        self.assertIn("France Travail timeout", content)

    def test_operations_view_contains_latest_run_warning_without_error_label(self):
        config = JobIngestionConfig.objects.create(name="view_warning", enabled=True)
        JobIngestionRun.objects.create(
            config=config,
            status="success",
            trigger="celery",
            error_count=0,
            enrichment_skipped_count=1,
            error_summary="Enrichment skipped for 209YWFP: low relevance",
        )

        self.client.force_login(self.staff_user)
        response = self.client.get("/admin/operations/")
        content = response.content.decode()

        self.assertIn("Latest Run Warning", content)
        self.assertNotIn("Latest Run Error", content)
        self.assertIn("209YWFP", content)

    def test_operations_view_contains_key_daily_limit_stop(self):
        source = _create_source()
        job = _create_normalized_job(source, _create_raw_record(source, "view-key-limit"))
        JobEnrichment.objects.create(
            job=job,
            status=JobEnrichment.Status.FAILED,
            status_reason="key_daily_limit_exceeded",
            last_error="HTTP Error 403: key_daily_limit_exceeded",
            payload_hash="view-key-limit",
            completed_at=timezone.now(),
        )

        self.client.force_login(self.staff_user)
        response = self.client.get("/admin/operations/")
        content = response.content.decode()

        self.assertIn("Latest Key Limit / Credits Stop", content)
        self.assertIn("key_daily_limit_exceeded", content)

    def test_operations_view_contains_enrichment_section(self):
        self.client.force_login(self.staff_user)
        response = self.client.get("/admin/operations/")
        content = response.content.decode()
        self.assertIn("Job Enrichment", content)
        self.assertIn("Latest Enrichment Events", content)
        self.assertIn("Active Jobs Without Enrichment", content)
