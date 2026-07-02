from django.contrib import admin
from .models import SystemSetting, AdminFileAccessLog, AdminAlertEvent, ContactMessage

@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ('key', 'is_active', 'created_at', 'updated_at')
    search_fields = ('key', 'description')
    list_filter = ('is_active',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(AdminFileAccessLog)
class AdminFileAccessLogAdmin(admin.ModelAdmin):
    list_display = ('admin_user', 'object_type', 'action', 'created_at', 'ip_address')
    list_filter = ('action', 'object_type', 'created_at')
    search_fields = ('admin_user__email', 'object_public_id', 'reason')
    readonly_fields = ('created_at',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

@admin.register(AdminAlertEvent)
class AdminAlertEventAdmin(admin.ModelAdmin):
    list_display = ('alert_type', 'severity', 'status', 'created_at', 'sent_at')
    list_filter = ('severity', 'status', 'created_at')
    search_fields = ('alert_type', 'summary')
    readonly_fields = ('created_at',)

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'email', 'subject', 'status')
    list_filter = ('status', 'created_at')
    search_fields = ('email', 'subject', 'message')
    readonly_fields = ('public_id', 'user', 'name', 'email', 'subject', 'message', 'source_path', 'status', 'sent_at', 'last_error_code', 'created_at', 'updated_at')

    def has_add_permission(self, request):
        return False
