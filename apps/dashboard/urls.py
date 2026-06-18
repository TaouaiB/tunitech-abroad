from django.urls import path
from . import views
from apps.notifications import views as notification_views

app_name = "dashboard"

urlpatterns = [
    path("", views.dashboard_home, name="home"),
    path("profile/", views.dashboard_profile, name="profile"),
    path("cv/", views.dashboard_cv, name="cv"),
    path("cv/status/<uuid:public_id>/", views.dashboard_cv_status, name="cv_status"),
    path("recommendations/", views.dashboard_recommendations, name="recommendations"),
    path("saved-jobs/", views.dashboard_saved_jobs, name="saved_jobs"),
    path("email-preferences/", notification_views.email_preferences_view, name="email_preferences"),
    path("account/", views.dashboard_account, name="account"),
    path("account/connections/", views.dashboard_connections, name="connections"),
    path("settings/delete-account/", views.dashboard_delete_account, name="delete_account"),
    path("settings/delete-account/done/", views.dashboard_delete_account_done, name="delete_account_done"),
]
