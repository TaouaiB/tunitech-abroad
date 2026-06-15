from django.contrib import admin
from .models import ConsentRecord, DeletionRequest

@admin.register(ConsentRecord)
class ConsentRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'consent_type', 'consent_version', 'accepted', 'created_at')
    search_fields = ('user__email', 'consent_type')
    list_filter = ('consent_type', 'accepted')
    readonly_fields = ('created_at', 'ip_address', 'user_agent')


@admin.register(DeletionRequest)
class DeletionRequestAdmin(admin.ModelAdmin):
    list_display = ("public_id", "user", "status", "requested_at", "processed_at", "attempt_count")
    search_fields = ("public_id", "user__email")
    list_filter = ("status",)
    readonly_fields = ("public_id", "requested_at", "processed_at")
