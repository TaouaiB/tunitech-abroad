from django.contrib import admin
from django.contrib import messages
from django.db.models import Count
from apps.jobs.models import (
    JobSource,
    IngestionRun,
    RawJobRecord,
    NormalizedJob,
    NormalizedJobSkill,
    JobQualityFeedback,
    JobIngestionConfig,
    JobIngestionRun,
    JobIngestionQueryRun,
)
from apps.jobs.services.anomaly_review import LOW_CONFIDENCE_THRESHOLD
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
        "target_daily_fetch_count",
        "max_jobs_per_run",
        "last_run_at",
        "last_success_at",
    )
    list_filter = ("enabled", "preset", "normalize_after_fetch", "enrichment_enabled", "enrich_every_fetched_it_job")
    search_fields = ("name", "preset")
    fieldsets = (
        (None, {"fields": ("name", "enabled", "preset", "custom_keywords")}),
        (
            "Fetch limits",
            {
                "fields": (
                    "target_daily_fetch_count",
                    "max_jobs_per_run",
                    "max_pages_per_query",
                    "page_size",
                    "queries_json",
                    "limit_per_keyword",
                    "max_total_per_run",
                    "max_pages_per_keyword",
                )
            },
        ),
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
        (
            "Freshness and expiry",
            {
                "fields": (
                    "stale_after_hours",
                    "removed_after_hours",
                    "expire_grace_hours",
                    "expire_after_days",
                    "mark_missing_as_stale_after_days",
                )
            },
        ),
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
    readonly_fields = ("started_at", "finished_at", "public_id", "query_stats_json", "config_snapshot_json")


@admin.register(JobIngestionQueryRun)
class JobIngestionQueryRunAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "ingestion_run",
        "query_label",
        "fetched_count",
        "created_count",
        "updated_count",
        "unchanged_count",
        "skipped_count",
        "error_count",
        "started_at",
    )
    list_filter = ("query_label", "error_count")
    search_fields = ("query_label", "error_message")
    readonly_fields = (
        "ingestion_run",
        "query_label",
        "params_json",
        "requested_range_json",
        "fetched_count",
        "created_count",
        "updated_count",
        "unchanged_count",
        "skipped_count",
        "error_count",
        "error_message",
        "started_at",
        "finished_at",
        "created_at",
    )


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

@admin.action(description="Re-run deterministic skill extraction")
def re_extract_skills_action(modeladmin, request, queryset):
    from apps.jobs.services.admin_operations import JobAdminOperationsService

    count = JobAdminOperationsService.re_extract_skills(queryset.values_list("id", flat=True))
    modeladmin.message_user(request, f"Re-extracted skills for {count} jobs.", messages.SUCCESS)

@admin.action(description="Rematerialize skills from existing enrichment")
def rematerialize_skills_action(modeladmin, request, queryset):
    from apps.jobs.services.admin_operations import JobAdminOperationsService

    count = JobAdminOperationsService.rematerialize_from_enrichment(queryset.values_list("id", flat=True))
    modeladmin.message_user(request, f"Rematerialized skills for {count} jobs.", messages.SUCCESS)

@admin.action(description="Recover zero-skill jobs (Rule-based)")
def recover_zero_skill_jobs_action(modeladmin, request, queryset):
    from apps.jobs.services.zero_skill_recovery import ZeroSkillJobRecoveryService
    result = ZeroSkillJobRecoveryService.recover_queryset(queryset)
    modeladmin.message_user(
        request,
        f"Inspected: {result['jobs_inspected']}, Recovered: {result['recovered_jobs']} jobs ({result['skills_created']} skills created), Skipped: {result['skipped_excluded']}, Still zero-skill: {result['still_zero_skill']}.",
        messages.SUCCESS
    )

class NormalizedJobSkillInline(admin.TabularInline):
    model = NormalizedJobSkill
    extra = 1
    fields = ('skill', 'requirement_type', 'source', 'confidence')
    autocomplete_fields = ('skill',)


class JobQualityFeedbackInline(admin.TabularInline):
    model = JobQualityFeedback
    extra = 0
    fields = ("reason", "notes", "reviewed_by", "created_at")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("reviewed_by",)


class NoSkillsFilter(admin.SimpleListFilter):
    title = "Has materialized skills"
    parameter_name = "has_skills"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Yes"),
            ("no", "No (zero skills)"),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.annotate(_skill_count=Count("job_skills")).filter(_skill_count__gt=0)
        if self.value() == "no":
            return queryset.annotate(_skill_count=Count("job_skills")).filter(_skill_count=0)
        return queryset


class ActiveJobFilter(admin.SimpleListFilter):
    title = "Active review jobs"
    parameter_name = "active_review"

    def lookups(self, request, model_admin):
        return (
            ("active", "Active only"),
            ("inactive", "Inactive only"),
        )

    def queryset(self, request, queryset):
        from apps.jobs.models import JobStatus

        if self.value() == "active":
            return queryset.filter(status=JobStatus.ACTIVE)
        if self.value() == "inactive":
            return queryset.exclude(status=JobStatus.ACTIVE)
        return queryset


