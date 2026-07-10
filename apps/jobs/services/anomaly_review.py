from __future__ import annotations

from decimal import Decimal

from django.db.models import Count, Q, Sum

from apps.cvs.models import CVParsedData
from apps.jobs.models import (
    JobStatus,
    NormalizedJob,
    NormalizedJobSkill,
    SkillExtractionStatus,
)
from apps.skills.models import UnmatchedSkillCandidate


LOW_CONFIDENCE_THRESHOLD = Decimal("0.750")


class JobAnomalyReviewService:
    """Read-only query helpers for admin intelligence review."""

    @staticmethod
    def active_zero_skill_jobs():
        return (
            NormalizedJob.objects.select_related("source")
            .filter(status=JobStatus.ACTIVE)
            .annotate(skill_count=Count("job_skills"))
            .filter(skill_count=0)
            .order_by("-last_seen_at", "public_id")
        )

    @staticmethod
    def active_generic_only_jobs():
        return (
            NormalizedJob.objects.select_related("source")
            .filter(status=JobStatus.ACTIVE, skill_signal_quality="generic_only")
            .order_by("-last_seen_at", "public_id")
        )

    @staticmethod
    def low_confidence_job_skills(threshold: Decimal = LOW_CONFIDENCE_THRESHOLD):
        return (
            NormalizedJobSkill.objects.select_related("job", "job__source", "skill")
            .filter(confidence__isnull=False, confidence__lt=threshold)
            .order_by("confidence", "skill__canonical_name", "job__public_id")
        )

    @staticmethod
    def unmatched_candidates():
        return UnmatchedSkillCandidate.objects.select_related("mapped_skill", "reviewed_by").order_by(
            "-occurrence_count",
            "source_type",
            "status",
            "normalized_text",
            "id",
        )

    @staticmethod
    def unmatched_candidate_counts():
        return (
            UnmatchedSkillCandidate.objects.values("status", "source_type")
            .annotate(candidate_count=Count("id"), total_occurrences=Sum("occurrence_count"))
            .order_by("status", "source_type")
        )

    @staticmethod
    def jobs_with_failed_or_partial_skill_extraction():
        return (
            NormalizedJob.objects.select_related("source")
            .filter(
                Q(skill_extraction_status__in=[
                    SkillExtractionStatus.FAILED,
                    SkillExtractionStatus.NOT_ENOUGH_TEXT,
                    SkillExtractionStatus.PENDING,
                ])
                | Q(skill_signal_quality__in=["partial", "missing", "unknown", ""])
            )
            .order_by("-last_seen_at", "public_id")
        )

    @staticmethod
    def hidden_or_excluded_jobs():
        return (
            NormalizedJob.objects.select_related("source")
            .filter(
                Q(status__in=[
                    JobStatus.STALE,
                    JobStatus.EXPIRED,
                    JobStatus.REMOVED,
                    JobStatus.ARCHIVED,
                ])
                | Q(quality_issue__gt="")
                | Q(skill_signal_quality="excluded_non_it")
            )
            .order_by("-last_seen_at", "public_id")
        )

    @staticmethod
    def recent_cv_parses_with_warnings():
        return (
            CVParsedData.objects.select_related("cv_upload", "cv_upload__user")
            .filter(cv_upload__deleted_at__isnull=True)
            .filter(Q(cv_upload__parse_status="parsed_with_warnings") | ~Q(warnings_json=[]))
            .order_by("-updated_at", "cv_upload__public_id")
        )

    @classmethod
    def summary_counts(cls) -> dict[str, int]:
        return {
            "active_zero_skill_jobs": cls.active_zero_skill_jobs().count(),
            "active_generic_only_jobs": cls.active_generic_only_jobs().count(),
            "low_confidence_job_skills": cls.low_confidence_job_skills().count(),
            "unmatched_skill_candidates": cls.unmatched_candidates().count(),
            "jobs_with_failed_or_partial_skill_extraction": cls.jobs_with_failed_or_partial_skill_extraction().count(),
            "hidden_or_excluded_jobs": cls.hidden_or_excluded_jobs().count(),
            "recent_cv_parses_with_warnings": cls.recent_cv_parses_with_warnings().count(),
        }
