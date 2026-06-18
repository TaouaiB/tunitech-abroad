import uuid

from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.db import models
from django.utils.translation import gettext_lazy as _


class SourceType(models.TextChoices):
    API = "api", _("API")
    MANUAL = "manual", _("Manual")
    FIXTURE = "fixture", _("Fixture")


class JobSource(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    base_url = models.URLField(blank=True)
    source_type = models.CharField(max_length=20, choices=SourceType.choices)
    is_active = models.BooleanField(default=True)
    last_successful_sync_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["slug", "is_active", "last_successful_sync_at"]),
        ]

    def __str__(self):
        return self.name


class IngestionRunStatus(models.TextChoices):
    RUNNING = "running", _("Running")
    SUCCESS = "success", _("Success")
    PARTIAL_SUCCESS = "partial_success", _("Partial Success")
    FAILED = "failed", _("Failed")


class TriggerType(models.TextChoices):
    SCHEDULED = "scheduled", _("Scheduled")
    MANUAL_ADMIN = "manual_admin", _("Manual (Admin)")
    STARTUP_FIXTURE = "startup_fixture", _("Startup Fixture")
    RETRY = "retry", _("Retry")


class IngestionRun(models.Model):
    source = models.ForeignKey(JobSource, on_delete=models.PROTECT, related_name="ingestion_runs")
    status = models.CharField(max_length=20, choices=IngestionRunStatus.choices)
    trigger_type = models.CharField(max_length=20, choices=TriggerType.choices)
    started_at = models.DateTimeField()
    finished_at = models.DateTimeField(null=True, blank=True)
    search_params_json = models.JSONField(default=dict, blank=True)
    fetched_count = models.PositiveIntegerField(default=0)
    created_count = models.PositiveIntegerField(default=0)
    updated_count = models.PositiveIntegerField(default=0)
    unchanged_count = models.PositiveIntegerField(default=0)
    marked_stale_count = models.PositiveIntegerField(default=0)
    marked_expired_count = models.PositiveIntegerField(default=0)
    error_count = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["source", "status", "started_at", "finished_at", "trigger_type"]),
        ]

    def __str__(self):
        return f"{self.source.slug} run {self.id} ({self.status})"


class NormalizationStatus(models.TextChoices):
    PENDING = "pending", _("Pending")
    SUCCESS = "success", _("Success")
    FAILED = "failed", _("Failed")
    SKIPPED_UNCHANGED = "skipped_unchanged", _("Skipped (Unchanged)")


