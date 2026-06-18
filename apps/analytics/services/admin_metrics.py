from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Sum, Count, Q
from apps.cvs.models import CVUpload
from apps.jobs.models import NormalizedJob, JobStatus, IngestionRun, IngestionRunStatus
from apps.recommendations.models import JobRecommendation, RecommendationRun, SavedJob
from apps.llm.models import LLMRequestLog
from apps.notifications.models import EmailEvent
from apps.privacy.models import DeletionRequest

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
        metrics['cv_parses_pending_stuck'] = CVUpload.all_objects.filter(
            parse_status__in=['pending', 'processing'],
            uploaded_at__lt=now - timedelta(minutes=15)
        ).count()

        # Jobs
        metrics['active_jobs'] = NormalizedJob.objects.filter(status=JobStatus.ACTIVE).count()
        metrics['jobs_ingested_24h'] = NormalizedJob.objects.filter(created_at__gte=twenty_four_hours_ago).count()
        metrics['stale_expired_jobs'] = NormalizedJob.objects.filter(status__in=[JobStatus.STALE, JobStatus.EXPIRED]).count()

        last_success = IngestionRun.objects.filter(status=IngestionRunStatus.SUCCESS).order_by('-started_at').first()
        metrics['latest_successful_ingestion'] = last_success.started_at if last_success else None
        last_failed = IngestionRun.objects.filter(status=IngestionRunStatus.FAILED).order_by('-started_at').first()
        metrics['latest_failed_ingestion'] = last_failed.started_at if last_failed else None

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
