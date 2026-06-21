from dataclasses import dataclass
from typing import Optional
from apps.profiles.models import CandidateProfile, ProfileSkill
from apps.jobs.models import NormalizedJob, RequirementType
from apps.cvs.models import CVUpload
from apps.skills.services.normalizer import normalize_skill_text
from apps.jobs.services.relevance import TECH_CATEGORIES
from django.utils import timezone

MISSING_FRENCH_LEVELS = {"", "none", "no", "a0"}

@dataclass(frozen=True)
class FitScoreResult:
    fit_score: int
    match_confidence: str
    technical_skills_score: int
    experience_score: int
    role_title_score: int
    language_score: int
    location_score: int
    strong_skills: list[dict[str, str]]
    missing_required_skills: list[dict[str, str]]
    missing_optional_skills: list[dict[str, str]]
    risk_flags: list[str]
    profile_signals: list[str]
    recommended_actions: list[str]
    scoring_version: str = "score_v1"

class MatchScoringService:
    CONFIDENCE_RELIABLE = "reliable"
    CONFIDENCE_LOW = "low_confidence"
    CONFIDENCE_UNAVAILABLE = "unavailable"

    @staticmethod
    def calculate(
        profile: CandidateProfile,
        job: NormalizedJob,
        cv_upload: Optional[CVUpload] = None,
    ) -> FitScoreResult:
        risk_flags = set()
        profile_signals = set()
        recommended_actions = set()
        classification_json = job.classification_json or {}
        it_confidence = classification_json.get("confidence", "unknown")
        skill_signal_quality = job.skill_signal_quality
        job_skills = list(job.job_skills.select_related("skill").all())
        tech_job_skills = [js for js in job_skills if js.skill.category in TECH_CATEGORIES]
        req_skills = [js for js in tech_job_skills if js.requirement_type == RequirementType.REQUIRED]

        match_confidence = MatchScoringService.CONFIDENCE_UNAVAILABLE
        if it_confidence == "excluded" or skill_signal_quality == "excluded_non_it":
            match_confidence = MatchScoringService.CONFIDENCE_UNAVAILABLE
        elif it_confidence in ["high", "medium"]:
            if skill_signal_quality == "strong":
                match_confidence = MatchScoringService.CONFIDENCE_RELIABLE
            elif skill_signal_quality == "partial":
                if len(req_skills) > 0:
                    match_confidence = MatchScoringService.CONFIDENCE_RELIABLE
                else:
                    match_confidence = MatchScoringService.CONFIDENCE_LOW
            elif skill_signal_quality == "generic_only":
                match_confidence = MatchScoringService.CONFIDENCE_LOW
            elif skill_signal_quality == "missing":
                if MatchScoringService._has_strong_it_context(job):
                    match_confidence = MatchScoringService.CONFIDENCE_LOW
                else:
                    match_confidence = MatchScoringService.CONFIDENCE_UNAVAILABLE
        elif it_confidence == "low":
            if skill_signal_quality in ["strong", "partial"]:
                match_confidence = MatchScoringService.CONFIDENCE_LOW
            else:
                match_confidence = MatchScoringService.CONFIDENCE_UNAVAILABLE

        if match_confidence == MatchScoringService.CONFIDENCE_UNAVAILABLE:
            risk_flags.add("non_it_low_relevance_job")
            if it_confidence == "excluded" or skill_signal_quality == "excluded_non_it":
                recommended_actions.add("Offre probablement non IT. Matching indisponible.")
            else:
                recommended_actions.add("Données insuffisantes pour calculer un match fiable.")
        elif match_confidence == MatchScoringService.CONFIDENCE_LOW:
            risk_flags.add("insufficient_job_technical_signal")

        # Job active status check
        now = timezone.now()
        is_active = True
        if job.status != "active":
            is_active = False
        if job.expires_at and job.expires_at < now:
            is_active = False

        if not is_active:
            risk_flags.add("job_may_be_expired")

        # Profile complete check
        if profile.profile_completion_score < 50:
            risk_flags.add("profile_incomplete")
            recommended_actions.add("Complétez votre profil candidat.")

        # Signals
        if not profile.github_url:
            profile_signals.add("profile_signal_missing_github")
            recommended_actions.add("Ajoutez le lien vers votre profil GitHub.")
        if not profile.linkedin_url:
            profile_signals.add("profile_signal_missing_linkedin")
        if not profile.portfolio_url:
            profile_signals.add("profile_signal_missing_portfolio")

        tech_score, strong_skills, missing_req, missing_opt = MatchScoringService._calc_technical_score(profile, job, profile_signals, risk_flags)
        exp_score = MatchScoringService._calc_experience_score(profile, job, risk_flags)
        role_score = MatchScoringService._calc_role_title_score(profile, job)
        lang_score = MatchScoringService._calc_language_score(profile, job, risk_flags, recommended_actions)
        loc_score = MatchScoringService._calc_location_score(profile, job)

        fit_score = (
            tech_score * 0.50
            + exp_score * 0.20
            + role_score * 0.15
            + lang_score * 0.15
        )

        if missing_req:
            first_missing = missing_req[0]["name"]
            recommended_actions.add(f"Priorité : ajoutez {first_missing} à votre plan d'apprentissage. Mettez à jour votre CV si vous avez déjà utilisé {first_missing}.")
        elif missing_opt:
            recommended_actions.add("Votre profil couvre les compétences principales. Renforcez les compétences optionnelles pour améliorer votre score.")
        else:
            recommended_actions.add("Votre profil est bien aligné avec cette offre. Vérifiez les conditions de mobilité/contrat puis postulez sur la source.")

        fit_score = max(0, min(100, round(fit_score)))
        if match_confidence == MatchScoringService.CONFIDENCE_UNAVAILABLE:
            fit_score = min(fit_score, 25)

        return FitScoreResult(
            fit_score=fit_score,
            match_confidence=match_confidence,
            technical_skills_score=tech_score,
            experience_score=exp_score,
            role_title_score=role_score,
            language_score=lang_score,
            location_score=loc_score,
            strong_skills=strong_skills,
            missing_required_skills=missing_req,
            missing_optional_skills=missing_opt,
            risk_flags=sorted(list(risk_flags)),
            profile_signals=sorted(list(profile_signals)),
            recommended_actions=sorted(list(recommended_actions)),
        )

    @staticmethod
    def _has_strong_it_context(job: NormalizedJob) -> bool:
        classification_json = job.classification_json or {}
        if classification_json.get("confidence") != "high":
            return False

        family = classification_json.get("family")
        strong_context_families = {
            "data_ai_bi",
            "devops_cloud_sre",
            "cybersecurity",
            "qa_testing",
            "systems_network",
            "database",
            "erp_crm",
            "it_support",
            "it_project_product_analysis",
            "it_training_apprenticeship",
        }
        if family in strong_context_families:
            return True

        description = (job.description or "").lower()
        strong_description_terms = [
            "environnement technique",
            "stack technique",
            "architecture logicielle",
            "système d'information",
            "application métier",
            "développement logiciel",
            "developpement logiciel",
            "ingénierie logicielle",
            "ingenierie logicielle",
        ]
        return any(term in description for term in strong_description_terms)

    @staticmethod
    def _filter_noisy_skills(missing_skills, profile_skills_normalized):
        noisy_baseline = {
            "json", "xml", "yaml", "csv", "markdown", "http", "https", "agile", "scrum",
            "documentation", "office tools", "microsoft office", "pack office"
        }
        json_impliers = {
            "javascript", "typescript", "node.js", "rest api", "api rest", "restful api",
            "frontend development", "backend development", "full-stack development",
            "django", "flask", "fastapi", "express", "spring", "asp.net"
        }
        frontend_impliers = {
            "react", "angular", "vue.js", "frontend development", "full-stack development"
        }

        filtered = []
        for s in missing_skills:
            name_norm = normalize_skill_text(s.get("name") or "") or (s.get("name") or "").lower().strip()

            # JSON rule
            if name_norm == "json":
                if any(imp in profile_skills_normalized for imp in json_impliers):
                    continue

            # Baseline noisy (except advanced versions)
            if name_norm in noisy_baseline:
                if name_norm != "json":
                    continue

            # HTML/CSS rule (only if optional)
            if s.get("requirement_type") == "optional" and name_norm in ["html", "css"]:
                if any(imp in profile_skills_normalized for imp in frontend_impliers):
                    continue

            filtered.append(s)

        return filtered

    @staticmethod
    def _calc_technical_score(profile, job, profile_signals, risk_flags):
        # Profile skills
        profile_skills_normalized = set()
        for profile_skill in ProfileSkill.objects.filter(profile=profile):
            skill_name = profile_skill.normalized_name or profile_skill.raw_name
            normalized_skill_name = normalize_skill_text(skill_name)
            if normalized_skill_name:
                profile_skills_normalized.add(normalized_skill_name)

        strong_skills = []
        missing_req = []
        missing_opt = []

        job_skills = list(job.job_skills.select_related("skill").all())
        tech_job_skills = [js for js in job_skills if js.skill.category in TECH_CATEGORIES]
        req_skills = [js for js in tech_job_skills if js.requirement_type == RequirementType.REQUIRED]
        opt_skills = [js for js in tech_job_skills if js.requirement_type == RequirementType.OPTIONAL]

        if not req_skills and tech_job_skills:
            profile_signals.add("low_confidence_job_skills")
            risk_flags.add("no_required_skills_extracted")
        elif not req_skills:
            risk_flags.add("no_required_skills_extracted")
            risk_flags.add("insufficient_job_technical_signal")

        # Compare required
        req_matched = 0
        for js in req_skills:
            skill_name = js.skill.canonical_name
            normalized_skill_name = normalize_skill_text(skill_name)
            if normalized_skill_name and normalized_skill_name in profile_skills_normalized:
                req_matched += 1
                strong_skills.append({"name": skill_name, "type": "required"})
            else:
                missing_req.append({"name": skill_name, "requirement_type": "required"})

        # Compare optional
        opt_matched = 0
        for js in opt_skills:
            skill_name = js.skill.canonical_name
            normalized_skill_name = normalize_skill_text(skill_name)
            if normalized_skill_name and normalized_skill_name in profile_skills_normalized:
                opt_matched += 1
                strong_skills.append({"name": skill_name, "type": "optional"})
            else:
                missing_opt.append({"name": skill_name, "requirement_type": "optional"})

        if missing_req:
            risk_flags.add("missing_required_skills")

        req_score = (req_matched / len(req_skills) * 100) if req_skills else 0
        opt_score = (opt_matched / len(opt_skills) * 100) if opt_skills else 50

        tech_score = (req_score * 0.8) + (opt_score * 0.2)

        missing_req = MatchScoringService._filter_noisy_skills(missing_req, profile_skills_normalized)
        missing_opt = MatchScoringService._filter_noisy_skills(missing_opt, profile_skills_normalized)

        return max(0, min(100, round(tech_score))), strong_skills, missing_req, missing_opt

    @staticmethod
    def _calc_experience_score(profile, job, risk_flags):
        p_years = profile.years_experience
        p_level = profile.current_level.lower() if profile.current_level else ""
        j_level = job.experience_level.lower() if job.experience_level else ""

        if "intern" in j_level or "student" in j_level or "apprentice" in j_level:
            if "intern" in p_level or "student" in p_level or "junior" in p_level or (p_years is not None and p_years <= 1):
                return 100
            return 80

        if "junior" in j_level:
            if p_years is not None and p_years >= 0.5:
                return 100
            if "junior" in p_level or "mid" in p_level or "senior" in p_level:
                return 100
            if "intern" in p_level or "student" in p_level:
                return 40
            return 60

        if "mid" in j_level:
            if p_years is not None:
                if p_years >= 2:
                    return 100
                if p_years >= 1:
                    return 70
            return 40

        if "senior" in j_level or "lead" in j_level:
            if p_years is not None:
                if p_years >= 5:
                    return 100
                if p_years >= 3:
                    risk_flags.add("experience_too_low")
                    return 60
            risk_flags.add("experience_too_low")
            return 30

        risk_flags.add("experience_unknown")
        return 60

    @staticmethod
    def _calc_role_title_score(profile, job):
        p_roles = [r.lower() for r in (profile.target_roles or []) if r]
        j_title = job.title.lower() if job.title else ""

        if not p_roles and j_title:
            return 60
        if not p_roles and not j_title:
            return 60

        for role in p_roles:
            if role in j_title:
                return 100

        if p_roles and j_title:
            return 50

        return 60

    @staticmethod
    def _calc_language_score(profile, job, risk_flags, recommended_actions):
        j_lang_req = job.language_requirements_json or {}
        p_french = (profile.french_level or "").strip().lower()
        p_english = profile.english_level.lower() if profile.english_level else ""
        has_french_level = p_french not in MISSING_FRENCH_LEVELS

        # Check if job explicitly requires English
        req_english = False
        if isinstance(j_lang_req, dict) and j_lang_req.get("english"):
            req_english = True
        elif isinstance(j_lang_req, list):
            req_english = any("english" in str(x).lower() for x in j_lang_req)

        # Basic France-first check
        france_first = job.country.lower() == "france" if job.country else True

        score = 55
        if not j_lang_req:
            risk_flags.add("job_language_unknown")
        if france_first and not has_french_level:
            risk_flags.add("french_level_missing")
            recommended_actions.add("Renseignez votre niveau de français.")
            score = 40
        elif req_english and not p_english:
            risk_flags.add("english_level_missing")
            score = min(score, 60)

        if has_french_level:
            score = max(score, 70)

        if has_french_level and p_english and j_lang_req:
            score = 85

        return max(0, min(100, score))

    @staticmethod
    def _calc_location_score(profile, job):
        j_country = job.country.lower() if job.country else ""
        j_remote = job.remote_type.lower() if job.remote_type else ""

        p_remote_pref = profile.remote_preference.lower() if profile.remote_preference else ""
        p_relocation = profile.relocation_preference

        if not j_country and not j_remote:
            return 45

        # Remote
        if "remote" in j_remote or "télétravail" in j_remote:
            if p_remote_pref in ["remote_only", "hybrid", "any"] or not p_remote_pref:
                return 75
            return 60

        if j_country == "france" or j_country == "fr":
            if p_relocation:
                return 65
            return 55

        if not j_country:
            return 45

        return 50
