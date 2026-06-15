from celery import shared_task
from django.contrib.auth import get_user_model
from apps.recommendations.services.recommendation import RecommendationService
from apps.recommendations.services.active_users import ActiveUserRecommendationService

User = get_user_model()

@shared_task
def refresh_user_recommendations(user_id: int, trigger_type: str) -> dict:
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return {"status": "skipped", "reason": "user_not_found"}

    try:
        result = RecommendationService.refresh_for_user(user, trigger_type)
        return {
            "status": "success" if result.skipped_reason is None else "skipped",
            "run_id": result.run_id,
            "created": result.recommendations_created,
            "updated": result.recommendations_updated,
            "stale": result.recommendations_marked_stale,
            "skipped_reason": result.skipped_reason,
        }
    except Exception as e:
        return {"status": "failed", "error": str(e)}

@shared_task
def refresh_active_users_recommendations() -> dict:
    active_users = ActiveUserRecommendationService.get_active_users(days=14)
    count = 0
    for user in active_users:
        refresh_user_recommendations.delay(user.id, "nightly_refresh")
        count += 1
        
    return {"status": "enqueued", "users_enqueued": count}
