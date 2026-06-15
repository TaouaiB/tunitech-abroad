"""
config/urls.py

Root URL configuration — Phase 0 minimal.
Only a health check / debug endpoint is wired here.
Auth, job, profile, CV, and all product URLs will be added in future phases.
"""
from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include


from apps.core.services.health import HealthCheckService

def health(request):
    """
    Detailed health endpoint using HealthCheckService.
    """
    health_data = HealthCheckService.check()
    status_code = 200 if health_data.get("status") == "ok" else 503
    return JsonResponse(health_data, status=status_code)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health, name="health"),
    path("accounts/", include("allauth.urls")),
    path("dashboard/", include("apps.dashboard.urls")),
    path("jobs/", include("apps.jobs.urls")),
    path("", include("apps.matching.urls")),
    path("", include("apps.core.urls")),
    path("", include("apps.notifications.urls")),
    path("", include("apps.privacy.urls")),
]
