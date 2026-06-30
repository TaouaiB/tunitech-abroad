import logging
from django.db import connection
from django.core.cache import cache
from django.utils import timezone
from apps.jobs.models import NormalizedJob
from apps.jobs.services.eligibility import JobEligibilityService
from apps.jobs.tasks import CELERY_HEARTBEAT_CACHE_KEY
from django.conf import settings

logger = logging.getLogger(__name__)


class HealthCheckService:
    @classmethod
    def check(cls) -> dict:
        return cls.run()

    @classmethod
    def run(cls) -> dict:
        generated_at = timezone.now()
        db_status = "ok"
        redis_status = "ok"
        jobs_status = "ok"
        celery_status = "unknown"
        status = "ok"
        details = {}
        counts = {}
        errors = []
        warnings = []
        reasons = {}
        recommended_actions = []

        # ── Database ──────────────────────────────────────────────────────────
        try:
            connection.ensure_connection()
        except Exception:
            db_status = "error"
            status = "critical"
            logger.error("Health check: database connectivity failure.")
            errors.append("database_unavailable")
            recommended_actions.append("Check database connectivity and service status.")

        # ── Redis ─────────────────────────────────────────────────────────────
        try:
            cache.set("health_check_test", "1", timeout=5)
            if cache.get("health_check_test") != "1":
                redis_status = "error"
                if status == "ok":
                    status = "degraded"
                errors.append("redis_read_write_failed")
        except Exception:
            redis_status = "error"
            if status == "ok":
                status = "degraded"
            logger.error("Health check: Redis connectivity failure.")
            errors.append("redis_unavailable")
            recommended_actions.append("Check Redis connectivity and service status.")

        # ── Jobs ──────────────────────────────────────────────────────────────
        try:
            active_jobs = NormalizedJob.objects.filter(status="active").count()
            public_matchable = JobEligibilityService.filter_matchable(
                NormalizedJob.objects.filter(status="active")
            ).count()
            public_visible = JobEligibilityService.filter_publicly_visible(
                NormalizedJob.objects.filter(status="active")
            ).count()
            counts.update({
                "active_jobs": active_jobs,
                "public_visible_jobs": public_visible,
                "public_matchable_jobs": public_matchable,
            })
            details["active_jobs_count"] = active_jobs
            details["public_matchable_count"] = public_matchable

            if active_jobs == 0:
                jobs_status = "warning"
                warnings.append("zero_active_jobs")
                recommended_actions.append("Inspect ingestion, freshness, and job eligibility diagnostics.")
            elif public_matchable == 0:
                jobs_status = "warning"
                warnings.append("zero_matchable_jobs")
                recommended_actions.append("Inspect ingestion, freshness, and job eligibility diagnostics.")

            # Baseline cache read/write is best-effort. If Redis is
            # unavailable here, do not flag jobs_check_failed — the DB
            # query above already succeeded.
            try:
                last_active = cache.get("health_last_active_jobs")
                if isinstance(last_active, (int, float)) and last_active > 0:
                    if active_jobs < (last_active * 0.5):  # 50% drop
                        jobs_status = "warning"
                        warnings.append("active_job_count_drop")
                        reasons["active_job_count_drop"] = {
                            "before": last_active,
                            "after": active_jobs,
                            "threshold": "50%",
                        }
                cache.set("health_last_active_jobs", active_jobs, timeout=86400)
            except Exception:
                logger.error("Health check: baseline cache read/write failed (Redis unavailable).")
                warnings.append("jobs_baseline_cache_unavailable")

        except Exception:
            jobs_status = "error"
            logger.error("Health check: jobs query failure.")
            errors.append("jobs_check_failed")

        # ── Celery heartbeat ──────────────────────────────────────────────────
        _heartbeat_cache_ok = True
        heartbeat_value = None
        try:
            heartbeat_value = cache.get(CELERY_HEARTBEAT_CACHE_KEY)
        except Exception:
            logger.error("Health check: Celery heartbeat cache read failed (Redis unavailable).")
            warnings.append("celery_heartbeat_check_unavailable")
            _heartbeat_cache_ok = False
        if _heartbeat_cache_ok:
            if heartbeat_value:
                try:
                    heartbeat_at = timezone.datetime.fromisoformat(heartbeat_value)
                    if timezone.is_naive(heartbeat_at):
                        heartbeat_at = timezone.make_aware(heartbeat_at)
                    age_minutes = round((generated_at - heartbeat_at).total_seconds() / 60, 1)
                    details["celery_last_heartbeat_at"] = heartbeat_at.isoformat()
                    details["celery_heartbeat_age_minutes"] = age_minutes
                    celery_status = "healthy" if age_minutes <= settings.CELERY_HEARTBEAT_STALE_MINUTES else "stale"
                    if celery_status == "stale":
                        warnings.append("celery_heartbeat_stale")
                        if status == "ok":
                            status = "degraded"
                except (TypeError, ValueError):
                    celery_status = "error"
                    errors.append("celery_heartbeat_invalid")
            else:
                warnings.append("celery_heartbeat_missing")

        # ── ok semantics ──────────────────────────────────────────────────────
        # ok must be False whenever there are non-empty errors, regardless of
        # the computed status string. Job/celery warnings do not by themselves
        # flip ok to False.
        ok = (status == "ok") and (len(errors) == 0)

        return {
            "ok": ok,
            "service": "health_check",
            "generated_at": generated_at.isoformat(),
            "scope": {"source": "admin_monitoring"},
            "counts": counts,
            "statuses": {
                "overall": status,
                "database": db_status,
                "redis": redis_status,
                "jobs": jobs_status,
                "celery": celery_status,
            },
            "reasons": reasons,
            "top_items": [],
            "warnings": warnings,
            "errors": errors,
            "recommended_actions": recommended_actions,
            "artifacts": {},
            # Legacy flat keys preserved for existing tests.
            "status": status,
            "database": db_status,
            "redis": redis_status,
            "jobs": jobs_status,
            "details": details,
        }
