from django.contrib import admin
from .models import CandidateProfile, ProfileSkill

@admin.register(CandidateProfile)
class CandidateProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'current_level', 'target_type', 'is_confirmed', 'created_at')
    search_fields = ('user__email', 'user__username', 'full_name')
    list_filter = ('is_confirmed', 'current_level', 'target_type')
    readonly_fields = ('public_id', 'created_at', 'updated_at')

@admin.register(ProfileSkill)
class ProfileSkillAdmin(admin.ModelAdmin):
    list_display = ('normalized_name', 'profile', 'confidence', 'is_confirmed', 'created_at')
    search_fields = ('normalized_name', 'raw_name', 'profile__user__email')
    list_filter = ('is_confirmed', 'source')
    readonly_fields = ('created_at', 'updated_at')