class SkillSignalQualityFilter(admin.SimpleListFilter):
    title = "Skill signal quality"
    parameter_name = "skill_signal_quality_review"

    def lookups(self, request, model_admin):
        return (
            ("strong_partial", "Strong or partial"),
            ("strong", "Strong"),
            ("partial", "Partial"),
            ("weak", "Generic/missing/unknown"),
        )

    def queryset(self, request, queryset):
        if self.value() == "strong_partial":
            return queryset.filter(skill_signal_quality__in=["strong", "partial"])
        if self.value() == "strong":
            return queryset.filter(skill_signal_quality="strong")
        if self.value() == "partial":
            return queryset.filter(skill_signal_quality="partial")
        if self.value() == "weak":
            return queryset.filter(skill_signal_quality__in=["generic_only", "missing", "unknown", ""])
        return queryset


class GenericOnlyJobFilter(admin.SimpleListFilter):
    title = "Generic-only skills"
    parameter_name = "generic_only_review"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Generic-only signal"),
            ("no", "Not generic-only"),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(skill_signal_quality="generic_only")
        if self.value() == "no":
            return queryset.exclude(skill_signal_quality="generic_only")
        return queryset


class HiddenOrExcludedJobFilter(admin.SimpleListFilter):
    title = "Hidden/excluded reason"
    parameter_name = "hidden_excluded_review"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Hidden/excluded/reasoned"),
            ("non_it", "Excluded non-IT"),
            ("quality_issue", "Has quality issue"),
        )

    def queryset(self, request, queryset):
        from django.db.models import Q
        from apps.jobs.models import JobStatus

        hidden_statuses = [JobStatus.STALE, JobStatus.EXPIRED, JobStatus.REMOVED, JobStatus.ARCHIVED]
        if self.value() == "yes":
            return queryset.filter(
                Q(status__in=hidden_statuses) | Q(quality_issue__gt="") | Q(skill_signal_quality="excluded_non_it")
            )
        if self.value() == "non_it":
            return queryset.filter(skill_signal_quality="excluded_non_it")
        if self.value() == "quality_issue":
            return queryset.filter(quality_issue__gt="")
        return queryset

@admin.register(NormalizedJob)
class NormalizedJobAdmin(admin.ModelAdmin):
    list_display = (
        "public_id",
        "title",
        "company_name",
        "location",
        "status",
        "source",
        "source_job_id",
        "skill_signal_quality",
        "skill_extraction_status",
        "enrichment_status",
        "quality_issue",
        "job_skill_count",
        "last_seen_at",
        "created_at",
    )
    list_filter = (
        NoSkillsFilter,
        ActiveJobFilter,
        SkillSignalQualityFilter,
        GenericOnlyJobFilter,
        HiddenOrExcludedJobFilter,
        "status",
        "skill_extraction_status",
        "source",
        "job_type",
        "remote_type",
        "experience_level",
        "quality_issue",
    )
    search_fields = ("title", "company_name", "source_job_id", "public_id", "source__name", "source__slug")
    readonly_fields = (
        "public_id",
        "source_job_id",
        "skill_signal_quality",
        "skill_extraction_status",
        "quality_issue",
        "created_at",
        "updated_at",
        "first_seen_at",
        "last_seen_at",
        "last_fetched_at",
    )
    actions = [mark_jobs_stale, mark_jobs_expired, queue_selected_eligible_job_enrichments, re_extract_skills_action, rematerialize_skills_action, recover_zero_skill_jobs_action]
    inlines = [NormalizedJobSkillInline, JobQualityFeedbackInline]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related("source", "enrichment").annotate(job_skill_count_value=Count("job_skills"))

    @admin.display(ordering="job_skill_count_value", description="Job skill count")
    def job_skill_count(self, obj):
        return obj.job_skill_count_value

    @admin.display(ordering="enrichment__status", description="Enrichment status")
    def enrichment_status(self, obj):
        enrichment = getattr(obj, "enrichment", None)
        return enrichment.status if enrichment else "-"


class LowConfidenceJobSkillFilter(admin.SimpleListFilter):
    title = "Low confidence"
    parameter_name = "low_confidence_review"

    def lookups(self, request, model_admin):
        return (
            ("yes", f"Below {LOW_CONFIDENCE_THRESHOLD}"),
            ("missing", "Missing confidence"),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(confidence__isnull=False, confidence__lt=LOW_CONFIDENCE_THRESHOLD)
        if self.value() == "missing":
            return queryset.filter(confidence__isnull=True)
        return queryset


@admin.register(NormalizedJobSkill)
class NormalizedJobSkillAdmin(admin.ModelAdmin):
    list_display = ("job_public_id", "job", "skill", "requirement_type", "source", "confidence", "job_source")
    list_filter = (LowConfidenceJobSkillFilter, "requirement_type", "source", "job__source")
    search_fields = (
        "job__title",
        "job__company_name",
        "job__public_id",
        "job__source_job_id",
        "skill__canonical_name",
    )
    readonly_fields = ("created_at",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("job", "job__source", "skill")

    @admin.display(ordering="job__public_id", description="Job public ID")
    def job_public_id(self, obj):
        return obj.job.public_id

    @admin.display(ordering="job__source", description="Job source")
    def job_source(self, obj):
        return obj.job.source


@admin.register(JobQualityFeedback)
class JobQualityFeedbackAdmin(admin.ModelAdmin):
    list_display = ("job_public_id", "job", "reason", "reviewed_by", "created_at")
    list_filter = ("reason", "created_at")
    search_fields = ("job__public_id", "job__source_job_id", "job__title", "job__company_name", "notes", "reviewed_by__email")
    autocomplete_fields = ("job", "reviewed_by")
    readonly_fields = ("created_at",)

    @admin.display(ordering="job__public_id", description="Job public ID")
    def job_public_id(self, obj):
        return obj.job.public_id
