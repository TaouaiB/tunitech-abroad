from django.contrib import admin
from .models import JobRecommendation, RecommendationRun, SavedJob, RecommendationQualityFeedback


class RecommendationQualityFeedbackInline(admin.TabularInline):
    model = RecommendationQualityFeedback
    extra = 0
    raw_id_fields = ('reviewed_by',)


@admin.register(JobRecommendation)
class JobRecommendationAdmin(admin.ModelAdmin):
    list_display = ('user', 'job', 'status', 'fit_score', 'match_confidence', 'rank', 'computed_at')
    list_filter = ('status', 'computed_at')
    search_fields = ('user__email', 'job__title', 'job__company_name')
    readonly_fields = ('computed_at', 'updated_at')
    inlines = [RecommendationQualityFeedbackInline]


@admin.register(RecommendationRun)
class RecommendationRunAdmin(admin.ModelAdmin):
    list_display = ('user', 'trigger_type', 'status', 'started_at', 'stored_recommendations_count')
    list_filter = ('status', 'trigger_type', 'started_at')
    search_fields = ('user__email', 'error_message')
    readonly_fields = ('started_at', 'finished_at', 'error_message')


@admin.register(SavedJob)
class SavedJobAdmin(admin.ModelAdmin):
    list_display = ('user', 'job', 'saved_at')
    list_filter = ('saved_at',)
    search_fields = ('user__email', 'job__title', 'job__company_name')
    readonly_fields = ('saved_at',)


@admin.register(RecommendationQualityFeedback)
class RecommendationQualityFeedbackAdmin(admin.ModelAdmin):
    list_display = ('id', 'recommendation', 'reason', 'reviewed_by', 'created_at')
    list_filter = ('reason', 'created_at')
    search_fields = ('recommendation__user__email', 'reviewed_by__email')
    raw_id_fields = ('recommendation', 'reviewed_by')
