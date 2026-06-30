import logging
from decimal import Decimal
from typing import Any, Dict

from django.db.models import Count, Max, Q
from django.utils import timezone

from apps.jobs.models import NormalizedJob
from apps.jobs.services.eligibility import JobEligibilityService

logger = logging.getLogger(__name__)


class JobEligibilityDiagnosticsService:
    @classmethod
    def run(cls) -> Dict[str, Any]:
        now = timezone.now()

        normalized_qs = NormalizedJob.objects.all()
        normalized_total = normalized_qs.count()

        active_qs = normalized_qs.filter(status="active")
        active_total = active_qs.count()

        public_visible_qs = JobEligibilityService.filter_publicly_visible(active_qs)
        public_visible_total = public_visible_qs.count()

        public_matchable_qs = JobEligibilityService.filter_matchable(active_qs)
        public_matchable_total = public_matchable_qs.count()

        excluded_total = active_total - public_visible_total

        zero_skill_qs = active_qs.annotate(job_skill_count=Count("job_skills")).filter(job_skill_count=0)
        weak_skill_qs = active_qs.filter(skill_signal_quality="generic_only")
        low_confidence_only_qs = (
            active_qs.annotate(
                job_skill_count=Count("job_skills"),
                max_skill_confidence=Max("job_skills__confidence"),
            )
            .filter(job_skill_count__gt=0)
            .filter(Q(max_skill_confidence__lt=Decimal("0.500")) | Q(max_skill_confidence__isnull=True))
        )

        zero_skill_jobs = zero_skill_qs.count()
        generic_skill_jobs = weak_skill_qs.count()
        low_confidence_only_jobs = low_confidence_only_qs.count()
        weak_skill_jobs = generic_skill_jobs + low_confidence_only_jobs
        non_it_candidates = active_qs.filter(skill_signal_quality="excluded_non_it").count()

        eligibility_reasons: dict[str, int] = {}

        excluded_qs = active_qs.exclude(id__in=public_visible_qs.values("id"))
        for job in excluded_qs.iterator(chunk_size=1000):
            reason = JobEligibilityService.reason(job)
            eligibility_reasons[reason] = eligibility_reasons.get(reason, 0) + 1

        diagnostics = {
            "ok": True,
            "service": "job_eligibility_diagnostics",
            "generated_at": now.isoformat(),
            "scope": {
                "active_only": True,
            },
            "counts": {
                "normalized_total": normalized_total,
                "active_total": active_total,
                "public_visible_total": public_visible_total,
                "public_matchable_total": public_matchable_total,
                "excluded_total": excluded_total,
                "zero_skill_jobs": zero_skill_jobs,
                "weak_skill_jobs": weak_skill_jobs,
                "generic_skill_jobs": generic_skill_jobs,
                "low_confidence_only_jobs": low_confidence_only_jobs,
                "non_it_candidates": non_it_candidates,
            },
            "statuses": {},
            "reasons": {
                "exclusion_reasons": eligibility_reasons,
                "quality_reasons": {
                    "zero_skill_jobs": zero_skill_jobs,
                    "generic_skill_jobs": generic_skill_jobs,
                    "low_confidence_only_jobs": low_confidence_only_jobs,
                    "non_it_candidates": non_it_candidates,
                },
            },
            "top_items": [
                {
                    "bucket": "zero_skill_jobs",
                    "public_id": str(job.public_id),
                    "title": job.title,
                    "company_name": job.company_name,
                }
                for job in zero_skill_qs.order_by("-last_seen_at")[:10]
            ],
            "warnings": [],
            "errors": [],
            "recommended_actions": [],
            "artifacts": {},
        }

        if excluded_total > active_total * 0.5 and active_total > 0:
            diagnostics["warnings"].append("More than 50% of active jobs are excluded from public visibility.")

        return diagnostics
