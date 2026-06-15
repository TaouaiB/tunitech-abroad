from django.contrib import admin
from .models import EmailBatch, EmailEvent, EmailPreference, EmailUnsubscribeToken

@admin.register(EmailPreference)
class EmailPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'product_updates_enabled', 'weekly_digest_enabled', 'cv_analysis_email_enabled')
    search_fields = ('user__email', 'user__username')
    list_filter = ('product_updates_enabled', 'weekly_digest_enabled', 'cv_analysis_email_enabled')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(EmailBatch)
class EmailBatchAdmin(admin.ModelAdmin):
    list_display = (
        "public_id",
        "batch_type",
        "status",
        "period_start",
        "period_end",
        "sent_count",
        "failed_count",
        "skipped_count",
    )
    list_filter = ("batch_type", "status")
    readonly_fields = ("public_id", "created_at", "updated_at")
    search_fields = ("public_id",)


@admin.register(EmailEvent)
class EmailEventAdmin(admin.ModelAdmin):
    list_display = (
        "public_id",
        "email_type",
        "status",
        "to_email",
        "subject",
        "created_at",
    )
    list_filter = ("email_type", "status")
    readonly_fields = ("public_id", "created_at", "updated_at", "queued_at", "sent_at", "failed_at")
    search_fields = ("public_id", "to_email", "subject", "idempotency_key", "user__email")


@admin.register(EmailUnsubscribeToken)
class EmailUnsubscribeTokenAdmin(admin.ModelAdmin):
    list_display = ("public_id", "user", "email_type", "used_at", "created_at", "expires_at")
    list_filter = ("email_type", "used_at")
    readonly_fields = ("public_id", "created_at", "used_at")
    search_fields = ("public_id", "user__email", "user__username")
    exclude = ("token",)
