from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.shortcuts import redirect
from django.views.generic import View

from apps.recommendations.services.feedback import RecommendationFeedbackService
from apps.recommendations.services.recommendation import RecommendationService

class RefreshRecommendationsView(LoginRequiredMixin, View):
    def post(self, request):
        try:
            result = RecommendationService.refresh_for_user(request.user, trigger_type="manual_refresh")
            if result.skipped_reason == "profile_incomplete":
                messages.error(request, "Veuillez compléter votre profil pour obtenir des recommandations.")
            else:
                messages.success(request, f"Recommandations actualisées ({result.stored_recommendations_count} offres).")
        except Exception as e:
            messages.error(request, "Erreur lors de l'actualisation des recommandations.")

        return redirect("dashboard:recommendations")

class SubmitRecommendationFeedbackView(LoginRequiredMixin, View):
    def post(self, request, public_id):
        reason = request.POST.get("reason")
        notes = request.POST.get("notes", "")

        if reason:
            try:
                RecommendationFeedbackService.record_feedback(request.user, public_id, reason, notes)
                messages.success(request, "Merci pour votre retour sur cette recommandation.")
            except ValidationError:
                messages.error(request, "Le motif de retour sélectionné est invalide.")

        return redirect("dashboard:recommendations")
