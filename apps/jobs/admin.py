from django.contrib import admin
from apps.jobs.models import (
    JobSource,
    IngestionRun,
    RawJobRecord,
    NormalizedJob,
    NormalizedJobSkill,
)


@admin.register(JobSource)
class JobSourceAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "source_type", "is_active", "last_successful_sync_at")
    list_filter = ("source_type", "is_active")
    search_fields = ("name", "slug")


@admin.register(IngestionRun)
class IngestionRunAdmin(admin.ModelAdmin):
    list_display = ("id", "source", "status", "trigger_type", "started_at", "fetched_count")
    list_filter = ("status", "trigger_type", "source")
    search_fields = ("source__name",)
    readonly_fields = ("started_at", "finished_at", "created_at")


@admin.register(RawJobRecord)
class RawJobRecordAdmin(admin.ModelAdmin):
    list_display = ("source_job_id", "source", "normalization_status", "first_seen_at")
    list_filter = ("normalization_status", "source")
    search_fields = ("source_job_id",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(NormalizedJob)
class NormalizedJobAdmin(admin.ModelAdmin):
    list_display = ("title", "company_name", "job_type", "remote_type", "status", "source_job_id")
    list_filter = ("status", "job_type", "remote_type", "experience_level", "source")
    search_fields = ("title", "company_name", "source_job_id", "public_id")
    readonly_fields = ("public_id", "created_at", "updated_at")


@admin.register(NormalizedJobSkill)
class NormalizedJobSkillAdmin(admin.ModelAdmin):
    list_display = ("job", "skill", "requirement_type", "source")
    list_filter = ("requirement_type", "source")
    search_fields = ("job__title", "skill__canonical_name")
    readonly_fields = ("created_at",)
