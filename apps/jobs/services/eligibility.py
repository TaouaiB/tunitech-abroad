from django.db.models import Q, QuerySet
from django.utils import timezone

from apps.jobs.models import JobStatus, NormalizedJob


class PublicJobState:
    PUBLIC_MATCHABLE = "public_matchable"
    PUBLIC_LIMITED_PENDING_ANALYSIS = "public_limited_pending_analysis"
    ADMIN_REVIEW_ONLY = "admin_review_only"
    EXCLUDED = "excluded"

class JobEligibilityService:
    MATCHABLE_SIGNAL_QUALITIES = ("strong", "partial")
    UNANALYZED_SIGNAL_QUALITIES = ("missing", "unknown", "")

    @classmethod
    def active_public_base_queryset(cls, qs: QuerySet[NormalizedJob] | None = None) -> QuerySet[NormalizedJob]:
        now = timezone.now()
        if qs is None:
            qs = NormalizedJob.objects.all()
        return (
            qs.filter(status=JobStatus.ACTIVE, source__is_active=True)
            .filter(Q(expires_at__isnull=True) | Q(expires_at__gte=now))
        )

    @classmethod
    def filter_publicly_visible(cls, qs: QuerySet[NormalizedJob] | None = None) -> QuerySet[NormalizedJob]:
        qs = cls.active_public_base_queryset(qs)
        return qs.exclude(
            Q(skill_signal_quality="excluded_non_it")
            | Q(classification_json__contains={"confidence": "excluded"})
            | Q(classification_json__contains={"is_it": False})
        ).filter(
            Q(skill_signal_quality__in=cls.MATCHABLE_SIGNAL_QUALITIES, job_skills__isnull=False)
            | Q(
                skill_signal_quality__in=cls.UNANALYZED_SIGNAL_QUALITIES,
                skill_extraction_status__in=("pending", "processing"),
            )
        ).distinct()

    @classmethod
    def filter_matchable(cls, qs: QuerySet[NormalizedJob] | None = None) -> QuerySet[NormalizedJob]:
        qs = cls.active_public_base_queryset(qs)
        return qs.filter(
            skill_signal_quality__in=cls.MATCHABLE_SIGNAL_QUALITIES,
            job_skills__isnull=False,
        ).exclude(
            Q(skill_signal_quality="excluded_non_it")
            | Q(classification_json__contains={"confidence": "excluded"})
            | Q(classification_json__contains={"is_it": False})
        ).distinct()

    @staticmethod
    def _has_materialized_skills(job) -> bool:
        prefetched = getattr(job, "_prefetched_objects_cache", {})
        if "job_skills" in prefetched:
            return bool(prefetched["job_skills"])
        return job.job_skills.exists()

    @staticmethod
    def classify_public_state(job) -> str:
        if job.status != JobStatus.ACTIVE:
            return PublicJobState.EXCLUDED

        classification = job.classification_json or {}
        confidence = classification.get("confidence")
        is_it = classification.get("is_it")
        
        signal = job.skill_signal_quality
        extraction = job.skill_extraction_status
        
        if signal == "excluded_non_it" or confidence == "excluded" or is_it is False:
            return PublicJobState.EXCLUDED

        legacy_unclassified = is_it is None
        if is_it is not True and not legacy_unclassified:
            return PublicJobState.ADMIN_REVIEW_ONLY

        if signal in ("missing", "unknown", "", None):
            if extraction in ("pending", "processing"):
                if (is_it is True and confidence == "high") or legacy_unclassified:
                    return PublicJobState.PUBLIC_LIMITED_PENDING_ANALYSIS
                return PublicJobState.ADMIN_REVIEW_ONLY
            return PublicJobState.ADMIN_REVIEW_ONLY

        has_materialized_skills = JobEligibilityService._has_materialized_skills(job)

        if signal in JobEligibilityService.MATCHABLE_SIGNAL_QUALITIES:
            if not has_materialized_skills:
                return PublicJobState.ADMIN_REVIEW_ONLY
            return PublicJobState.PUBLIC_MATCHABLE

        if signal == "generic_only":
            return PublicJobState.ADMIN_REVIEW_ONLY

        return PublicJobState.ADMIN_REVIEW_ONLY

    @staticmethod
    def reason(job) -> str:
        state = JobEligibilityService.classify_public_state(job)
        if state == PublicJobState.EXCLUDED:
            return "Classified as non-IT or explicitly excluded"
        elif state == PublicJobState.ADMIN_REVIEW_ONLY:
            if job.skill_signal_quality in ("missing", "unknown", "", None):
                return "Zero materialized skills after extraction or weak IT signal"
            return "Ambiguous technical evidence or conflict"
        elif state == PublicJobState.PUBLIC_LIMITED_PENDING_ANALYSIS:
            return "IT job pending skill extraction"
        return "Matchable IT job"

    @staticmethod
    def is_publicly_visible(job) -> bool:
        state = JobEligibilityService.classify_public_state(job)
        return state in (PublicJobState.PUBLIC_MATCHABLE, PublicJobState.PUBLIC_LIMITED_PENDING_ANALYSIS)
        
    @staticmethod
    def is_matchable(job) -> bool:
        return JobEligibilityService.classify_public_state(job) == PublicJobState.PUBLIC_MATCHABLE
