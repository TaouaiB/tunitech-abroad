from django.contrib import admin
from .models import JobEnrichment, LLMRequestLog

@admin.register(LLMRequestLog)
class LLMRequestLogAdmin(admin.ModelAdmin):
    list_display = ("purpose", "model_name", "status", "user", "total_tokens", "latency_ms", "created_at")
    list_filter = ("status", "purpose", "provider")
    search_fields = ("user__email", "purpose", "model_name")
    readonly_fields = ("created_at", "prompt_tokens", "completion_tokens", "total_tokens", "latency_ms", "error_message")


@admin.register(JobEnrichment)
class JobEnrichmentAdmin(admin.ModelAdmin):
    list_display = (
        "public_id",
        "job",
        "status",
        "model_name",
        "total_tokens",
        "estimated_cost_usd",
        "attempt_count",
        "created_at",
    )
    list_filter = ("status", "model_name", "created_at", "completed_at")
    search_fields = ("public_id", "job__title", "job__company_name", "payload_hash")
    readonly_fields = (
        "public_id",
        "job",
        "status",
        "status_reason",
        "payload_hash",
        "model_name",
        "validated_output_json",
        "validation_errors_json",
        "prompt_tokens",
        "completion_tokens",
        "total_tokens",
        "estimated_cost_usd",
        "attempt_count",
        "last_error",
        "started_at",
        "completed_at",
        "created_at",
        "updated_at",
    )
    exclude = ("raw_request_json", "raw_response_text", "raw_response_json")

    def has_add_permission(self, request):
        return False
