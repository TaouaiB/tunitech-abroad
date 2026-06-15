from apps.profiles.models import CandidateProfile, ProfileSkill

class ProfileCompletenessService:
    @classmethod
    def calculate(cls, profile: CandidateProfile) -> int:
        score = 0
        total_fields = 7
        
        if profile.full_name:
            score += 1
        if profile.phone:
            score += 1
        if profile.location:
            score += 1
        if profile.current_level:
            score += 1
        if profile.years_experience is not None:
            score += 1
        if profile.target_roles:
            score += 1
            
        if ProfileSkill.objects.filter(profile=profile).exists():
            score += 1
            
        completion_percentage = int((score / total_fields) * 100)
        
        if profile.profile_completion_score != completion_percentage:
            profile.profile_completion_score = completion_percentage
            profile.save(update_fields=['profile_completion_score'])
            
        return completion_percentage
