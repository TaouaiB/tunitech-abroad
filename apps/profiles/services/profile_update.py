from apps.profiles.models import CandidateProfile
from .completeness import ProfileCompletenessService

class ProfileUpdateService:
    @classmethod
    def update_profile(cls, user, cleaned_data) -> CandidateProfile:
        profile = getattr(user, 'candidate_profile', None)
        if not profile:
            profile = CandidateProfile(user=user)
            
        for field, value in cleaned_data.items():
            if hasattr(profile, field):
                setattr(profile, field, value)
                
        profile.save()
        ProfileCompletenessService.calculate(profile)
        return profile
