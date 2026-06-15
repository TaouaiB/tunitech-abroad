from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class ActiveUserRecommendationService:
    @classmethod
    def get_active_users(cls, days: int = 14):
        threshold_date = timezone.now() - timedelta(days=days)
        
        # We need users with last_login >= threshold_date
        # AND usable profile (profile_completion_score >= 50)
        # Note: CV presence isn't strictly necessary if the profile is completed manually.
        
        return User.objects.filter(
            last_login__gte=threshold_date,
            candidate_profile__profile_completion_score__gte=50
        ).distinct()
