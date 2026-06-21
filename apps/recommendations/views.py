from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.contrib import messages
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
