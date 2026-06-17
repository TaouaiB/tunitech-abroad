from apps.profiles.models import CandidateProfile
from apps.profiles.services.validation import (
    CURRENT_LEVEL_CHOICES,
    LANGUAGE_LEVEL_CHOICES,
    RELOCATION_PREFERENCE_CHOICES,
    REMOTE_PREFERENCE_CHOICES,
    TARGET_JOB_TYPE_CHOICES,
    TARGET_TYPE_CHOICES,
    is_meaningful_text,
    meaningful_list,
    normalize_profile_url,
)

class ProfileCompletenessService:
    FIELD_LABELS = {
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
    RECOMMENDATION_FIELD_LABELS = {
        'career_level': FIELD_LABELS['current_level'],
        'target_roles': FIELD_LABELS['target_roles'],
        'french_level': FIELD_LABELS['french_level'],
        'english_level': FIELD_LABELS['english_level'],
    }
    URL_FIELDS = {
        "linkedin_url": "LinkedIn",
        "github_url": "GitHub",
        "portfolio_url": "Portfolio",
        "website_url": "Site personnel",
    }
    ALLOWED_VALUES = {
        "current_level": {value for value, _label in CURRENT_LEVEL_CHOICES if value},
        "french_level": {value for value, _label in LANGUAGE_LEVEL_CHOICES if value},
        "english_level": {value for value, _label in LANGUAGE_LEVEL_CHOICES if value},
        "relocation_preference": {value for value, _label in RELOCATION_PREFERENCE_CHOICES if value},
        "remote_preference": {value for value, _label in REMOTE_PREFERENCE_CHOICES if value},
        "target_type": {value for value, _label in TARGET_TYPE_CHOICES if value},
    }
    TARGET_JOB_TYPE_VALUES = {value for value, _label in TARGET_JOB_TYPE_CHOICES}

    @classmethod
    def get_missing_fields(cls, profile: CandidateProfile) -> list[str]:
        report = cls.get_report(profile)
        return report["missing"] + report["invalid"]

    @classmethod
    def get_recommendation_missing_fields(cls, profile: CandidateProfile) -> list[str]:
        report = cls.get_recommendation_report(profile)
        return report["missing"] + report["invalid"]

    @classmethod
    def get_report(cls, profile: CandidateProfile) -> dict[str, list[str] | int]:
        missing = []
        invalid = []
        for field, label in cls.FIELD_LABELS.items():
            if not cls._is_field_complete(profile, field):
                missing.append(label)

        for field, label in cls.URL_FIELDS.items():
            val = getattr(profile, field, None)
            if val:
                try:
                    normalize_profile_url(val)
                except ValueError:
                    invalid.append(f"{label} invalide")

        for field, allowed in cls.ALLOWED_VALUES.items():
            val = getattr(profile, field, None)
            if val and val not in allowed:
                invalid.append(f"{cls.FIELD_LABELS.get(field, field)} invalide")

        return {
            "missing": missing,
            "invalid": invalid,
            "score": cls._score(profile),
        }

    @classmethod
    def get_recommendation_report(cls, profile: CandidateProfile) -> dict[str, list[str] | int]:
        missing = []
        invalid = []

        for field, label in cls.RECOMMENDATION_FIELD_LABELS.items():
            if field == "career_level":
                if not cls._has_usable_career_level(profile):
                    missing.append(label)
                continue
            if not cls._is_field_complete(profile, field):
                missing.append(label)

        for field, label in cls.URL_FIELDS.items():
            val = getattr(profile, field, None)
            if val:
                try:
                    normalize_profile_url(val)
                except ValueError:
                    invalid.append(f"{label} invalide")

        for field, allowed in cls.ALLOWED_VALUES.items():
            if field in {"relocation_preference", "remote_preference"}:
                continue
            val = getattr(profile, field, None)
            if val and val not in allowed:
                invalid.append(f"{cls.FIELD_LABELS.get(field, field)} invalide")

        return {
            "missing": missing,
            "invalid": invalid,
            "score": cls._score(profile),
        }

    @classmethod
    def calculate(cls, profile: CandidateProfile) -> int:
        score = cls._score(profile)
        
        if profile.profile_completion_score != score:
            profile.profile_completion_score = score
            profile.save(update_fields=['profile_completion_score'])
            
        return score

    @classmethod
    def _score(cls, profile: CandidateProfile) -> int:
        fields_to_check = list(cls.FIELD_LABELS.keys())
        filled = 0
        for field in fields_to_check:
            if cls._is_field_complete(profile, field):
                filled += 1
                
        base = 10
        additional = int((filled / len(fields_to_check)) * 90)
        return base + additional

    @classmethod
    def _is_field_complete(cls, profile: CandidateProfile, field: str) -> bool:
        val = getattr(profile, field, None)
        if val is None or val == "":
            return False
        if field in {"full_name", "phone", "location"}:
            return is_meaningful_text(str(val))
        if field == "target_roles":
            return bool(meaningful_list(val if isinstance(val, list) else [str(val)]))
        if field == "target_job_types":
            if not isinstance(val, list) or not val:
                return False
            return all(item in cls.TARGET_JOB_TYPE_VALUES for item in val)
        if field in cls.ALLOWED_VALUES:
            return val in cls.ALLOWED_VALUES[field]
        return True

    @classmethod
    def _has_usable_career_level(cls, profile: CandidateProfile) -> bool:
        current_level = getattr(profile, "current_level", "")
        if current_level:
            return current_level in cls.ALLOWED_VALUES["current_level"]
        return getattr(profile, "years_experience", None) is not None
