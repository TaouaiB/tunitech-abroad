# Data Model Requirements

## Preferred model: JobEnrichment

Create a dedicated model instead of adding too many fields directly to `NormalizedJob`.

Suggested model:

```python
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
```

## Why dedicated model

A dedicated enrichment model is cleaner because:

- it tracks status and retries cleanly
- it stores raw/validated output separately
- it tracks token/cost metadata
- it avoids bloating the primary job table
- it supports monitoring/admin review

## NormalizedJob fields allowed

Add small helper fields only if needed:

- `has_successful_enrichment` optional denormalized BooleanField, default False
- or avoid this and always use `select_related("enrichment")`

Do not remove existing `required_skills_json`, `optional_skills_json`, or `NormalizedJobSkill` in this phase.

## Usage rule

Matching should use enrichment only when:

- feature flag `JOB_RECOMMENDATIONS_USE_ENRICHED_DATA=True`
- job has `enrichment.status == success`
- `validated_output_json` passes expected shape

Otherwise fallback to deterministic extracted skills.
