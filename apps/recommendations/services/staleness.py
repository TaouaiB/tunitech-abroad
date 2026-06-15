from django.utils import timezone
from apps.recommendations.models import JobRecommendation

class RecommendationStalenessService:
    @classmethod
    def mark_user_recommendations_stale(cls, user, reason: str) -> int:
        now = timezone.now()
        count = JobRecommendation.objects.filter(
            user=user, 
            status="active"
        ).update(status="stale", updated_at=now)
        
        return count
