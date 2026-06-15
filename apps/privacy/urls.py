from django.urls import path
from . import views

app_name = "privacy"

urlpatterns = [
    path("privacy/", views.privacy_policy_view, name="privacy_policy"),
    path("terms/", views.terms_view, name="terms"),
]
