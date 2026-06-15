from django.conf import settings
from django.db import models


class JobRecommendation(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("stale", "Stale"),
        ("dismissed", "Dismissed"),
        ("expired_job", "Expired Job"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    profile = models.ForeignKey("profiles.CandidateProfile", on_delete=models.CASCADE)
    cv_upload = models.ForeignKey(
        "cvs.CVUpload", null=True, blank=True, on_delete=models.SET_NULL
    )
    job = models.ForeignKey("jobs.NormalizedJob", on_delete=models.CASCADE)

    fit_score = models.PositiveSmallIntegerField()
    ranking_score = models.DecimalField(max_digits=6, decimal_places=2)
    rank = models.PositiveIntegerField()

    strong_skills_json = models.JSONField(default=list, blank=True)
    missing_skills_json = models.JSONField(default=list, blank=True)
    risk_flags_json = models.JSONField(default=list, blank=True)
    profile_signals_json = models.JSONField(default=list, blank=True)

    reason_summary = models.TextField(blank=True)
    recommendation_version = models.CharField(max_length=32, default="reco_v1")

    computed_at = models.DateTimeField()
    status = models.CharField(max_length=32, choices=STATUS_CHOICES)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "job", "recommendation_version"],
                name="unique_user_job_version",
            )
        ]
        indexes = [
            models.Index(fields=["user", "status", "-ranking_score"]),
            models.Index(fields=["user", "rank"]),
            models.Index(fields=["job", "status"]),
            models.Index(fields=["computed_at"]),
            models.Index(fields=["recommendation_version"]),
        ]

    def __str__(self):
        return f"Rec for {self.user} - {self.job} (Rank: {self.rank})"


class RecommendationRun(models.Model):
    TRIGGER_CHOICES = [
        ("cv_uploaded", "CV Uploaded"),
        ("cv_replaced", "CV Replaced"),
        ("profile_updated", "Profile Updated"),
        ("new_jobs_imported", "New Jobs Imported"),
        ("dashboard_stale_refresh", "Dashboard Stale Refresh"),
        ("nightly_refresh", "Nightly Refresh"),
        ("manual_admin", "Manual Admin"),
    ]
    STATUS_CHOICES = [
        ("running", "Running"),
        ("success", "Success"),
        ("partial_success", "Partial Success"),
        ("failed", "Failed"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    trigger_type = models.CharField(max_length=64, choices=TRIGGER_CHOICES)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES)

    started_at = models.DateTimeField()
    finished_at = models.DateTimeField(null=True, blank=True)

    candidate_jobs_count = models.PositiveIntegerField(default=0)
    scored_jobs_count = models.PositiveIntegerField(default=0)
    stored_recommendations_count = models.PositiveIntegerField(default=0)

    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Run {self.id} ({self.status}) - {self.trigger_type}"


class SavedJob(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    job = models.ForeignKey("jobs.NormalizedJob", on_delete=models.CASCADE)
    notes = models.TextField(blank=True)
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "job"], name="unique_saved_job")
        ]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["job"]),
            models.Index(fields=["saved_at"]),
        ]

    def __str__(self):
        return f"{self.user} saved {self.job}"
