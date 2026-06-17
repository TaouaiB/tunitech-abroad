import logging
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied

from apps.matching.models import MatchResult
from apps.matching.services.scoring import MatchScoringService
from apps.cvs.models import CVUpload
from apps.jobs.models import NormalizedJob
from apps.jobs.services.query import JobQueryService

try:
    from apps.analytics.services.user_event import UserEventService
except ImportError:
    UserEventService = None

logger = logging.getLogger(__name__)

class MatchResultService:
    @staticmethod
    def create_match_result(user, job: NormalizedJob, cv_upload=None) -> MatchResult:
        if not user.is_authenticated:
            raise PermissionDenied("User must be authenticated to create a match result.")
            
        public_job = JobQueryService.get_public_job(job.public_id)
            
        profile = getattr(user, 'candidate_profile', None)
        if not profile:
            raise ValueError("Candidate profile not found for user.")
            
        if not cv_upload:
            cv_upload = CVUpload.objects.filter(user=user, is_active=True).first()
            
        score_result = MatchScoringService.calculate(profile=profile, job=public_job, cv_upload=cv_upload)
        
        profile_snapshot = {
            "public_id": str(profile.public_id),
            "current_level": profile.current_level,
            "years_experience": float(profile.years_experience) if profile.years_experience is not None else None,
            "target_country": profile.target_country,
            "target_roles": profile.target_roles,
            "french_level": profile.french_level,
            "english_level": profile.english_level,
        }
        
        job_snapshot = {
            "public_id": str(public_job.public_id),
            "title": public_job.title,
            "company_name": public_job.company_name,
            "experience_level": public_job.experience_level,
            "country": public_job.country,
            "remote_type": public_job.remote_type,
            "language_requirements_json": public_job.language_requirements_json,
            "required_skills_json": public_job.required_skills_json,
            "optional_skills_json": public_job.optional_skills_json,
            "match_confidence": score_result.match_confidence,
        }
        
        match = MatchResult.objects.create(
            user=user,
            profile=profile,
            cv_upload=cv_upload,
            job=public_job,
            profile_snapshot_json=profile_snapshot,
            job_snapshot_json=job_snapshot,
            fit_score=score_result.fit_score,
            technical_skills_score=score_result.technical_skills_score,
            experience_score=score_result.experience_score,
            role_title_score=score_result.role_title_score,
            language_score=score_result.language_score,
            location_score=score_result.location_score,
            strong_skills_json=score_result.strong_skills,
            missing_required_skills_json=score_result.missing_required_skills,
            missing_optional_skills_json=score_result.missing_optional_skills,
            risk_flags_json=score_result.risk_flags,
            profile_signals_json=score_result.profile_signals,
            recommended_actions_json=score_result.recommended_actions,
            scoring_version=score_result.scoring_version,
        )
        
        if UserEventService is not None:
            try:
                UserEventService.record_event(
                    event_type="match_generated",
                    user=user,
                    metadata={"match_public_id": str(match.public_id)}
                )
            except Exception as e:
                logger.warning(f"Failed to record UserEvent match_generated: {e}")
                
        return match

    @staticmethod
    def get_user_match(user, public_id) -> MatchResult:
        if not user.is_authenticated:
            raise PermissionDenied("User must be authenticated.")
        return get_object_or_404(MatchResult, user=user, public_id=public_id)

    @staticmethod
    def list_user_matches(user) -> QuerySet[MatchResult]:
        if not user.is_authenticated:
            raise PermissionDenied("User must be authenticated.")
        return MatchResult.objects.filter(user=user).order_by("-created_at")
