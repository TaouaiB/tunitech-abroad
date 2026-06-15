from django.urls import path

from apps.jobs import views

app_name = "jobs"

urlpatterns = [
    path("", views.job_list, name="list"),
    path("<uuid:public_id>/", views.job_detail, name="detail"),
]
