import uuid
from django.db import models
from django.conf import settings


class MatchResult(models.Model):
    class LlmStatusChoices(models.TextChoices):
        NOT_REQUESTED = "not_requested", "Not Requested"
        DISABLED = "disabled", "Disabled"
        PENDING = "pending", "Pending"
        GENERATED = "generated", "Generated"
        FAILED = "failed", "Failed"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="match_results",
    )
    profile = models.ForeignKey(
        "profiles.CandidateProfile",
        on_delete=models.PROTECT,
    )
    cv_upload = models.ForeignKey(
        "cvs.CVUpload",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    job = models.ForeignKey(
        "jobs.NormalizedJob",
        on_delete=models.PROTECT,
        related_name="match_results",
    )
    
    profile_snapshot_json = models.JSONField(default=dict)
    job_snapshot_json = models.JSONField(default=dict)
    
    fit_score = models.PositiveSmallIntegerField()
    technical_skills_score = models.PositiveSmallIntegerField()
    experience_score = models.PositiveSmallIntegerField()
    role_title_score = models.PositiveSmallIntegerField()
    language_score = models.PositiveSmallIntegerField()
    location_score = models.PositiveSmallIntegerField()
    
    strong_skills_json = models.JSONField(default=list, blank=True)
    missing_required_skills_json = models.JSONField(default=list, blank=True)
    missing_optional_skills_json = models.JSONField(default=list, blank=True)
    risk_flags_json = models.JSONField(default=list, blank=True)
    profile_signals_json = models.JSONField(default=list, blank=True)
    recommended_actions_json = models.JSONField(default=list, blank=True)
    
    llm_explanation_status = models.CharField(
        max_length=50,
        choices=LlmStatusChoices.choices,
        default=LlmStatusChoices.NOT_REQUESTED,
    )
    llm_explanation_text = models.TextField(blank=True)
    scoring_version = models.CharField(max_length=50, default="score_v1")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["public_id"]),
            models.Index(fields=["user", "job"]),
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["job", "fit_score"]),
            models.Index(fields=["fit_score"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["llm_explanation_status"]),
            models.Index(fields=["scoring_version"]),
        ]

    def __str__(self):
        return f"Match {self.public_id} - Score {self.fit_score}"


class QuickMatchSession(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    session_key_hash = models.CharField(max_length=64, db_index=True)
    ip_hash = models.CharField(max_length=64, blank=True, db_index=True)
    job = models.ForeignKey(
        "jobs.NormalizedJob",
        on_delete=models.PROTECT,
        related_name="quick_match_sessions",
    )
    
    entered_skills_json = models.JSONField(default=list)
    normalized_skills_json = models.JSONField(default=list, blank=True)
    experience_level = models.CharField(max_length=50)
    french_level = models.CharField(max_length=50)
    
    estimated_fit_score = models.PositiveSmallIntegerField()
    matched_skills_json = models.JSONField(default=list, blank=True)
    missing_skills_json = models.JSONField(default=list, blank=True)
    risk_flags_json = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["public_id"]),
            models.Index(fields=["session_key_hash"]),
            models.Index(fields=["ip_hash"]),
            models.Index(fields=["job"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["expires_at"]),
            models.Index(fields=["estimated_fit_score"]),
        ]

    def __str__(self):
        return f"QuickMatch {self.public_id} - Est Score {self.estimated_fit_score}"
