from django.contrib import admin
from django.contrib import messages
from apps.skills.models import Skill, SkillAlias, UnmatchedSkillCandidate
from apps.skills.services.review import UnmatchedSkillReviewService

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('canonical_name', 'category', 'source', 'is_active', 'created_at')
    search_fields = ('canonical_name', 'slug')
    list_filter = ('category', 'source', 'is_active')
    prepopulated_fields = {'slug': ('canonical_name',)}
    readonly_fields = ('created_at', 'updated_at')

@admin.register(SkillAlias)
class SkillAliasAdmin(admin.ModelAdmin):
    list_display = ('alias', 'skill', 'normalized_alias', 'language')
    search_fields = ('alias', 'normalized_alias', 'skill__canonical_name')
    list_filter = ('language',)
    readonly_fields = ('created_at', 'updated_at')

@admin.action(description='Mark selected candidates as ignored')
def ignore_candidates(modeladmin, request, queryset):
    count = 0
    for candidate in queryset:
        if candidate.status == 'pending':
            UnmatchedSkillReviewService.ignore_candidate(candidate.id, request.user)
            count += 1
    modeladmin.message_user(request, f"{count} candidates ignored.", messages.SUCCESS)

@admin.action(description='Map selected candidates (if mapped_skill is set)')
def map_candidates(modeladmin, request, queryset):
    count = 0
    error_count = 0
    for candidate in queryset:
        if candidate.status == 'pending' and candidate.mapped_skill_id:
            try:
                UnmatchedSkillReviewService.map_candidate(candidate.id, candidate.mapped_skill_id, request.user)
                count += 1
            except Exception as e:
                error_count += 1
    
    if count:
        modeladmin.message_user(request, f"{count} candidates mapped.", messages.SUCCESS)
    if error_count:
        modeladmin.message_user(request, f"{error_count} candidates failed to map.", messages.ERROR)

@admin.register(UnmatchedSkillCandidate)
class UnmatchedSkillCandidateAdmin(admin.ModelAdmin):
    list_display = ('raw_skill_text', 'normalized_text', 'source_type', 'occurrence_count', 'status', 'mapped_skill')
    search_fields = ('raw_skill_text', 'normalized_text')
    list_filter = ('status', 'source_type')
    readonly_fields = ('created_at', 'updated_at', 'reviewed_at', 'reviewed_by')
    actions = [ignore_candidates, map_candidates]
    
    def save_model(self, request, obj, form, change):
        if change and obj.status == 'pending' and obj.mapped_skill_id:
            # use service to map
            try:
                UnmatchedSkillReviewService.map_candidate(obj.id, obj.mapped_skill_id, request.user)
                # It saved to db, we don't need to super().save_model unless other fields changed, but it's safer.
            except Exception as e:
                messages.error(request, f"Failed to map candidate: {e}")
        else:
            super().save_model(request, obj, form, change)
