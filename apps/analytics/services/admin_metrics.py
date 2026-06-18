from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.cache import cache
from django.db.models import Sum, Count, Q, F
from apps.cvs.models import CVUpload
from apps.jobs.models import (
    NormalizedJob,
    JobStatus,
    JobIngestionRun,
    RawJobRecord,
    NormalizationStatus,
    JobSource,
)
from apps.recommendations.models import JobRecommendation, RecommendationRun, SavedJob
from apps.llm.models import LLMRequestLog, JobEnrichment
from apps.llm.services.job_enrichment import (
    get_openrouter_circuit_status,
    get_allowed_skill_signal_qualities,
    is_enrichment_retry_eligible,
    sanitize_enrichment_error,
)
from apps.notifications.models import EmailEvent
from apps.privacy.models import DeletionRequest
from apps.jobs.tasks import CELERY_HEARTBEAT_CACHE_KEY

User = get_user_model()

class AdminMetricsService:
    @classmethod
    def get_dashboard_metrics(cls):
        now = timezone.now()
        seven_days_ago = now - timedelta(days=7)
        twenty_four_hours_ago = now - timedelta(hours=24)
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)

        metrics = {}

        # Users
        metrics['users_total'] = User.objects.count()
        metrics['new_signups_7d'] = User.objects.filter(date_joined__gte=seven_days_ago).count()
        metrics['active_users_7d'] = User.objects.filter(last_login__gte=seven_days_ago).count()

        # CVs
        metrics['cv_uploads_7d'] = CVUpload.all_objects.filter(uploaded_at__gte=seven_days_ago).count()
        metrics['cv_parse_failures_7d'] = CVUpload.all_objects.filter(
            uploaded_at__gte=seven_days_ago,
            parse_status='failed'
        ).count()
        cv_stale_cutoff = now - timedelta(minutes=settings.CV_PARSE_STALE_MINUTES)
        metrics['cv_parses_pending'] = CVUpload.all_objects.filter(parse_status='pending').count()
        metrics['cv_parses_processing_stale'] = CVUpload.all_objects.filter(
            parse_status='processing',
            uploaded_at__lt=cv_stale_cutoff,
        ).count()
        metrics['cv_parses_pending_stuck'] = CVUpload.all_objects.filter(
            parse_status__in=['pending', 'processing'],
            uploaded_at__lt=cv_stale_cutoff,
        ).count()

        cls._add_celery_metrics(metrics, now)

        # Jobs — basic counts
        metrics['active_jobs'] = NormalizedJob.objects.filter(status=JobStatus.ACTIVE).count()
        metrics['jobs_ingested_24h'] = NormalizedJob.objects.filter(created_at__gte=twenty_four_hours_ago).count()
        metrics['stale_expired_jobs'] = NormalizedJob.objects.filter(status__in=[JobStatus.STALE, JobStatus.EXPIRED]).count()

        # Legacy IngestionRun metrics removed as part of Phase 14J follow-up.

        # ─── Ingestion Pipeline (from JobIngestionRun) ───────────────
        cls._add_ingestion_pipeline_metrics(metrics, now)

        # ─── Enrichment ─────────────────────────────────────────────
        cls._add_enrichment_metrics(metrics, now)

        # Recommendations
        metrics['recommendation_runs_24h'] = RecommendationRun.objects.filter(started_at__gte=twenty_four_hours_ago).count()
        metrics['recommendation_failures_24h'] = RecommendationRun.objects.filter(
            started_at__gte=twenty_four_hours_ago,
            status='failed'
        ).count()
        metrics['stale_recommendations'] = JobRecommendation.objects.filter(status='stale').count()
        metrics['saved_jobs_count'] = SavedJob.objects.count()

        # LLM
        llm_today = LLMRequestLog.objects.filter(created_at__gte=today)
        metrics['llm_calls_today'] = llm_today.count()
        metrics['llm_failures_today'] = llm_today.filter(status='failed').count() # Assuming status can be 'failed' or 'error'

        # Emails
        emails_24h = EmailEvent.objects.filter(created_at__gte=twenty_four_hours_ago)
        metrics['emails_sent_24h'] = emails_24h.filter(status='sent').count()
        metrics['emails_failed_24h'] = emails_24h.filter(status='failed').count()

        # Privacy
        metrics['pending_deletion_requests'] = DeletionRequest.objects.filter(status='pending').count()

        return metrics

    @classmethod
    def _add_ingestion_pipeline_metrics(cls, metrics, now):
        """Add ingestion pipeline metrics from JobIngestionRun."""
        # Latest run (any status)
        latest_run = JobIngestionRun.objects.order_by('-started_at').first()
        if latest_run:
            error_summary, warning_summary = cls._split_ingestion_summary(latest_run)
            metrics['ingestion_latest_run_time'] = latest_run.started_at
            metrics['ingestion_latest_run_status'] = latest_run.status
            metrics['ingestion_latest_run_trigger'] = latest_run.trigger
            metrics['ingestion_latest_run_fetched'] = latest_run.fetched_count
            metrics['ingestion_latest_run_created'] = latest_run.created_raw_count
            metrics['ingestion_latest_run_updated'] = latest_run.updated_raw_count
            metrics['ingestion_latest_run_normalized'] = latest_run.normalized_count
            metrics['ingestion_latest_run_errors'] = latest_run.error_count
            metrics['ingestion_latest_run_error_summary'] = error_summary[:200] if latest_run.error_count else ""
            metrics['ingestion_latest_run_warning_summary'] = warning_summary[:200]
            metrics['ingestion_latest_run_enrichment_skipped'] = latest_run.enrichment_skipped_count
        else:
            metrics['ingestion_latest_run_time'] = None
            metrics['ingestion_latest_run_status'] = None
            metrics['ingestion_latest_run_trigger'] = None
            metrics['ingestion_latest_run_fetched'] = 0
            metrics['ingestion_latest_run_created'] = 0
            metrics['ingestion_latest_run_updated'] = 0
            metrics['ingestion_latest_run_normalized'] = 0
            metrics['ingestion_latest_run_errors'] = 0
            metrics['ingestion_latest_run_error_summary'] = ""
            metrics['ingestion_latest_run_warning_summary'] = ""
            metrics['ingestion_latest_run_enrichment_skipped'] = 0

        # Last successful ingestion
        last_success = JobIngestionRun.objects.filter(
            status__in=['success', 'partial_success']
        ).order_by('-started_at').first()
        if last_success:
            metrics['ingestion_last_success_time'] = last_success.finished_at or last_success.started_at
            delta = now - metrics['ingestion_last_success_time']
            metrics['ingestion_hours_since_success'] = round(delta.total_seconds() / 3600, 1)
        else:
            metrics['ingestion_last_success_time'] = None
            metrics['ingestion_hours_since_success'] = None

        # Last failed ingestion
        last_fail = JobIngestionRun.objects.filter(
            status='failed'
        ).order_by('-started_at').first()
        if last_fail:
            metrics['ingestion_last_failure_time'] = last_fail.finished_at or last_fail.started_at
            metrics['ingestion_last_failure_error'] = (last_fail.error_summary or "")[:200]
        else:
            metrics['ingestion_last_failure_time'] = None
            metrics['ingestion_last_failure_error'] = ""

        stale_cutoff = now - timedelta(minutes=settings.INGESTION_STALE_RUNNING_MINUTES)
        stale_running = JobIngestionRun.objects.filter(
            status="running",
            started_at__lt=stale_cutoff,
        ).order_by("started_at").first()
        metrics["ingestion_stale_running_count"] = JobIngestionRun.objects.filter(
            status="running",
            started_at__lt=stale_cutoff,
        ).count()
        if stale_running:
            metrics["ingestion_stale_running_started_at"] = stale_running.started_at
            metrics["ingestion_stale_running_age_hours"] = round(
                (now - stale_running.started_at).total_seconds() / 3600,
                1,
            )
        else:
            metrics["ingestion_stale_running_started_at"] = None
            metrics["ingestion_stale_running_age_hours"] = None

        # Raw records pending/failed normalization
        metrics['raw_records_pending_normalization'] = RawJobRecord.objects.filter(
            normalization_status=NormalizationStatus.PENDING
        ).count()
        metrics['raw_records_failed_normalization'] = RawJobRecord.objects.filter(
            normalization_status=NormalizationStatus.FAILED
        ).count()

        # JobSource freshness
        ft_source = JobSource.objects.filter(slug="france_travail").first()
        metrics['job_source_last_sync'] = ft_source.last_successful_sync_at if ft_source else None

    @staticmethod
    def _split_ingestion_summary(run: JobIngestionRun) -> tuple[str, str]:
        error_lines: list[str] = []
        enrichment_skip_lines: list[str] = []
        for line in (run.error_summary or "").splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.lower().startswith("enrichment skipped for ") or stripped.lower().startswith("warning:"):
                enrichment_skip_lines.append(stripped)
            else:
                error_lines.append(stripped)

        warning_lines: list[str] = []
        if run.enrichment_skipped_count:
            warning_lines.append(f"Enrichment skipped for {run.enrichment_skipped_count} job(s).")
        if enrichment_skip_lines:
            warning_lines.append(enrichment_skip_lines[-1])

        return "\n".join(error_lines), "\n".join(warning_lines)

    @classmethod
    def _add_enrichment_metrics(cls, metrics, now):
        """Add JobEnrichment status breakdown and latest success/failure."""
        # Status counts
        status_counts = (
            JobEnrichment.objects.values('status')
            .annotate(count=Count('id'))
        )
        status_map = {row['status']: row['count'] for row in status_counts}
        metrics['enrichment_pending'] = status_map.get('pending', 0)
        metrics['enrichment_processing'] = status_map.get('processing', 0)
        metrics['enrichment_queued_pending_processing'] = metrics['enrichment_pending'] + metrics['enrichment_processing']
        metrics['enrichment_success'] = status_map.get('success', 0)
        metrics['enrichment_failed'] = status_map.get('failed', 0)
        metrics['enrichment_validation_error'] = status_map.get('validation_error', 0)
        metrics['enrichment_skipped'] = status_map.get('skipped', 0)
        metrics['enrichment_total'] = sum(status_map.values())
        stale_processing_cutoff = now - timedelta(minutes=settings.JOB_ENRICHMENT_PROCESSING_STALE_MINUTES)
        metrics['enrichment_stale_processing'] = JobEnrichment.objects.filter(
            status=JobEnrichment.Status.PROCESSING,
        ).filter(
            Q(started_at__lt=stale_processing_cutoff)
            | Q(started_at__isnull=True, updated_at__lt=stale_processing_cutoff)
        ).count()

        # Latest successful enrichment
        latest_success = JobEnrichment.objects.filter(
            status=JobEnrichment.Status.SUCCESS
        ).select_related('job').order_by(
            F('completed_at').desc(nulls_last=True),
            F('updated_at').desc(nulls_last=True),
        ).first()
        if latest_success:
            metrics['enrichment_latest_success_time'] = latest_success.completed_at or latest_success.updated_at
            metrics['enrichment_latest_success_job'] = latest_success.job.title[:80] if latest_success.job else ""
        else:
            metrics['enrichment_latest_success_time'] = None
            metrics['enrichment_latest_success_job'] = ""

        # Latest failed enrichment
        latest_fail = JobEnrichment.objects.filter(
            status__in=[JobEnrichment.Status.FAILED, JobEnrichment.Status.VALIDATION_ERROR]
        ).select_related('job').order_by(
            F('completed_at').desc(nulls_last=True),
            F('updated_at').desc(nulls_last=True),
        ).first()
        if latest_fail:
            metrics['enrichment_latest_failure_time'] = latest_fail.completed_at or latest_fail.updated_at
            metrics['enrichment_latest_failure_job'] = latest_fail.job.title[:80] if latest_fail.job else ""
            metrics['enrichment_latest_failure_error'] = sanitize_enrichment_error(latest_fail)
        else:
            metrics['enrichment_latest_failure_time'] = None
            metrics['enrichment_latest_failure_job'] = ""
            metrics['enrichment_latest_failure_error'] = ""

        # Latest forbidden/provider-blocked error, including historical raw 403 rows.
        latest_forbidden = JobEnrichment.objects.filter(
            Q(status_reason__in=['forbidden', 'forbidden/provider_blocked', 'provider_blocked'])
            | Q(last_error__icontains='HTTP Error 403')
            | Q(last_error__icontains='Forbidden')
        ).exclude(
            Q(status_reason__in=["key_daily_limit_exceeded", "insufficient_credits"])
            | Q(last_error__icontains="key_daily_limit_exceeded")
            | Q(last_error__icontains="insufficient_credits")
            | (Q(last_error__icontains="key limit exceeded") & Q(last_error__icontains="daily limit"))
            | (Q(last_error__icontains="insufficient") & Q(last_error__icontains="credit"))
        ).select_related('job').order_by(
            F('completed_at').desc(nulls_last=True),
            F('updated_at').desc(nulls_last=True),
        ).first()
        if latest_forbidden:
            metrics['enrichment_latest_forbidden_time'] = latest_forbidden.completed_at or latest_forbidden.updated_at
            metrics['enrichment_latest_forbidden_job'] = latest_forbidden.job.title[:80] if latest_forbidden.job else ""
            metrics['enrichment_latest_forbidden_error'] = sanitize_enrichment_error(latest_forbidden)
        else:
            metrics['enrichment_latest_forbidden_time'] = None
            metrics['enrichment_latest_forbidden_job'] = ""
            metrics['enrichment_latest_forbidden_error'] = ""

        latest_key_limit = JobEnrichment.objects.filter(
            Q(status_reason="key_daily_limit_exceeded")
            | Q(last_error__icontains="key_daily_limit_exceeded")
            | (Q(last_error__icontains="key limit exceeded") & Q(last_error__icontains="daily limit"))
            | Q(status_reason="insufficient_credits")
            | Q(last_error__icontains="insufficient_credits")
            | (Q(last_error__icontains="insufficient") & Q(last_error__icontains="credit"))
        ).select_related('job').order_by(
            F('completed_at').desc(nulls_last=True),
            F('updated_at').desc(nulls_last=True),
        ).first()
        if latest_key_limit:
            metrics['enrichment_latest_key_limit_time'] = latest_key_limit.completed_at or latest_key_limit.updated_at
            metrics['enrichment_latest_key_limit_job'] = latest_key_limit.job.title[:80] if latest_key_limit.job else ""
            metrics['enrichment_latest_key_limit_error'] = sanitize_enrichment_error(latest_key_limit)
        else:
            metrics['enrichment_latest_key_limit_time'] = None
            metrics['enrichment_latest_key_limit_job'] = ""
            metrics['enrichment_latest_key_limit_error'] = ""

        # Cost today
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_cost = JobEnrichment.objects.filter(
            completed_at__gte=today_start
        ).aggregate(total_cost=Sum('estimated_cost_usd'))['total_cost']
        metrics['enrichment_cost_today'] = today_cost or 0.00

        buckets = cls._active_jobs_without_enrichment_buckets()
        metrics['jobs_without_enrichment'] = buckets["total"]
        metrics['active_jobs_without_enrichment_eligible'] = buckets["eligible"]
        metrics['active_jobs_without_enrichment_skipped'] = (
            buckets["skipped_low_relevance"]
            + buckets["skipped_low_confidence"]
            + buckets["skipped_non_fr"]
            + buckets["skipped_existing_pending"]
            + buckets["other"]
        )
        metrics['active_jobs_without_enrichment_skipped_low_relevance'] = buckets["skipped_low_relevance"]
        metrics['active_jobs_without_enrichment_skipped_low_confidence'] = buckets["skipped_low_confidence"]
        metrics['active_jobs_without_enrichment_skipped_non_fr'] = buckets["skipped_non_fr"]
        metrics['active_jobs_without_enrichment_skipped_existing_pending'] = buckets["skipped_existing_pending"]
        metrics['active_jobs_without_enrichment_other'] = buckets["other"]
        metrics['active_jobs_without_enrichment_bucket_total'] = buckets["bucket_total"]

        # Permanent blocked records
        permanent_qs = JobEnrichment.objects.filter(
            Q(status=JobEnrichment.Status.VALIDATION_ERROR) |
            Q(status=JobEnrichment.Status.FAILED, status_reason__in=[
                "missing_api_key", "forbidden", "forbidden/provider_blocked",
                "provider_blocked", "key_daily_limit_exceeded",
                "insufficient_credits", "invalid_model"
            ]) |
            Q(status=JobEnrichment.Status.FAILED, last_error__icontains="403") |
            Q(status=JobEnrichment.Status.FAILED, last_error__icontains="forbidden")
        )
        metrics['enrichment_permanent_blocked_count'] = permanent_qs.count()

        retry_candidates = JobEnrichment.objects.filter(
            status__in=[
                JobEnrichment.Status.PENDING,
                JobEnrichment.Status.PROCESSING,
                JobEnrichment.Status.FAILED,
                JobEnrichment.Status.SKIPPED,
            ]
        ).only(
            "status",
            "status_reason",
            "last_error",
            "created_at",
            "updated_at",
            "started_at",
            "completed_at",
        )
        metrics['enrichment_retry_eligible_count'] = sum(
            1 for enrichment in retry_candidates if is_enrichment_retry_eligible(enrichment, now=now)[0]
        )

        circuit_status = get_openrouter_circuit_status(now=now)
        metrics["openrouter_circuit_status"] = circuit_status["status"]
        metrics["openrouter_circuit_enabled"] = circuit_status["enabled"]
        metrics["openrouter_circuit_latest_failure_reason"] = circuit_status["latest_failure_reason"]
        metrics["openrouter_circuit_recent_failures"] = circuit_status["recent_failure_count"]
        metrics["openrouter_circuit_failure_threshold"] = circuit_status["failure_threshold"]
        metrics["openrouter_circuit_window_minutes"] = circuit_status["window_minutes"]
        metrics["openrouter_circuit_cooldown_remaining_minutes"] = circuit_status["cooldown_remaining_minutes"]
        metrics["openrouter_enrichment_queue"] = settings.OPENROUTER_ENRICHMENT_QUEUE
        metrics["openrouter_enrichment_rate_limit"] = settings.OPENROUTER_ENRICHMENT_RATE_LIMIT
        metrics["ft_request_delay_seconds"] = settings.FRANCE_TRAVAIL_REQUEST_DELAY_SECONDS
        metrics["ft_max_requests_per_run"] = settings.FRANCE_TRAVAIL_MAX_REQUESTS_PER_RUN
        metrics["ft_backoff_on_429_seconds"] = settings.FRANCE_TRAVAIL_BACKOFF_ON_429_SECONDS

    @classmethod
    def _active_jobs_without_enrichment_buckets(cls) -> dict[str, int]:
        successful_job_ids = JobEnrichment.objects.filter(
            status=JobEnrichment.Status.SUCCESS,
        ).values_list("job_id", flat=True)
        base_qs = NormalizedJob.objects.filter(status=JobStatus.ACTIVE).exclude(id__in=successful_job_ids)
        total = base_qs.count()
        allowed_qualities = get_allowed_skill_signal_qualities()

        pending_job_ids = JobEnrichment.objects.filter(
            status__in=[JobEnrichment.Status.PENDING, JobEnrichment.Status.PROCESSING],
        ).values_list("job_id", flat=True)
        existing_pending = base_qs.filter(id__in=pending_job_ids).count()
        queue_candidate_qs = base_qs.exclude(id__in=pending_job_ids)

        non_fr = queue_candidate_qs.exclude(country="FR").count()
        fr_qs = queue_candidate_qs.filter(country="FR")

        low_confidence = fr_qs.exclude(classification_json__confidence="high").count()
        high_confidence_qs = fr_qs.filter(classification_json__confidence="high")

        eligible = high_confidence_qs.filter(skill_signal_quality__in=allowed_qualities).exclude(
            enrichment__status__in=[
                JobEnrichment.Status.FAILED,
                JobEnrichment.Status.VALIDATION_ERROR,
                JobEnrichment.Status.SKIPPED,
            ],
        ).count()
        low_relevance = high_confidence_qs.exclude(skill_signal_quality__in=allowed_qualities).count()
        bucket_total = eligible + low_relevance + low_confidence + non_fr + existing_pending
        other = max(total - bucket_total, 0)

        return {
            "total": total,
            "eligible": eligible,
            "skipped_low_relevance": low_relevance,
            "skipped_low_confidence": low_confidence,
            "skipped_non_fr": non_fr,
            "skipped_existing_pending": existing_pending,
            "other": other,
            "bucket_total": bucket_total + other,
        }

    @classmethod
    def _add_celery_metrics(cls, metrics, now):
        heartbeat_value = cache.get(CELERY_HEARTBEAT_CACHE_KEY)
        heartbeat_at = None
        if heartbeat_value:
            try:
                heartbeat_at = timezone.datetime.fromisoformat(heartbeat_value)
                if timezone.is_naive(heartbeat_at):
                    heartbeat_at = timezone.make_aware(heartbeat_at)
            except (TypeError, ValueError):
                heartbeat_at = None

        metrics["celery_last_heartbeat_at"] = heartbeat_at
        if heartbeat_at:
            age_minutes = round((now - heartbeat_at).total_seconds() / 60, 1)
            metrics["celery_heartbeat_age_minutes"] = age_minutes
            metrics["celery_status"] = (
                "healthy"
                if age_minutes <= settings.CELERY_HEARTBEAT_STALE_MINUTES
                else "stale"
            )
        else:
            metrics["celery_heartbeat_age_minutes"] = None
            metrics["celery_status"] = "unknown"
