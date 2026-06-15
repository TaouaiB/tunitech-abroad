from django import forms
from .models import CandidateProfile

class ProfileForm(forms.ModelForm):
    class Meta:
        model = CandidateProfile
        fields = [
            'full_name', 'phone', 'location', 'linkedin_url', 
            'github_url', 'portfolio_url', 'website_url', 
            'current_level', 'years_experience', 'target_country',
            'french_level', 'english_level', 'relocation_preference', 'remote_preference'
        ]
