from django.contrib import admin
from .models import JobRecommendation, RecommendationRun, SavedJob

@admin.register(JobRecommendation)
class JobRecommendationAdmin(admin.ModelAdmin):
    list_display = ('user', 'job', 'status', 'fit_score', 'rank', 'computed_at')
    list_filter = ('status', 'computed_at')
    search_fields = ('user__email', 'job__title', 'job__company_name')
    readonly_fields = ('computed_at', 'updated_at')

@admin.register(RecommendationRun)
class RecommendationRunAdmin(admin.ModelAdmin):
    list_display = ('user', 'trigger_type', 'status', 'started_at', 'finished_at')
    list_filter = ('status', 'trigger_type', 'started_at')
    search_fields = ('user__email',)
    readonly_fields = ('started_at', 'finished_at')

@admin.register(SavedJob)
class SavedJobAdmin(admin.ModelAdmin):
    list_display = ('user', 'job', 'saved_at')
    list_filter = ('saved_at',)
    search_fields = ('user__email', 'job__title', 'job__company_name')
    readonly_fields = ('saved_at',)
