from django.urls import path
from apps.matching import views

app_name = "matching"

urlpatterns = [
    path("jobs/<uuid:public_id>/match/", views.CreateMatchView.as_view(), name="create"),
    path("jobs/<uuid:public_id>/quick-match/", views.QuickMatchView.as_view(), name="quick_match"),
    path("dashboard/matches/", views.MatchHistoryView.as_view(), name="history"),
    path("dashboard/matches/<uuid:public_id>/", views.MatchDetailView.as_view(), name="detail"),
]
