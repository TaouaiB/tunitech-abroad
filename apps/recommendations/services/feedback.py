from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404

from apps.recommendations.models import (
    JobRecommendation,
    RecommendationQualityFeedback,
    RecommendationQualityIssue,
)


class RecommendationFeedbackService:
    @staticmethod
    def record_feedback(user, job_public_id, reason: str, notes: str = "") -> RecommendationQualityFeedback:
        if not user.is_authenticated:
            raise PermissionDenied("User must be authenticated.")

        valid_reasons = {choice.value for choice in RecommendationQualityIssue}
        if reason not in valid_reasons:
            raise ValidationError("Invalid recommendation feedback reason.")

        recommendation = get_object_or_404(
            JobRecommendation,
            user=user,
            job__public_id=job_public_id,
            status="active",
        )
        return RecommendationQualityFeedback.objects.create(
            recommendation=recommendation,
            reason=reason,
            notes=(notes or "").strip(),
            reviewed_by=user,
        )
