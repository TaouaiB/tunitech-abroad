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
from django.utils import timezone
from django.views.generic import TemplateView
from django.shortcuts import redirect
from allauth.account import views as allauth_views

from apps.core.services.health import HealthCheckService
from apps.analytics.admin_views import admin_operations_view, data_quality_dashboard_view
from apps.cvs.admin_views import admin_cv_download

import logging


logger = logging.getLogger(__name__)


def health(request):
    """
    Detailed health endpoint using HealthCheckService.
    """
    try:
        health_data = HealthCheckService.check()
    except Exception:
        logger.error("Health endpoint: health check service failed.")
        health_data = {
            "ok": False,
            "service": "health_check",
            "generated_at": timezone.now().isoformat(),
            "scope": {"source": "admin_monitoring"},
            "counts": {},
            "statuses": {
                "overall": "critical",
                "database": "unknown",
                "redis": "unknown",
                "jobs": "unknown",
                "celery": "unknown",
            },
            "reasons": {},
            "top_items": [],
            "warnings": [],
            "errors": ["health_check_unavailable"],
            "recommended_actions": ["Check application health-check service logs."],
            "artifacts": {},
            "status": "critical",
            "database": "unknown",
            "redis": "unknown",
            "jobs": "unknown",
            "details": {},
        }
    status_code = 200 if health_data.get("ok") is True else 503
    return JsonResponse(health_data, status=status_code)


def signup_redirect_wrapper(request, *args, **kwargs):
    """
    Delegate to allauth signup view.
    """
    return allauth_views.signup(request, *args, **kwargs)

urlpatterns = [
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
    path("sitemap.xml", TemplateView.as_view(template_name="sitemap.xml", content_type="application/xml")),
    path(f"{settings.ADMIN_URL}operations/", admin_operations_view, name="admin_operations"),
    path(f"{settings.ADMIN_URL}data-quality/", data_quality_dashboard_view, name="admin_data_quality"),
    path(f"{settings.ADMIN_URL}cv-download/<uuid:public_id>/", admin_cv_download, name="admin_cv_download"),
    path(settings.ADMIN_URL, admin.site.urls),
    path("health/", health, name="health"),
    path("accounts/signup/", signup_redirect_wrapper, name="account_signup"),
    path("accounts/", include("allauth.urls")),
    path("dashboard/", include("apps.dashboard.urls")),
    path("dashboard/recommendations/", include("apps.recommendations.urls")),
    path("jobs/", include("apps.jobs.urls")),
    path("", include("apps.matching.urls")),
    path("", include("apps.core.urls")),
    path("", include("apps.notifications.urls")),
    path("", include("apps.privacy.urls")),
]
