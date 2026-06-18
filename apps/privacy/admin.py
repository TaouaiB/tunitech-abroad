from django.contrib import admin
from .models import ConsentRecord, DeletionRequest

@admin.register(ConsentRecord)
class ConsentRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'consent_type', 'consent_version', 'accepted', 'created_at')
    search_fields = ('user__email', 'consent_type')
    list_filter = ('consent_type', 'accepted')
    readonly_fields = ('created_at', 'ip_address', 'user_agent')


from django.contrib import messages
from apps.privacy.tasks import process_account_deletion

@admin.action(description="Process selected deletion requests")
def process_deletion_requests(modeladmin, request, queryset):
    count = 0
    for deletion_request in queryset:
        if deletion_request.status in ['pending', 'failed']:
            process_account_deletion.delay(deletion_request.id)
            count += 1
    modeladmin.message_user(request, f"Queued {count} deletion requests for processing.", messages.SUCCESS)

@admin.register(DeletionRequest)
class DeletionRequestAdmin(admin.ModelAdmin):
    list_display = ("public_id", "user", "status", "requested_at", "processed_at", "attempt_count")
    search_fields = ("public_id", "user__email")
    list_filter = ("status",)
    readonly_fields = ("public_id", "requested_at", "processed_at")
    actions = [process_deletion_requests]
