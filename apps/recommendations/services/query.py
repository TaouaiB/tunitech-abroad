from dataclasses import dataclass
import logging
from apps.recommendations.models import JobRecommendation, RecommendationRun, SavedJob
from apps.matching.models import MatchResult

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class RecommendationDashboardResult:
    recommendations: list[JobRecommendation]
    is_pending: bool
    is_stale: bool
    latest_run: RecommendationRun | None
    blocked_reason: str | None = None


class RecommendationQueryService:
    @classmethod
    def _freshness_value(cls, recommendation: JobRecommendation):
        job = recommendation.job
        return (
            job.published_at
            or job.first_seen_at
            or job.last_seen_at
            or recommendation.computed_at
        )

    @classmethod
    def _sort_recommendations(cls, recommendations: list[JobRecommendation]) -> list[JobRecommendation]:
        return sorted(
            recommendations,
            key=lambda recommendation: (
                -recommendation.fit_score,
                -float(recommendation.ranking_score),
                -cls._freshness_value(recommendation).timestamp(),
            ),
        )

    @classmethod
    def _get_recommendations_by_status(cls, user, status: str, limit: int) -> list[JobRecommendation]:
        recommendations = list(
            JobRecommendation.objects.filter(
                user=user,
                status=status,
            )
            .select_related("job", "job__source")
            .order_by("-fit_score", "-ranking_score", "-job__published_at", "-job__first_seen_at", "-job__last_seen_at")[
                : max(limit * 3, limit)
            ]
        )
        return cls._sort_recommendations(recommendations)[:limit]

    @classmethod
    def _enqueue_refresh(cls, user) -> None:
        try:
            from apps.recommendations.services.recommendation import RecommendationService

            RecommendationService.refresh_for_user(user, "dashboard_refresh")
        except Exception as exc:
            logger.warning("Could not refresh recommendations for user %s: %s", user.id, exc)

    @classmethod
    def _with_saved_state(cls, user, recommendations: list[JobRecommendation]) -> list[JobRecommendation]:
        job_ids = [recommendation.job_id for recommendation in recommendations]
        saved_job_ids = set(
            SavedJob.objects.filter(user=user, job_id__in=job_ids).values_list("job_id", flat=True)
        )
        match_public_ids_by_job_id = {}
        matches = MatchResult.objects.filter(user=user, job_id__in=job_ids).order_by("job_id", "-created_at")
        for match in matches:
            if match.job_id not in match_public_ids_by_job_id:
                match_public_ids_by_job_id[match.job_id] = match.public_id

        for recommendation in recommendations:
            recommendation.is_saved = recommendation.job_id in saved_job_ids
            recommendation.match_public_id = match_public_ids_by_job_id.get(recommendation.job_id)
        return recommendations

    @classmethod
    def get_dashboard_recommendations(cls, user, limit: int = 20) -> RecommendationDashboardResult:
        from apps.profiles.models import CandidateProfile
        
        latest_run = RecommendationRun.objects.filter(user=user).order_by("-started_at").first()
        
        # Check if currently running
        is_running = latest_run is not None and latest_run.status == "running"
        
        profile = CandidateProfile.objects.filter(user=user).first()
        from apps.cvs.models import CVUpload
        active_cv = CVUpload.objects.filter(user=user, is_active=True).first()
        
        blocked_reason = None
        score = 0
        if profile:
            from apps.profiles.services.completeness import ProfileCompletenessService
            ProfileCompletenessService.calculate(profile)
            recommendation_report = ProfileCompletenessService.get_recommendation_report(profile)
            recommendation_missing = recommendation_report["missing"] + recommendation_report["invalid"]
            score = recommendation_report["score"]
        else:
            recommendation_missing = []

        if not profile or score < 50:
            missing = []
            if profile:
                missing = recommendation_missing
            missing_str = ", ".join(missing) if missing else "plusieurs champs"
            blocked_reason = f"Votre profil est incomplet pour générer des recommandations (minimum 50% requis). Champs manquants : {missing_str}."
        elif not active_cv or not hasattr(active_cv, 'parsed_data'):
            blocked_reason = "Aucun CV analysé n'est disponible."
            
        if blocked_reason:
            return RecommendationDashboardResult(
                recommendations=[],
                is_pending=False,
                is_stale=False,
                latest_run=latest_run,
                blocked_reason=blocked_reason,
            )
            
        is_profile_complete = blocked_reason is None
        
        # Check active recommendations
        active_recs = cls._get_recommendations_by_status(user, "active", limit)
        
        if active_recs:
            return RecommendationDashboardResult(
                recommendations=cls._with_saved_state(user, active_recs),
                is_pending=is_running,
                is_stale=False,
                latest_run=latest_run,
            )
            
        # If no active ones, check stale ones
        stale_recs = cls._get_recommendations_by_status(user, "stale", limit)
        
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
                previous_run_id = latest_run.id if latest_run else None
                cls._enqueue_refresh(user)
                active_recs = cls._get_recommendations_by_status(user, "active", limit)
                if active_recs:
                    return RecommendationDashboardResult(
                        recommendations=cls._with_saved_state(user, active_recs),
                        is_pending=False,
                        is_stale=False,
                        latest_run=RecommendationRun.objects.filter(user=user).order_by("-started_at").first(),
                    )
                latest_run = RecommendationRun.objects.filter(user=user).order_by("-started_at").first()
                if latest_run is None or latest_run.id == previous_run_id:
                    is_pending = True
                else:
                    is_pending = latest_run.status == "running"
                
        if not blocked_reason and not active_recs and not stale_recs and latest_run:
            if latest_run.status == "failed":
                blocked_reason = "La génération a échoué. Veuillez réessayer."
            elif latest_run.status == "success":
                if latest_run.candidate_jobs_count == 0:
                    blocked_reason = "Aucune offre d'emploi active pour le moment."
                elif latest_run.stored_recommendations_count == 0:
                    blocked_reason = "Aucune offre ne correspond à votre profil."
            
        return RecommendationDashboardResult(
            recommendations=[],
            is_pending=is_pending,
            is_stale=False,
            latest_run=latest_run,
            blocked_reason=blocked_reason,
        )
