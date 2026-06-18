from django.contrib import admin
from django.contrib import messages
from apps.jobs.models import (
    JobSource,
    IngestionRun,
    RawJobRecord,
    NormalizedJob,
    NormalizedJobSkill,
    JobIngestionConfig,
    JobIngestionRun,
)
from apps.jobs.tasks import normalize_raw_job_record


@admin.action(description="Reprocess selected raw jobs")
def reprocess_raw_jobs(modeladmin, request, queryset):
    count = 0
    for record in queryset:
        normalize_raw_job_record.delay(record.id)
        count += 1
    modeladmin.message_user(request, f"Queued {count} raw jobs for reprocessing.", messages.SUCCESS)

@admin.register(JobSource)
class JobSourceAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "source_type", "is_active", "last_successful_sync_at")
    list_filter = ("source_type", "is_active")
    search_fields = ("name", "slug")


@admin.register(IngestionRun)
class IngestionRunAdmin(admin.ModelAdmin):
    list_display = ("id", "source", "status", "trigger_type", "started_at", "fetched_count", "error_count")
    list_filter = ("status", "trigger_type", "source")
    search_fields = ("source__name",)
    readonly_fields = ("started_at", "finished_at", "created_at")


@admin.register(JobIngestionConfig)
class JobIngestionConfigAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "enabled",
        "preset",
        "frequency_minutes",
        "normalize_after_fetch",
        "enrichment_enabled",
        "enrich_every_fetched_it_job",
        "enrichment_limit_per_run",
        "daily_enrichment_limit",
        "last_run_at",
        "last_success_at",
    )
    list_filter = ("enabled", "preset", "normalize_after_fetch", "enrichment_enabled", "enrich_every_fetched_it_job")
    search_fields = ("name", "preset")
    fieldsets = (
        (None, {"fields": ("name", "enabled", "preset", "custom_keywords")}),
        ("Fetch limits", {"fields": ("limit_per_keyword", "max_total_per_run", "max_pages_per_keyword")}),
        ("Schedule", {"fields": ("frequency_minutes", "nightly_enabled", "nightly_max_total")}),
        (
            "Processing",
            {
                "fields": (
                    "normalize_after_fetch",
                    "enrichment_enabled",
                    "enrich_every_fetched_it_job",
                    "enrichment_limit_per_run",
                    "daily_enrichment_limit",
                )
            },
        ),
        ("Expiry", {"fields": ("expire_after_days", "mark_missing_as_stale_after_days")}),
        ("Runtime", {"fields": ("dry_run", "last_run_at", "last_success_at", "last_error")}),
    )
    readonly_fields = ("last_run_at", "last_success_at", "last_error")


@admin.register(JobIngestionRun)
class JobIngestionRunAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "config",
        "status",
        "trigger",
        "started_at",
        "fetched_count",
        "normalized_count",
        "duplicates_skipped_count",
        "enrichment_queued_count",
        "enrichment_skipped_count",
        "error_count",
    )
    list_filter = ("status", "trigger", "config")
    search_fields = ("public_id",)
    readonly_fields = ("started_at", "finished_at", "public_id")


@admin.register(RawJobRecord)
class RawJobRecordAdmin(admin.ModelAdmin):
    list_display = ("source_job_id", "source", "normalization_status", "first_seen_at", "last_seen_at")
    list_filter = ("normalization_status", "source")
    search_fields = ("source_job_id", "payload_hash")
    readonly_fields = ("created_at", "updated_at", "payload_hash", "normalization_error")
    actions = [reprocess_raw_jobs]


@admin.action(description="Mark selected jobs as stale")
def mark_jobs_stale(modeladmin, request, queryset):
    from apps.jobs.models import JobStatus
    from apps.jobs.services.admin_operations import JobAdminOperationsService

    updated = JobAdminOperationsService.mark_selected_jobs_status(queryset.values_list("id", flat=True), JobStatus.STALE)
    modeladmin.message_user(request, f"{updated} jobs marked as stale.", messages.SUCCESS)

@admin.action(description="Mark selected jobs as expired")
def mark_jobs_expired(modeladmin, request, queryset):
    from apps.jobs.models import JobStatus
    from apps.jobs.services.admin_operations import JobAdminOperationsService

    updated = JobAdminOperationsService.mark_selected_jobs_status(queryset.values_list("id", flat=True), JobStatus.EXPIRED)
    modeladmin.message_user(request, f"{updated} jobs marked as expired.", messages.SUCCESS)

@admin.action(description="Queue selected eligible enrichments")
def queue_selected_eligible_job_enrichments(modeladmin, request, queryset):
    from apps.jobs.services.admin_operations import JobAdminOperationsService

    queued = JobAdminOperationsService.queue_selected_eligible_enrichments(queryset.values_list("id", flat=True))
    if queued:
        modeladmin.message_user(request, f"Queued {queued} eligible job enrichments.", messages.SUCCESS)
    else:
        modeladmin.message_user(request, "No selected jobs were eligible for enrichment queueing.", messages.WARNING)

@admin.register(NormalizedJob)
class NormalizedJobAdmin(admin.ModelAdmin):
    list_display = ("title", "company_name", "job_type", "remote_type", "experience_level", "country", "city", "status", "source_job_id")
    list_filter = ("status", "job_type", "remote_type", "experience_level", "source", "country")
    search_fields = ("title", "company_name", "source_job_id", "public_id")
    readonly_fields = ("public_id", "created_at", "updated_at", "first_seen_at", "last_seen_at", "last_fetched_at")
    actions = [mark_jobs_stale, mark_jobs_expired, queue_selected_eligible_job_enrichments]


@admin.register(NormalizedJobSkill)
class NormalizedJobSkillAdmin(admin.ModelAdmin):
    list_display = ("job", "skill", "requirement_type", "source")
    list_filter = ("requirement_type", "source")
    search_fields = ("job__title", "skill__canonical_name")
    readonly_fields = ("created_at",)
