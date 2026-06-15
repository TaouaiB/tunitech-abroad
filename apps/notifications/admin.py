from django.contrib import admin
from .models import EmailPreference

@admin.register(EmailPreference)
class EmailPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'product_updates_enabled', 'weekly_digest_enabled', 'cv_analysis_email_enabled')
    search_fields = ('user__email', 'user__username')
    list_filter = ('product_updates_enabled', 'weekly_digest_enabled', 'cv_analysis_email_enabled')
    readonly_fields = ('created_at', 'updated_at')
