import json

from django import forms
from .models import CandidateProfile
from .services.validation import (
    CURRENT_LEVEL_CHOICES,
    LANGUAGE_LEVEL_CHOICES,
    RELOCATION_PREFERENCE_CHOICES,
    REMOTE_PREFERENCE_CHOICES,
    TARGET_TYPE_CHOICES,
    meaningful_list,
    normalize_profile_url,
)

class ProfileForm(forms.ModelForm):
    linkedin_url = forms.CharField(label="LinkedIn", required=False, widget=forms.URLInput)
    github_url = forms.CharField(label="GitHub", required=False, widget=forms.URLInput)
    portfolio_url = forms.CharField(label="Portfolio", required=False, widget=forms.URLInput)
    website_url = forms.CharField(label="Personal website", required=False, widget=forms.URLInput)
    target_roles = forms.CharField(
        label="Target roles",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Backend developer, DevOps, Data analyst"}),
        help_text="Enter one or more IT roles separated by commas.",
    )

    class Meta:
        model = CandidateProfile
        fields = [
            'full_name', 'phone', 'location', 'linkedin_url',
            'github_url', 'portfolio_url', 'website_url',
            'current_level', 'years_experience', 'target_roles',
            'target_type',
            'french_level', 'english_level', 'relocation_preference', 'remote_preference'
        ]
        labels = {
            'full_name': 'Full name',
            'phone': 'Phone',
            'location': 'Location',
            'current_level': 'Career level',
            'years_experience': 'Years of experience',
            'target_roles': 'Target roles',
            'target_type': 'Target opportunity type',
            'french_level': 'French level',
            'english_level': 'English level',
            'relocation_preference': 'Mobility / relocation',
            'remote_preference': 'Remote work preference',
        }
        help_texts = {
            'phone': 'Include the country code if possible.',
            'location': 'City and country, for example Tunis, Tunisia.',
            'linkedin_url': 'Complete URL starting with https://.',
            'github_url': 'Complete URL starting with https://.',
            'portfolio_url': 'Complete URL starting with https://.',
            'website_url': 'Complete URL starting with https://.',
            'current_level': 'Choose the level that best describes your current situation.',
            'years_experience': 'Use 0 for your first internship or first experience.',
        }
        widgets = {
            'current_level': forms.Select(choices=CURRENT_LEVEL_CHOICES),
            'french_level': forms.Select(choices=LANGUAGE_LEVEL_CHOICES),
            'english_level': forms.Select(choices=LANGUAGE_LEVEL_CHOICES),
            'relocation_preference': forms.Select(choices=RELOCATION_PREFERENCE_CHOICES),
            'remote_preference': forms.Select(choices=REMOTE_PREFERENCE_CHOICES),
            'target_type': forms.Select(choices=TARGET_TYPE_CHOICES),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound and self.instance and self.instance.pk:
            value = getattr(self.instance, "target_roles", [])
            self.initial["target_roles"] = ", ".join(value) if isinstance(value, list) else value

    def _clean_list_field(self, field_name: str) -> list[str]:
        value = self.cleaned_data.get(field_name, "")
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        value = (value or "").strip()
        if not value:
            return []
        if value.startswith("["):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError:
                parsed = None
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if item.strip()]
        return [item.strip() for item in value.split(",") if item.strip()]

    def clean_target_roles(self):
        return meaningful_list(self._clean_list_field("target_roles"))

    def clean_current_level(self):
        return self._clean_choice("current_level", {value for value, _label in CURRENT_LEVEL_CHOICES})

    def clean_french_level(self):
        return self._clean_choice("french_level", {value for value, _label in LANGUAGE_LEVEL_CHOICES})

    def clean_english_level(self):
        return self._clean_choice("english_level", {value for value, _label in LANGUAGE_LEVEL_CHOICES})

    def clean_remote_preference(self):
        return self._clean_choice("remote_preference", {value for value, _label in REMOTE_PREFERENCE_CHOICES})

    def clean_relocation_preference(self):
        return self._clean_choice("relocation_preference", {value for value, _label in RELOCATION_PREFERENCE_CHOICES})

    def clean_target_type(self):
        return self._clean_choice("target_type", {value for value, _label in TARGET_TYPE_CHOICES})

    def _clean_choice(self, field_name: str, allowed_values: set[str]) -> str:
        value = self.cleaned_data.get(field_name) or ""
        if value not in allowed_values:
            raise forms.ValidationError("Select one of the suggested values.")
        return value

    def _clean_url_field(self, field_name: str) -> str:
        value = self.cleaned_data.get(field_name) or ""
        try:
            return normalize_profile_url(value)
        except ValueError as exc:
            raise forms.ValidationError(str(exc)) from exc

    def clean_linkedin_url(self):
        return self._clean_url_field("linkedin_url")

    def clean_github_url(self):
        return self._clean_url_field("github_url")

    def clean_portfolio_url(self):
        return self._clean_url_field("portfolio_url")

    def clean_website_url(self):
        return self._clean_url_field("website_url")
