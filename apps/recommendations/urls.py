from django.urls import path
from . import views

app_name = "recommendations"

urlpatterns = [
    path("refresh/", views.RefreshRecommendationsView.as_view(), name="refresh"),
]
