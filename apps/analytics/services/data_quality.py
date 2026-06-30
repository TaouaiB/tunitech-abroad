from decimal import Decimal

from django.db.models import Count, Max, Q

from apps.cvs.models import CVUpload
from apps.jobs.models import NormalizedJob, SearchQueryLog
from apps.jobs.services.eligibility import JobEligibilityService
from apps.skills.models import UnmatchedSkillCandidate


class AdminDataQualityService:
    @classmethod
    def get_dashboard_context(cls) -> dict:
        active_qs = NormalizedJob.objects.filter(status="active").select_related("source")
        zero_skill_jobs = (
            active_qs.annotate(job_skill_count=Count("job_skills"))
            .filter(job_skill_count=0)
            .order_by("-created_at")[:20]
        )
        weak_skill_jobs = (
            active_qs.annotate(
                job_skill_count=Count("job_skills"),
                max_skill_confidence=Max("job_skills__confidence"),
            )
            .filter(
                Q(skill_signal_quality="generic_only")
                | Q(max_skill_confidence__lt=Decimal("0.500"))
                | Q(max_skill_confidence__isnull=True, job_skill_count__gt=0)
            )
            .order_by("-created_at")[:20]
        )

        public_visible_ids = JobEligibilityService.filter_publicly_visible(active_qs).values("id")
        hidden_jobs = []
        for job in active_qs.exclude(id__in=public_visible_ids).order_by("-created_at")[:20]:
            job.admin_public_eligibility_reason = JobEligibilityService.reason(job)
            hidden_jobs.append(job)

        cvs_with_warnings = (
            CVUpload.all_objects.filter(
                Q(parse_status__in=["parsed_with_warnings", "failed"])
                | Q(parsed_data__warnings_json__isnull=False)
            )
            .exclude(parsed_data__warnings_json=[])
            .select_related("user")
            .order_by("-uploaded_at")[:20]
        )
        low_confidence_cvs = (
            CVUpload.all_objects.filter(parsed_data__confidence_json__isnull=False)
            .exclude(parsed_data__confidence_json={})
            .select_related("user")
            .order_by("-uploaded_at")[:20]
        )

        zero_result_searches = (
            SearchQueryLog.objects.filter(result_count=0)
            .values("normalized_query", "normalized_company", "skill")
            .annotate(count=Count("id"))
            .order_by("-count", "normalized_query")[:20]
        )

        return {
            "jobs_zero_skills": zero_skill_jobs,
            "weak_skill_jobs": weak_skill_jobs,
            "unknown_skills": UnmatchedSkillCandidate.objects.filter(status="pending").order_by(
                "-occurrence_count", "-updated_at"
            )[:20],
            "hidden_jobs": hidden_jobs,
            "cvs_with_warnings": cvs_with_warnings,
            "low_confidence_cvs": low_confidence_cvs,
            "zero_result_searches": zero_result_searches,
        }
