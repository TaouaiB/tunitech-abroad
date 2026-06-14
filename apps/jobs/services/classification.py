import re
from apps.jobs.models import JobType, RemoteType, ExperienceLevel, RequirementType


class JobClassificationService:
    @staticmethod
    def classify(payload: dict, description: str, title: str) -> dict:
        combined_text = f"{title} {description}".lower()

        # Job Type Detection
        job_type = JobType.UNKNOWN.value
        type_contrat = payload.get("typeContrat", "").upper()
        nature_contrat = payload.get("natureContrat", "").upper()
        
        if "SAI" in type_contrat or "STAGE" in type_contrat or any(
            kw in combined_text for kw in ["stage", "stagiaire", "pfe", "fin d'études", "fin d'etudes"]
        ):
            job_type = JobType.INTERNSHIP.value
        elif "APP" in type_contrat or "ALTERNANCE" in type_contrat or any(
            kw in combined_text for kw in ["alternance", "apprentissage", "contrat pro"]
        ):
            job_type = JobType.APPRENTICESHIP.value
        elif "CDI" in type_contrat or "CDI" in nature_contrat or re.search(r'\bcdi\b', combined_text):
            job_type = JobType.FULL_TIME_JOB.value
        elif "CDD" in type_contrat or "MIS" in type_contrat or any(
            kw in combined_text for kw in ["cdd", "freelance", "mission"]
        ):
            job_type = JobType.CONTRACT.value

        # Remote Type Detection
        remote_type = RemoteType.UNKNOWN.value
        if any(kw in combined_text for kw in ["télétravail", "teletravail", "remote", "à distance", "a distance", "full-remote", "full remote", "100% télétravail"]):
            if "hybride" in combined_text or "hybrid" in combined_text or "jours sur site" in combined_text:
                remote_type = RemoteType.HYBRID.value
            else:
                remote_type = RemoteType.REMOTE.value
        elif "hybride" in combined_text or "hybrid" in combined_text or "jours sur site" in combined_text or "partiel" in combined_text:
            remote_type = RemoteType.HYBRID.value
        elif any(kw in combined_text for kw in ["présentiel", "presentiel", "sur site", "on-site"]):
            remote_type = RemoteType.ON_SITE.value

        # Experience Level Detection
        experience_level = ExperienceLevel.UNKNOWN.value
        exp_libelle = payload.get("experienceLibelle", "").lower()
        
        if job_type in [JobType.INTERNSHIP.value, JobType.APPRENTICESHIP.value]:
            experience_level = ExperienceLevel.INTERNSHIP.value
        elif "débutant accepté" in exp_libelle or "debutant" in exp_libelle or any(
            kw in combined_text for kw in ["junior", "débutant", "debutant", "0-2 ans", "0 à 2 ans"]
        ):
            experience_level = ExperienceLevel.JUNIOR.value
        elif any(kw in combined_text for kw in ["senior", "expert", "lead", "5 ans", "5+ ans", "10 ans"]):
            experience_level = ExperienceLevel.SENIOR.value
        elif "an" in exp_libelle or "ans" in exp_libelle or "mid" in combined_text or "confirmé" in combined_text:
            experience_level = ExperienceLevel.MID_LEVEL.value

        # Language Detection
        lang_reqs = {
            "french": RequirementType.UNKNOWN.value,
            "english": RequirementType.UNKNOWN.value,
        }
        
        # Check payload languages first
        for lang_obj in payload.get("langues", []):
            libelle = lang_obj.get("libelle", "").lower()
            exigence = lang_obj.get("exigence", "").upper()
            req = RequirementType.REQUIRED.value if exigence == "E" else RequirementType.OPTIONAL.value
            if "anglais" in libelle:
                lang_reqs["english"] = req
            elif "français" in libelle or "francais" in libelle:
                lang_reqs["french"] = req

        # Fallback to text detection if not explicitly required
        if lang_reqs["english"] == RequirementType.UNKNOWN.value:
            if any(kw in combined_text for kw in ["anglais courant", "anglais indispensable", "anglais exigé", "english required", "english mandatory"]):
                lang_reqs["english"] = RequirementType.REQUIRED.value
            elif any(kw in combined_text for kw in ["anglais apprécié", "bon niveau d'anglais", "anglais technique", "english plus", "english preferred"]):
                lang_reqs["english"] = RequirementType.OPTIONAL.value

        if lang_reqs["french"] == RequirementType.UNKNOWN.value:
            if any(kw in combined_text for kw in ["français courant", "français indispensable", "french required"]):
                lang_reqs["french"] = RequirementType.REQUIRED.value
            elif any(kw in combined_text for kw in ["français apprécié"]):
                lang_reqs["french"] = RequirementType.OPTIONAL.value

        return {
            "job_type": job_type,
            "remote_type": remote_type,
            "experience_level": experience_level,
            "language_requirements": lang_reqs,
        }
