"""
config/urls.py

Root URL configuration — Phase 0 minimal.
Only a health check / debug endpoint is wired here.
Auth, job, profile, CV, and all product URLs will be added in future phases.
"""
from django.http import JsonResponse
from django.urls import path


def health(request):
    """
    Minimal health endpoint.

    Returns 200 and a JSON payload so local infrastructure can be verified
    without needing a real frontend.
    """
    return JsonResponse({"status": "ok", "phase": 0})


urlpatterns = [
    path("health/", health, name="health"),
]
