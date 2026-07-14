import re
import unicodedata

from apps.jobs.services.presentation import JobPresentationService
from apps.jobs.services.language_requirements import (
    LanguageRequirementClassifier,
    LanguageRequirementKind,
)
from apps.matching.models import RISK_FLAG_LABELS


class MatchPresentationService:
    """Context-aware, user-facing presentation for persisted match data."""

    LANGUAGE_WARNING_LABELS = {
        "french_level_missing": "Niveau de français requis non atteint",
        "english_level_missing": "Niveau d'anglais requis non atteint",
    }
    SKILL_ACTION_PATTERN = re.compile(
        r"Priorité\s*:\s*ajoutez\s+.+?\s+à votre plan d[’']apprentissage\.\s*"
        r"Mettez à jour votre CV si vous avez déjà utilisé\s+.+?\.(?:\s*|$)"
    )

    @staticmethod
    def _normalized(value) -> str:
        text = unicodedata.normalize("NFKD", str(value or ""))
        return "".join(char for char in text if not unicodedata.combining(char)).strip().casefold()

    @classmethod
    def get_user_facing_risk_labels(cls, subject) -> list[str]:
        labels = []
        job = getattr(subject, "job", None)
        for flag in getattr(subject, "risk_flags_json", []) or []:
            if flag in {"missing_required_skills", "job_language_unknown", "experience_unknown"}:
                continue
            if flag == "french_level_missing":
                if not job or LanguageRequirementClassifier.classify(
                    job.language_requirements_json, "french"
                ) != LanguageRequirementKind.REQUIRED:
                    continue
                label = cls.LANGUAGE_WARNING_LABELS[flag]
            elif flag == "english_level_missing":
                if not job or LanguageRequirementClassifier.classify(
                    job.language_requirements_json, "english"
                ) != LanguageRequirementKind.REQUIRED:
                    continue
                label = cls.LANGUAGE_WARNING_LABELS[flag]
            else:
                label = RISK_FLAG_LABELS.get(flag, str(flag).replace("_", " ").capitalize())
            if cls._normalized(label) == "langues non precisees":
                continue
            if label not in labels:
                labels.append(label)
        return labels

    @classmethod
    def get_user_facing_actions(cls, match) -> list[str]:
        actions = []
        for action in getattr(match, "recommended_actions_json", []) or []:
            if not cls.SKILL_ACTION_PATTERN.search(str(action)):
                actions.append(str(action))

        missing = JobPresentationService.get_missing_required_skill_entries(match)
        if missing:
            name = missing[0]["name"]
            actions.insert(
                0,
                f"Priorité : ajoutez {name} à votre plan d'apprentissage. "
                f"Mettez à jour votre CV si vous avez déjà utilisé {name}.",
            )
        return list(dict.fromkeys(actions))

    @classmethod
    def get_user_facing_recommendation_reason(cls, recommendation) -> str:
        reason = str(getattr(recommendation, "reason_summary", "") or "")
        reason = cls.SKILL_ACTION_PATTERN.sub("", reason).strip(" .")
        missing = JobPresentationService.get_missing_required_skill_entries(recommendation)
        if missing:
            name = missing[0]["name"]
            canonical = (
                f"Priorité : ajoutez {name} à votre plan d'apprentissage. "
                f"Mettez à jour votre CV si vous avez déjà utilisé {name}."
            )
            return f"{canonical} {reason}".strip()
        return reason
