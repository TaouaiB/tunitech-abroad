# Admin Configuration Design

Add a database-backed configuration model, for example in `apps.jobs.models`:

```python
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
    enqueue_enrichment = models.BooleanField(default=True)
    enrich_every_fetched_it_job = models.BooleanField(default=True)
    enrichment_limit_per_run = models.PositiveIntegerField(default=1000)

    expire_after_days = models.PositiveIntegerField(default=21)
    mark_missing_as_stale_after_days = models.PositiveIntegerField(default=14)

    dry_run = models.BooleanField(default=False)
    last_run_at = models.DateTimeField(null=True, blank=True)
    last_success_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True, default="")
```

The exact fields can be adjusted to existing model style, but all required behavior must remain.

Add a run log model, for example:

```python
class JobIngestionRun(models.Model):
    config = models.ForeignKey(JobIngestionConfig, on_delete=models.SET_NULL, null=True, blank=True)
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=32, choices=[...])
    trigger = models.CharField(max_length=32)  # manual, command, celery, cron, admin
    preset = models.CharField(max_length=50, default="broad_it")
    keywords_json = models.JSONField(default=list, blank=True)
    limit_per_keyword = models.PositiveIntegerField(default=50)
    max_total = models.PositiveIntegerField(default=1000)

    fetched_count = models.PositiveIntegerField(default=0)
    created_raw_count = models.PositiveIntegerField(default=0)
    updated_raw_count = models.PositiveIntegerField(default=0)
    normalized_count = models.PositiveIntegerField(default=0)
    skipped_duplicate_count = models.PositiveIntegerField(default=0)
    expired_count = models.PositiveIntegerField(default=0)
    enrichment_queued_count = models.PositiveIntegerField(default=0)
    enrichment_skipped_count = models.PositiveIntegerField(default=0)
    error_count = models.PositiveIntegerField(default=0)
    error_summary = models.TextField(blank=True, default="")
```

## Admin behavior

Register both models in Django admin.

Admin must be able to:

- View and edit config.
- See last run status.
- See counts for fetched/created/updated/normalized/enriched/expired.
- Disable ingestion.
- Reduce frequency.
- Reduce limits.
- Disable enrichment separately.
- Trigger manual sync via admin action if feasible.

Admin action must enqueue a background task or call a service safely; do not run a huge API loop inside a web request.
