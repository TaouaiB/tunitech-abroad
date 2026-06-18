import json

from django import forms
from .models import CandidateProfile
from .services.validation import (
    CURRENT_LEVEL_CHOICES,
    LANGUAGE_LEVEL_CHOICES,
    RELOCATION_PREFERENCE_CHOICES,
    REMOTE_PREFERENCE_CHOICES,
    TARGET_JOB_TYPE_CHOICES,
    TARGET_TYPE_CHOICES,
    meaningful_list,
    normalize_profile_url,
)

class ProfileForm(forms.ModelForm):
    linkedin_url = forms.CharField(label="LinkedIn", required=False, widget=forms.URLInput)
    github_url = forms.CharField(label="GitHub", required=False, widget=forms.URLInput)
    portfolio_url = forms.CharField(label="Portfolio", required=False, widget=forms.URLInput)
    website_url = forms.CharField(label="Site personnel", required=False, widget=forms.URLInput)
    target_roles = forms.CharField(
        label="Rôles ciblés",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Développeur backend, DevOps, Data analyst"}),
        help_text="Indiquez un ou plusieurs rôles IT séparés par des virgules.",
    )
    target_job_types = forms.MultipleChoiceField(
        label="Types de contrat cibles",
        choices=TARGET_JOB_TYPE_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Sélectionnez les formats qui vous intéressent.",
    )

    class Meta:
        model = CandidateProfile
        fields = [
            'full_name', 'phone', 'location', 'linkedin_url', 
            'github_url', 'portfolio_url', 'website_url', 
            'current_level', 'years_experience', 'target_roles',
            'target_job_types', 'target_type',
            'french_level', 'english_level', 'relocation_preference', 'remote_preference'
        ]
        labels = {
            'full_name': 'Nom complet',
            'phone': 'Téléphone',
            'location': 'Localisation',
            'current_level': 'Niveau de carrière',
            'years_experience': 'Années d’expérience',
            'target_roles': 'Rôles ciblés',
            'target_job_types': 'Types de contrat cibles',
            'target_type': 'Type d’opportunité recherchée',
            'french_level': 'Niveau de français',
            'english_level': 'Niveau d’anglais',
            'relocation_preference': 'Mobilité / relocalisation',
            'remote_preference': 'Préférence télétravail'
        }
        help_texts = {
            'phone': 'Numéro avec indicatif pays si possible.',
            'location': 'Ville et pays, par exemple Tunis, Tunisia.',
            'linkedin_url': 'URL complète commençant par https://.',
            'github_url': 'URL complète commençant par https://.',
            'portfolio_url': 'URL complète commençant par https://.',
            'website_url': 'URL complète commençant par https://.',
            'current_level': 'Choisissez le niveau qui décrit le mieux votre situation actuelle.',
            'years_experience': 'Utilisez 0 pour un premier stage ou une première expérience.',
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
            self.initial["target_job_types"] = getattr(self.instance, "target_job_types", [])

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
                return [str(item).strip() for item in parsed if str(item).strip()]
        return [item.strip() for item in value.split(",") if item.strip()]

    def clean_target_roles(self):
        return meaningful_list(self._clean_list_field("target_roles"))

    def clean_target_job_types(self):
        return self.cleaned_data.get("target_job_types") or []

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
            raise forms.ValidationError("Sélectionnez une valeur proposée.")
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
