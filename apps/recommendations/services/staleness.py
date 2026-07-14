from django.utils import timezone
from apps.recommendations.models import JobRecommendation
from apps.matching.services.policy_version import RECOMMENDATION_VERSION

class RecommendationStalenessService:
    @classmethod
    def mark_outdated_policy_recommendations_stale(cls, user) -> int:
        return JobRecommendation.objects.filter(
            user=user,
            status="active",
        ).exclude(recommendation_version=RECOMMENDATION_VERSION).update(
            status="stale", updated_at=timezone.now()
        )

    @classmethod
    def mark_user_recommendations_stale(cls, user, reason: str) -> int:
        now = timezone.now()
        count = JobRecommendation.objects.filter(
            user=user, 
            status="active"
        ).update(status="stale", updated_at=now)
        
        return count
