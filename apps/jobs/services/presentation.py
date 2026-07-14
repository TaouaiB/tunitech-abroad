from apps.jobs.models import RequirementType
from apps.skills.services.extraction_policy import SkillCandidateKind, classify_skill_candidate


class JobPresentationService:
    UNKNOWN_LANGUAGE_VALUES = {
        "",
        "-",
        "n/a",
        "na",
        "none",
        "null",
        "t",
        "unknown",
        "inconnu",
        "inconnue",
        "non precise",
        "non précisé",
        "non précisée",
        "not specified",
        "unspecified",
        "langues non precisees",
        "langues non précisées",
    }

    @staticmethod
    def is_valid_badge_value(value) -> bool:
        """
        Returns False if the value is empty, None, or a known placeholder like "unknown".
        """
        if not value:
            return False
        val_str = str(value).strip().lower()
        if not val_str:
            return False
        return val_str not in JobPresentationService.UNKNOWN_LANGUAGE_VALUES


    JOB_TYPE_LABELS = {
        "full_time_job": "Emploi",
        "internship": "Stage",
        "apprenticeship": "Alternance",
        "contract": "Freelance / Mission",
        "unknown": "Type non précisé",
    }

    @staticmethod
    def get_deduplicated_badges(job):
        badges = []
        seen = set()

        def add_badge(text, css_class):
            if not JobPresentationService.is_valid_badge_value(text):
                return
            val_lower = str(text).strip().lower()
            if val_lower not in seen:
                seen.add(val_lower)
                badges.append({"text": text, "css_class": css_class})

        job_type_val = getattr(job, "job_type", "")
        if job_type_val:
            job_type_label = JobPresentationService.JOB_TYPE_LABELS.get(str(job_type_val), "Type non précisé")
            add_badge(job_type_label, "tta-badge-brand")

        add_badge(getattr(job, 'get_remote_type_display', lambda: job.remote_type)(), "tta-badge-muted")
        add_badge(getattr(job, 'get_experience_level_display', lambda: job.experience_level)(), "tta-badge-muted")

        return badges

    @staticmethod
    def get_user_facing_skill_entries(job, *, strong_skills=None, missing_required=None, missing_optional=None):
        """Return the one canonical, deterministic skill set used on every user page."""
        requirement_order = {
            RequirementType.REQUIRED: 0,
            RequirementType.OPTIONAL: 1,
            RequirementType.DETECTED: 2,
            RequirementType.UNKNOWN: 3,
        }

        def names(rows):
            values = set()
            for row in rows or []:
                value = row.get("name") if isinstance(row, dict) else row
                if value:
                    values.add(str(value).strip().casefold())
            return values

        strong_names = names(strong_skills)
        missing_required_names = names(missing_required)
        missing_optional_names = names(missing_optional)
        rows = list(job.job_skills.select_related("skill").all())
        rows.sort(
            key=lambda row: (
                requirement_order.get(row.requirement_type, 9),
                row.skill.canonical_name.casefold(),
                row.skill_id,
            )
        )

        entries = []
        seen = set()
        for row in rows:
            skill_name = (row.skill.canonical_name or "").strip()
            normalized_name = skill_name.casefold()
            if not skill_name or normalized_name in seen:
                continue
            decision = classify_skill_candidate(
                raw_text=skill_name,
                canonical_name=skill_name,
                category=row.skill.category,
            )
            if decision.kind != SkillCandidateKind.HARD_TECHNICAL or not decision.materialize:
                continue

            status = "neutral"
            if normalized_name in strong_names:
                status = "strong"
            elif normalized_name in missing_required_names:
                status = "missing"
            elif normalized_name in missing_optional_names:
                status = "warning"
            entries.append({"name": skill_name, "status": status, "requirement_type": row.requirement_type})
            seen.add(normalized_name)
        return entries

    @staticmethod
    def get_strong_skill_entries(subject):
        return [
            entry
            for entry in JobPresentationService.get_subject_skill_entries(subject)
            if entry["status"] == "strong"
        ]

    @staticmethod
    def get_missing_required_skill_entries(subject):
        return [
            entry
            for entry in JobPresentationService.get_subject_skill_entries(subject)
            if entry["status"] == "missing"
        ]

    @staticmethod
    def get_missing_optional_skill_entries(subject):
        return [
            entry
            for entry in JobPresentationService.get_subject_skill_entries(subject)
            if entry["status"] == "warning"
        ]

    @staticmethod
    def get_subject_skill_entries(subject):
        """Resolve persisted status only against the subject's current canonical job skills."""
        if hasattr(subject, "missing_required_skills_json"):
            return JobPresentationService.get_user_facing_skill_entries(
                subject.job,
                strong_skills=subject.strong_skills_json,
                missing_required=subject.missing_required_skills_json,
                missing_optional=subject.missing_optional_skills_json,
            )

        if hasattr(subject, "missing_skills_json") and hasattr(subject, "matched_skills_json"):
            missing_required = []
            missing_optional = []
            for skill in subject.missing_skills_json or []:
                target = (
                    missing_optional
                    if isinstance(skill, dict) and skill.get("requirement_type") == RequirementType.OPTIONAL
                    else missing_required
                )
                target.append(skill)
            return JobPresentationService.get_user_facing_skill_entries(
                subject.job,
                strong_skills=subject.matched_skills_json,
                missing_required=missing_required,
                missing_optional=missing_optional,
            )

        missing_required = []
        missing_optional = []
        for skill in getattr(subject, "missing_skills_json", []) or []:
            target = (
                missing_optional
                if isinstance(skill, dict) and skill.get("requirement_type") == RequirementType.OPTIONAL
                else missing_required
            )
            target.append(skill)
        return JobPresentationService.get_user_facing_skill_entries(
            subject.job,
            strong_skills=getattr(subject, "strong_skills_json", []),
            missing_required=missing_required,
            missing_optional=missing_optional,
        )

    @staticmethod
    def get_card_skill_chips(job, limit=5):
        canonical = [entry["name"] for entry in JobPresentationService.get_user_facing_skill_entries(job)[:limit]]
        if canonical:
            return canonical

        # The public search card may show bounded raw evidence while canonical
        # extraction is pending; matching/recommendation/saved/detail pages do not.
        chips = []
        for raw_skill in job.required_skills_json if isinstance(job.required_skills_json, list) else []:
            skill_name = str(raw_skill).strip()
            decision = classify_skill_candidate(raw_text=skill_name)
            if (
                not skill_name
                or len(skill_name) > 34
                or decision.kind != SkillCandidateKind.HARD_TECHNICAL
                or not decision.materialize
            ):
                continue
            chips.append(skill_name)
            if len(chips) >= limit:
                break
        return chips

    @staticmethod
    def get_valid_languages(job):
        """
        Returns a dictionary of language requirements, filtering out
        unknown, empty, or placeholder values.
        """
        language_requirements = job.language_requirements_json
        if not isinstance(language_requirements, dict):
            return {}

        valid_langs = {}

        for lang, code in language_requirements.items():
            language_name = str(lang).strip()
            if not language_name:
                continue

            if not code:
                continue

            val = str(code).strip().lower()
            if val in JobPresentationService.UNKNOWN_LANGUAGE_VALUES:
                continue

            valid_langs[language_name] = code

        return valid_langs

    @staticmethod
    def get_safe_public_eligibility_reason(job) -> str:
        from apps.jobs.services.eligibility import JobEligibilityService, PublicJobState
        from apps.jobs.models import JobStatus
        from django.utils import timezone

        state = JobEligibilityService.classify_public_state(job)
        if state in (
            PublicJobState.PUBLIC_MATCHABLE,
            PublicJobState.PUBLIC_LIMITED_PENDING_ANALYSIS,
        ):
            return ""

        if job.status == JobStatus.EXPIRED:
            return "Offre expirée"

        if job.status == JobStatus.STALE:
            return "Offre ancienne"

        expires_at = getattr(job, "expires_at", None)
        if expires_at and expires_at < timezone.now():
            return "Offre expirée"

        if not getattr(job.source, "is_active", True) or job.status in (
            JobStatus.REMOVED,
            JobStatus.ARCHIVED,
        ):
            return "Offre indisponible"

        return "Non publiée"
