from django.urls import path

from apps.jobs import views

app_name = "jobs"

urlpatterns = [
    path("", views.job_list, name="list"),
    path("<uuid:public_id>/", views.job_detail, name="detail"),
    path("<uuid:public_id>/save/", views.save_job, name="save"),
    path("<uuid:public_id>/unsave/", views.unsave_job, name="unsave"),
]
