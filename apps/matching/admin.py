from django.contrib import admin
from .models import MatchResult, QuickMatchSession, MatchQualityFeedback


class MatchQualityFeedbackInline(admin.TabularInline):
    model = MatchQualityFeedback
    extra = 0
    raw_id_fields = ('reviewed_by',)


@admin.register(MatchResult)
class MatchResultAdmin(admin.ModelAdmin):
    list_display = ('public_id', 'user', 'job', 'fit_score', 'llm_explanation_status', 'created_at')
    list_filter = ('llm_explanation_status', 'scoring_version', 'created_at')
    search_fields = ('public_id', 'user__email', 'job__title', 'job__company_name')
    readonly_fields = ('public_id', 'created_at', 'updated_at')
    inlines = [MatchQualityFeedbackInline]


@admin.register(QuickMatchSession)
class QuickMatchSessionAdmin(admin.ModelAdmin):
    list_display = ('public_id', 'job', 'experience_level', 'estimated_fit_score', 'created_at', 'expires_at')
    list_filter = ('experience_level', 'created_at')
    search_fields = ('public_id', 'session_key_hash', 'job__title')
    readonly_fields = ('public_id', 'created_at', 'expires_at')


@admin.register(MatchQualityFeedback)
class MatchQualityFeedbackAdmin(admin.ModelAdmin):
    list_display = ('id', 'match_result', 'reason', 'reviewed_by', 'created_at')
    list_filter = ('reason', 'created_at')
    search_fields = ('match_result__public_id', 'reviewed_by__email')
    raw_id_fields = ('match_result', 'reviewed_by')
