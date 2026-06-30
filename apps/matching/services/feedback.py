from django.core.exceptions import PermissionDenied, ValidationError

from apps.matching.models import MatchQualityFeedback, MatchQualityIssue
from apps.matching.services.match_result import MatchResultService


class MatchFeedbackService:
    @staticmethod
    def record_feedback(user, match_public_id, reason: str, notes: str = "") -> MatchQualityFeedback:
        if not user.is_authenticated:
            raise PermissionDenied("User must be authenticated.")

        valid_reasons = {choice.value for choice in MatchQualityIssue}
        if reason not in valid_reasons:
            raise ValidationError("Invalid match feedback reason.")

        match_result = MatchResultService.get_user_match(user, match_public_id)
        return MatchQualityFeedback.objects.create(
            match_result=match_result,
            reason=reason,
            notes=(notes or "").strip(),
            reviewed_by=user,
        )
