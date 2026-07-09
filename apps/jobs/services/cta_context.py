from apps.profiles.models import CandidateProfile
from apps.cvs.models import CVUpload
from apps.matching.models import MatchResult


class CTAContextService:
    @staticmethod
    def get_job_cta_context(user, job):
        if not user.is_authenticated:
            return {"state": "anonymous"}

        profile = CandidateProfile.objects.filter(user=user).first()
        has_ready_profile = bool(profile and profile.profile_completion_score >= 50)
        has_ready_cv = CVUpload.objects.filter(
            user=user,
            is_active=True,
            parse_status__in=["parsed", "parsed_with_warnings"],
        ).exists()

        is_ready = bool(profile and (has_ready_profile or has_ready_cv))
        if not is_ready:
            return {"state": "no_profile"}

        match = MatchResult.objects.filter(user=user, job=job).order_by("-created_at").first()
        if not match:
            return {"state": "no_match"}

        return {"state": "match_exists", "match": match}