class RawJobRecord(models.Model):
    source = models.ForeignKey(JobSource, on_delete=models.PROTECT, related_name="raw_records")
    source_job_id = models.CharField(max_length=255)
    raw_payload_json = models.JSONField()
    payload_hash = models.CharField(max_length=64, db_index=True)
    first_seen_at = models.DateTimeField()
    last_seen_at = models.DateTimeField()
    last_fetched_at = models.DateTimeField()
    source_status = models.CharField(max_length=100, blank=True)
    normalization_status = models.CharField(
        max_length=20, choices=NormalizationStatus.choices, default=NormalizationStatus.PENDING
    )
    normalization_error = models.TextField(blank=True)
    ingestion_run = models.ForeignKey(
        IngestionRun, on_delete=models.SET_NULL, null=True, blank=True, related_name="raw_records"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("source", "source_job_id")
        indexes = [
            models.Index(fields=["source", "source_job_id"]),
            models.Index(fields=["last_seen_at"]),
            models.Index(fields=["last_fetched_at"]),
            models.Index(fields=["normalization_status"]),
            models.Index(fields=["ingestion_run"]),
        ]

    def __str__(self):
        return f"{self.source.slug} - {self.source_job_id}"


class RemoteType(models.TextChoices):
    REMOTE = "remote", _("Remote")
    HYBRID = "hybrid", _("Hybrid")
    ON_SITE = "on_site", _("On-site")
    UNKNOWN = "unknown", _("Unknown")


class JobType(models.TextChoices):
    INTERNSHIP = "internship", _("Internship")
    FULL_TIME_JOB = "full_time_job", _("Full-time Job")
    APPRENTICESHIP = "apprenticeship", _("Apprenticeship")
    CONTRACT = "contract", _("Contract")
    UNKNOWN = "unknown", _("Unknown")


class ExperienceLevel(models.TextChoices):
    INTERNSHIP = "internship", _("Internship")
    JUNIOR = "junior", _("Junior")
    MID_LEVEL = "mid_level", _("Mid-level")
    SENIOR = "senior", _("Senior")
    UNKNOWN = "unknown", _("Unknown")


class JobStatus(models.TextChoices):
    ACTIVE = "active", _("Active")
    STALE = "stale", _("Stale")
    EXPIRED = "expired", _("Expired")
    REMOVED = "removed", _("Removed")
    ARCHIVED = "archived", _("Archived")


class SkillExtractionStatus(models.TextChoices):
    PENDING = "pending", _("Pending")
    SUCCESS = "success", _("Success")
    FAILED = "failed", _("Failed")
    NOT_ENOUGH_TEXT = "not_enough_text", _("Not enough text")


def default_list():
    return []


def default_dict():
    return {}


class NormalizedJob(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    source = models.ForeignKey(JobSource, on_delete=models.PROTECT, related_name="normalized_jobs")
    raw_record = models.OneToOneField(RawJobRecord, on_delete=models.CASCADE, related_name="normalized_job")
    source_job_id = models.CharField(max_length=255)
    title = models.CharField(max_length=500)
    company_name = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=100, default="FR")
    city = models.CharField(max_length=255, blank=True)
    department = models.CharField(max_length=255, blank=True)
    region = models.CharField(max_length=255, blank=True)
    contract_type = models.CharField(max_length=255, blank=True)
    remote_type = models.CharField(max_length=20, choices=RemoteType.choices)
    job_type = models.CharField(max_length=20, choices=JobType.choices)
    experience_level = models.CharField(max_length=20, choices=ExperienceLevel.choices)
    description = models.TextField()
    source_url = models.URLField(max_length=2000, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    first_seen_at = models.DateTimeField()
    last_seen_at = models.DateTimeField()
    last_fetched_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=JobStatus.choices, default=JobStatus.ACTIVE)
    normalization_version = models.CharField(max_length=50, default="ft_v1")
    skill_extraction_status = models.CharField(
        max_length=20, choices=SkillExtractionStatus.choices, default=SkillExtractionStatus.PENDING
    )
    required_skills_json = models.JSONField(default=default_list, blank=True)
    optional_skills_json = models.JSONField(default=default_list, blank=True)
    language_requirements_json = models.JSONField(default=default_dict, blank=True)
    classification_json = models.JSONField(default=default_dict, blank=True)
    skill_signal_quality = models.CharField(max_length=32, default="unknown")
    search_vector = SearchVectorField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("source", "source_job_id")
        indexes = [
            models.Index(fields=["source", "source_job_id"]),
            models.Index(fields=["status"]),
            models.Index(fields=["job_type"]),
            models.Index(fields=["contract_type"]),
            models.Index(fields=["remote_type"]),
            models.Index(fields=["experience_level"]),
            models.Index(fields=["country", "city", "department", "region"]),
            models.Index(fields=["published_at", "expires_at"]),
            models.Index(fields=["last_seen_at", "last_fetched_at"]),
            GinIndex(fields=["search_vector"], name="jobs_normal_search_vector_gin"),
        ]

    def __str__(self):
        return f"{self.title} at {self.company_name or 'Unknown'}"


class RequirementType(models.TextChoices):
    REQUIRED = "required", _("Required")
    OPTIONAL = "optional", _("Optional")
    DETECTED = "detected", _("Detected")
    UNKNOWN = "unknown", _("Unknown")


class SkillSource(models.TextChoices):
    RULE = "rule", _("Rule")
    LLM = "llm", _("LLM")
    ADMIN = "admin", _("Admin")
    SOURCE_API = "source_api", _("Source API")


class NormalizedJobSkill(models.Model):
    job = models.ForeignKey(NormalizedJob, on_delete=models.CASCADE, related_name="job_skills")
    skill = models.ForeignKey("skills.Skill", on_delete=models.PROTECT, related_name="job_requirements")
    requirement_type = models.CharField(max_length=20, choices=RequirementType.choices)
    source = models.CharField(max_length=20, choices=SkillSource.choices)
    confidence = models.DecimalField(max_digits=4, decimal_places=3, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("job", "skill", "requirement_type")
        indexes = [
            models.Index(fields=["job"]),
            models.Index(fields=["skill"]),
            models.Index(fields=["requirement_type"]),
            models.Index(fields=["source"]),
            models.Index(fields=["confidence"]),
        ]

    def __str__(self):
        return f"{self.job.title} requires {self.skill.canonical_name}"


class JobIngestionConfig(models.Model):
    name = models.CharField(max_length=100, unique=True, default="default")
    enabled = models.BooleanField(default=True)
    preset = models.CharField(max_length=50, default="broad_it")
    custom_keywords = models.JSONField(default=list, blank=True)

    limit_per_keyword = models.PositiveIntegerField(default=50)
    max_total_per_run = models.PositiveIntegerField(default=1000)
    max_pages_per_keyword = models.PositiveIntegerField(default=10)

    frequency_minutes = models.PositiveIntegerField(default=240)
    nightly_enabled = models.BooleanField(default=True)
    nightly_max_total = models.PositiveIntegerField(default=2000)

    normalize_after_fetch = models.BooleanField(default=True)
    enrichment_enabled = models.BooleanField(default=True)
    enrich_every_fetched_it_job = models.BooleanField(default=True)
    enrichment_limit_per_run = models.PositiveIntegerField(default=1000)
    daily_enrichment_limit = models.PositiveIntegerField(default=1000)

    expire_after_days = models.PositiveIntegerField(default=21)
    mark_missing_as_stale_after_days = models.PositiveIntegerField(default=14)

    dry_run = models.BooleanField(default=False)
    last_run_at = models.DateTimeField(null=True, blank=True)
    last_success_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True, default="")

    def __str__(self):
        return self.name


class JobIngestionRun(models.Model):
    config = models.ForeignKey(JobIngestionConfig, on_delete=models.SET_NULL, null=True, blank=True)
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=32, choices=[
        ('running', 'Running'),
        ('success', 'Success'),
        ('partial_success', 'Partial Success'),
        ('failed', 'Failed'),
    ])
    trigger = models.CharField(max_length=32)
    preset = models.CharField(max_length=50, default="broad_it")
    keywords_json = models.JSONField(default=list, blank=True)
    limit_per_keyword = models.PositiveIntegerField(default=50)
    max_total = models.PositiveIntegerField(default=1000)

    fetched_count = models.PositiveIntegerField(default=0)
    created_raw_count = models.PositiveIntegerField(default=0)
    updated_raw_count = models.PositiveIntegerField(default=0)
    normalized_count = models.PositiveIntegerField(default=0)
    duplicates_skipped_count = models.PositiveIntegerField(default=0)
    expired_count = models.PositiveIntegerField(default=0)
    enrichment_queued_count = models.PositiveIntegerField(default=0)
    enrichment_skipped_count = models.PositiveIntegerField(default=0)
    error_count = models.PositiveIntegerField(default=0)
    error_summary = models.TextField(blank=True, default="")

    def __str__(self):
        return f"Run {self.id} ({self.status}) for config {self.config_id}"
