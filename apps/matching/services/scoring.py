from dataclasses import dataclass
from typing import Optional
from apps.profiles.models import CandidateProfile, ProfileSkill
from apps.jobs.models import NormalizedJob, RequirementType
from apps.cvs.models import CVUpload
from apps.skills.services.normalizer import normalize_skill_text
from apps.jobs.services.relevance import TECH_CATEGORIES
from django.conf import settings
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
        enriched_data = MatchScoringService._get_successful_enrichment(job)

        job_skills = list(job.job_skills.select_related("skill").all())
        tech_job_skills = [js for js in job_skills if js.skill.category in TECH_CATEGORIES]
        req_skills = [js for js in tech_job_skills if js.requirement_type == RequirementType.REQUIRED]

        match_confidence = MatchScoringService.CONFIDENCE_UNAVAILABLE
        if it_confidence == "excluded" or skill_signal_quality == "excluded_non_it":
            match_confidence = MatchScoringService.CONFIDENCE_UNAVAILABLE
        elif enriched_data:
            if enriched_data.get("required_skills") or enriched_data.get("optional_skills"):
                match_confidence = MatchScoringService.CONFIDENCE_RELIABLE
            else:
                match_confidence = MatchScoringService.CONFIDENCE_LOW
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
            recommended_actions.add("Complete your candidate profile.")

        # Signals
        if not profile.github_url:
            profile_signals.add("profile_signal_missing_github")
            recommended_actions.add("Add your GitHub profile.")
        if not profile.linkedin_url:
            profile_signals.add("profile_signal_missing_linkedin")
        if not profile.portfolio_url:
            profile_signals.add("profile_signal_missing_portfolio")

        tech_score, strong_skills, missing_req, missing_opt = MatchScoringService._calc_technical_score(profile, job, profile_signals, risk_flags, recommended_actions)
        exp_score = MatchScoringService._calc_experience_score(profile, job, risk_flags)
        role_score = MatchScoringService._calc_role_title_score(profile, job)
        lang_score = MatchScoringService._calc_language_score(profile, job, risk_flags, recommended_actions)
        loc_score = MatchScoringService._calc_location_score(profile, job)

        fit_score = (
            tech_score * 0.45
            + exp_score * 0.20
            + role_score * 0.15
            + lang_score * 0.10
            + loc_score * 0.10
        )
        
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
    def _get_successful_enrichment(job: NormalizedJob) -> dict:
        if not getattr(settings, "JOB_RECOMMENDATIONS_USE_ENRICHED_DATA", False):
            return {}
        if not hasattr(job, "enrichment") or job.enrichment.status != "success":
            return {}
        enriched_data = job.enrichment.validated_output_json or {}
        if not isinstance(enriched_data, dict):
            return {}
        return enriched_data

    @staticmethod
    def _calc_technical_score(profile, job, profile_signals, risk_flags, recommended_actions):
        # Profile skills
        profile_skills_normalized = set()
        for profile_skill in ProfileSkill.objects.filter(profile=profile):
            skill_name = profile_skill.normalized_name or profile_skill.raw_name
            normalized_skill_name = normalize_skill_text(skill_name)
            if normalized_skill_name:
                profile_skills_normalized.add(normalized_skill_name)

        enriched_data = MatchScoringService._get_successful_enrichment(job)
        use_enriched = bool(enriched_data)

        strong_skills = []
        missing_req = []
        missing_opt = []

        if use_enriched:
            en_req = enriched_data.get("required_skills", [])
            en_opt = enriched_data.get("optional_skills", [])
            
            if not en_req and (en_req or en_opt):
                profile_signals.add("low_confidence_job_skills")
                risk_flags.add("no_required_skills_extracted")
            elif not en_req:
                risk_flags.add("no_required_skills_extracted")
                risk_flags.add("insufficient_job_technical_signal")
                
            req_matched = 0
            for skill_dict in en_req:
                skill_name = skill_dict.get("name", "")
                normalized_skill_name = normalize_skill_text(skill_name)
                if normalized_skill_name and normalized_skill_name in profile_skills_normalized:
                    req_matched += 1
                    strong_skills.append({"name": skill_name, "type": "required"})
                else:
                    missing_req.append({"name": skill_name, "requirement_type": "required"})

            opt_matched = 0
            for skill_dict in en_opt:
                skill_name = skill_dict.get("name", "")
                normalized_skill_name = normalize_skill_text(skill_name)
                if normalized_skill_name and normalized_skill_name in profile_skills_normalized:
                    opt_matched += 1
                    strong_skills.append({"name": skill_name, "type": "optional"})
                else:
                    missing_opt.append({"name": skill_name, "requirement_type": "optional"})
            
            if missing_req:
                risk_flags.add("missing_required_skills")
                recommended_actions.add("Add missing required skills to your learning plan.")
                
            req_score = (req_matched / len(en_req) * 100) if en_req else 0
            opt_score = (opt_matched / len(en_opt) * 100) if en_opt else 50
            tech_score = (req_score * 0.8) + (opt_score * 0.2)
            
            return max(0, min(100, round(tech_score))), strong_skills, missing_req, missing_opt

        # Fallback to deterministic skills
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
            recommended_actions.add("Add missing required skills to your learning plan.")

        req_score = (req_matched / len(req_skills) * 100) if req_skills else 0
        opt_score = (opt_matched / len(opt_skills) * 100) if opt_skills else 50

        tech_score = (req_score * 0.8) + (opt_score * 0.2)
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
            recommended_actions.add("Complete your French level.")
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
