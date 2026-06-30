import logging
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from apps.cvs.models import CVUpload
from apps.jobs.models import NormalizedJob, JobIngestionRun, SearchQueryLog
from apps.jobs.services.eligibility import JobEligibilityService
from apps.skills.models import UnmatchedSkillCandidate
from apps.notifications.models import EmailEvent

User = get_user_model()

logger = logging.getLogger(__name__)


class AdminOpsDigestService:
    @classmethod
    def generate_digest(cls) -> dict:
        now = timezone.now()
        yesterday = now - timedelta(days=1)

        # New user registrations in last 24 h.
        new_users = User.objects.filter(date_joined__gte=yesterday).count()

        # New CV uploads in last 24 h — use uploaded_at (the correct timestamp field).
        # CVUpload.objects excludes soft-deleted records; appropriate for count purposes.
        new_cvs = CVUpload.objects.filter(uploaded_at__gte=yesterday).count()

        # Parse outcomes in last 24 h — use all_objects for internal admin digest.
        parse_success = CVUpload.all_objects.filter(
            uploaded_at__gte=yesterday,
            parse_status__in=["parsed", "parsed_with_warnings"],
        ).count()
        parse_failed = CVUpload.all_objects.filter(
            uploaded_at__gte=yesterday,
            parse_status="failed",
        ).count()

        # Current active job counts.
        active_jobs = NormalizedJob.objects.filter(status="active").count()
        public_jobs = JobEligibilityService.filter_publicly_visible(
            NormalizedJob.objects.filter(status="active")
        ).count()
        matchable_jobs = JobEligibilityService.filter_matchable(
            NormalizedJob.objects.filter(status="active")
        ).count()

        # Pending unknown/unmatched skill candidates.
        unknown_skills = UnmatchedSkillCandidate.objects.filter(status="pending").count()

        # Email failures in last 24 h.
        email_failures = EmailEvent.objects.filter(
            created_at__gte=yesterday, status="failed"
        ).count()

        # ── Ingestion run counts (TTA-16G-005) ────────────────────────────────
        # JobIngestionRun exists in this codebase; count runs started in last 24 h.
        ingestion_runs_total = JobIngestionRun.objects.filter(
            started_at__gte=yesterday
        ).count()
        ingestion_runs_failed = JobIngestionRun.objects.filter(
            started_at__gte=yesterday,
            status="failed",
        ).count()

        # ── Zero-result search counts (TTA-16G-005) ───────────────────────────
        # SearchQueryLog.result_count == 0 means the search returned no jobs.
        zero_result_search_count = SearchQueryLog.objects.filter(
            created_at__gte=yesterday,
            result_count=0,
        ).count()
        total_search_count = SearchQueryLog.objects.filter(
            created_at__gte=yesterday,
        ).count()

        # ── LLM cost ──────────────────────────────────────────────────────────
        # No LLM request/cost model is available in this codebase before Phase 9.
        # Return a safe flag so consumers know the field is intentionally absent.
        llm_cost_unavailable = True

        return {
            "period": "last_24_hours",
            "new_users": new_users,
            "new_cvs": new_cvs,
            "parse_success": parse_success,
            "parse_failed": parse_failed,
            "active_jobs": active_jobs,
            "public_jobs": public_jobs,
            "matchable_jobs": matchable_jobs,
            "unknown_skills": unknown_skills,
            "email_failures": email_failures,
            "ingestion_runs_total": ingestion_runs_total,
            "ingestion_runs_failed": ingestion_runs_failed,
            "zero_result_search_count": zero_result_search_count,
            "total_search_count": total_search_count,
            "llm_cost_unavailable": llm_cost_unavailable,
        }

    @classmethod
    def send_digest_email(cls):
        admin_email = getattr(settings, 'ADMIN_ALERT_EMAIL', None)
        if not admin_email:
            logger.error("ADMIN_ALERT_EMAIL is not set. Cannot send digest.")
            return

        digest_data = cls.generate_digest()

        subject = "[DAILY DIGEST] TuniAtlas Operations"
        body_lines = ["Daily Operations Digest:\n"]
        for k, v in digest_data.items():
            body_lines.append(f"{k.replace('_', ' ').title()}: {v}")

        body = "\n".join(body_lines)

        try:
            send_mail(
                subject=subject,
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[admin_email],
                fail_silently=False,
            )
            logger.info("Admin ops digest sent successfully.")
        except Exception:
            logger.error("Failed to send admin ops digest email.")
