from django.urls import path
from . import views

app_name = "notifications"

urlpatterns = [
    path("dashboard/email-preferences/", views.email_preferences_view, name="email_preferences"),
    path("email/unsubscribe/<uuid:token>/", views.unsubscribe_view, name="unsubscribe"),
]
