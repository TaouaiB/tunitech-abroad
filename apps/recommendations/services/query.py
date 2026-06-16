from dataclasses import dataclass
import logging
from apps.recommendations.models import JobRecommendation, RecommendationRun, SavedJob

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class RecommendationDashboardResult:
    recommendations: list[JobRecommendation]
    is_pending: bool
    is_stale: bool
    latest_run: RecommendationRun | None


class RecommendationQueryService:
    @classmethod
    def _enqueue_refresh(cls, user) -> None:
        from apps.recommendations.tasks import refresh_user_recommendations

        try:
            refresh_user_recommendations.delay(user.id, "dashboard_stale_refresh")
        except Exception as exc:
            logger.warning("Could not enqueue recommendation refresh for user %s: %s", user.id, exc)

    @classmethod
    def _with_saved_state(cls, user, recommendations: list[JobRecommendation]) -> list[JobRecommendation]:
        job_ids = [recommendation.job_id for recommendation in recommendations]
        saved_job_ids = set(
            SavedJob.objects.filter(user=user, job_id__in=job_ids).values_list("job_id", flat=True)
        )
        for recommendation in recommendations:
            recommendation.is_saved = recommendation.job_id in saved_job_ids
        return recommendations

    @classmethod
    def get_dashboard_recommendations(cls, user, limit: int = 20) -> RecommendationDashboardResult:
        from apps.profiles.models import CandidateProfile
        
        latest_run = RecommendationRun.objects.filter(user=user).order_by("-started_at").first()
        
        # Check if currently running
        is_running = latest_run is not None and latest_run.status == "running"
        
        profile = CandidateProfile.objects.filter(user=user).first()
        is_profile_complete = profile is not None and profile.profile_completion_score >= 50
        
        # Check active recommendations
        active_recs = list(JobRecommendation.objects.filter(
            user=user, 
            status="active"
        ).select_related("job", "job__source").order_by("rank")[:limit])
        
        if active_recs:
            return RecommendationDashboardResult(
                recommendations=cls._with_saved_state(user, active_recs),
                is_pending=is_running,
                is_stale=False,
                latest_run=latest_run,
            )
            
        # If no active ones, check stale ones
        stale_recs = list(JobRecommendation.objects.filter(
            user=user, 
            status="stale"
        ).select_related("job", "job__source").order_by("rank")[:limit])
        
        if stale_recs:
            if not is_running and is_profile_complete:
                cls._enqueue_refresh(user)
            return RecommendationDashboardResult(
                recommendations=cls._with_saved_state(user, stale_recs),
                is_pending=is_running,
                is_stale=True,
                latest_run=latest_run,
            )
            
        is_pending = is_running
        
        # If no active and no stale, enqueue generation if not already running
        if not is_running and is_profile_complete:
            # If the latest run was successful, don't enqueue again to avoid infinite refresh
            if latest_run and latest_run.status == "success":
                is_pending = False
            else:
                cls._enqueue_refresh(user)
                is_pending = True
            
        return RecommendationDashboardResult(
            recommendations=[],
            is_pending=is_pending,
            is_stale=False,
            latest_run=latest_run,
        )
