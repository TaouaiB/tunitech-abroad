from django.contrib import admin
from .models import MatchResult, QuickMatchSession

@admin.register(MatchResult)
class MatchResultAdmin(admin.ModelAdmin):
    list_display = ('public_id', 'user', 'job', 'fit_score', 'llm_explanation_status', 'created_at')
    list_filter = ('llm_explanation_status', 'scoring_version', 'created_at')
    search_fields = ('public_id', 'user__email', 'job__title', 'job__company_name')
    readonly_fields = ('public_id', 'created_at', 'updated_at')

@admin.register(QuickMatchSession)
class QuickMatchSessionAdmin(admin.ModelAdmin):
    list_display = ('public_id', 'job', 'experience_level', 'estimated_fit_score', 'created_at', 'expires_at')
    list_filter = ('experience_level', 'created_at')
    search_fields = ('public_id', 'session_key_hash', 'job__title')
    readonly_fields = ('public_id', 'created_at', 'expires_at')
