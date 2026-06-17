class JobPresentationService:
    UNKNOWN_LANGUAGE_VALUES = {
        "",
        "-",
        "n/a",
        "na",
        "none",
        "null",
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
