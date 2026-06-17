from django.db import models
from django.conf import settings
import uuid

class LLMRequestLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    purpose = models.CharField(max_length=100)
    provider = models.CharField(max_length=50, default="openrouter")
    model_name = models.CharField(max_length=100)
    status = models.CharField(max_length=50) # 'success', 'error'
    prompt_tokens = models.IntegerField(null=True, blank=True)
    completion_tokens = models.IntegerField(null=True, blank=True)
    total_tokens = models.IntegerField(null=True, blank=True)
    latency_ms = models.IntegerField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.purpose} - {self.model_name} ({self.status})"

class JobEnrichment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"
        VALIDATION_ERROR = "validation_error", "Validation error"
        SKIPPED = "skipped", "Skipped"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    job = models.OneToOneField("jobs.NormalizedJob", on_delete=models.CASCADE, related_name="enrichment")

    status = models.CharField(max_length=32, choices=Status.choices, default=Status.PENDING, db_index=True)
    status_reason = models.TextField(blank=True, default="")

    payload_hash = models.CharField(max_length=64, db_index=True)
    model_name = models.CharField(max_length=128, blank=True, default="")

    raw_request_json = models.JSONField(default=dict, blank=True)
    raw_response_text = models.TextField(blank=True, default="")
    raw_response_json = models.JSONField(default=dict, blank=True)
    validated_output_json = models.JSONField(default=dict, blank=True)
    validation_errors_json = models.JSONField(default=list, blank=True)

    prompt_tokens = models.PositiveIntegerField(default=0)
    completion_tokens = models.PositiveIntegerField(default=0)
    total_tokens = models.PositiveIntegerField(default=0)
    estimated_cost_usd = models.DecimalField(max_digits=10, decimal_places=6, default=0)

    attempt_count = models.PositiveSmallIntegerField(default=0)
    last_error = models.TextField(blank=True, default="")
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
