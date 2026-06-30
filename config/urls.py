"""
config/urls.py

Root URL configuration — Phase 0 minimal.
Only a health check / debug endpoint is wired here.
Auth, job, profile, CV, and all product URLs will be added in future phases.
"""
from django.conf import settings
from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include
from django.views.generic import TemplateView

from apps.core.services.health import HealthCheckService
from apps.analytics.admin_views import admin_operations_view

def health(request):
    """
    Detailed health endpoint using HealthCheckService.
    """
    health_data = HealthCheckService.check()
    status_code = 200 if health_data.get("status") == "ok" else 503
    return JsonResponse(health_data, status=status_code)


urlpatterns = [
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
    path("sitemap.xml", TemplateView.as_view(template_name="sitemap.xml", content_type="application/xml")),
    path(f"{settings.ADMIN_URL}operations/", admin_operations_view, name="admin_operations"),
    path(settings.ADMIN_URL, admin.site.urls),
    path("health/", health, name="health"),
    path("accounts/", include("allauth.urls")),
    path("dashboard/", include("apps.dashboard.urls")),
    path("dashboard/recommendations/", include("apps.recommendations.urls")),
    path("jobs/", include("apps.jobs.urls")),
    path("", include("apps.matching.urls")),
    path("", include("apps.core.urls")),
    path("", include("apps.notifications.urls")),
    path("", include("apps.privacy.urls")),
]
