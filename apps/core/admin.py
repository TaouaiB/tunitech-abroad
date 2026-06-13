from django.contrib import admin
from .models import SystemSetting

@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ('key', 'is_active', 'created_at', 'updated_at')
    search_fields = ('key', 'description')
    list_filter = ('is_active',)
    readonly_fields = ('created_at', 'updated_at')
