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


    @staticmethod
    def get_card_skill_chips(job, limit=5):
        canonical_skills = [
            job_skill.skill.canonical_name
            for job_skill in job.job_skills.select_related("skill").all()[:limit]
            if job_skill.skill.canonical_name
        ]
        if canonical_skills:
            return canonical_skills

        raw_skills = job.required_skills_json if isinstance(job.required_skills_json, list) else []
        chips = []
        for raw_skill in raw_skills:
            skill = str(raw_skill).strip()
            if not skill or len(skill) > 34:
                continue
            chips.append(skill)
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
