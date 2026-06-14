from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.dashboard_home, name="home"),
    path("profile/", views.dashboard_profile, name="profile"),
    path("cv/", views.dashboard_cv, name="cv"),
    path("cv/status/<uuid:public_id>/", views.dashboard_cv_status, name="cv_status"),
]
