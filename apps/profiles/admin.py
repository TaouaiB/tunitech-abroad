from django.contrib import admin
from django.contrib import messages
from .models import CandidateProfile, ProfileSkill
from apps.recommendations.tasks import refresh_user_recommendations

@admin.action(description="Refresh recommendations")
def refresh_recommendations(modeladmin, request, queryset):
    count = 0
    for profile in queryset:
        refresh_user_recommendations.delay(profile.user_id, trigger_type="admin_action")
        count += 1
    modeladmin.message_user(request, f"Queued recommendation refresh for {count} profiles.", messages.SUCCESS)

@admin.register(CandidateProfile)
class CandidateProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'current_level', 'target_type', 'is_confirmed', 'created_at')
    search_fields = ('user__email', 'user__username', 'full_name')
    list_filter = ('is_confirmed', 'current_level', 'target_type', 'french_level', 'english_level')
    readonly_fields = ('public_id', 'created_at', 'updated_at')
    actions = [refresh_recommendations]

@admin.register(ProfileSkill)
class ProfileSkillAdmin(admin.ModelAdmin):
    list_display = ('normalized_name', 'profile', 'confidence', 'is_confirmed', 'created_at')
    search_fields = ('normalized_name', 'raw_name', 'profile__user__email')
    list_filter = ('is_confirmed', 'source')
    readonly_fields = ('created_at', 'updated_at')
