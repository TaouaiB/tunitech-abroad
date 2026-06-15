import hashlib
from datetime import timedelta
from django.utils import timezone
from django.conf import settings

from apps.matching.models import QuickMatchSession
from apps.jobs.models import NormalizedJob, RequirementType
from apps.skills.services.normalizer import normalize_skill_text

class QuickMatchRateLimitExceeded(Exception):
    pass

MISSING_FRENCH_LEVELS = {"", "none", "no", "a0"}

class QuickMatchService:
    @staticmethod
    def _has_french_level(french_level: str | None) -> bool:
        return (french_level or "").strip().lower() not in MISSING_FRENCH_LEVELS

    @staticmethod
    def run_quick_match(
        session_key: str,
        job: NormalizedJob,
        entered_skills: list[str],
        experience_level: str,
        french_level: str,
        ip_address: str | None = None,
    ) -> QuickMatchSession:
        
        if not session_key:
            session_key = "anonymous_session"

        # Rate Limiting
        session_hash = hashlib.sha256(f"{settings.SECRET_KEY}:{session_key}".encode()).hexdigest()
        ip_hash = hashlib.sha256(f"{settings.SECRET_KEY}:{ip_address}".encode()).hexdigest() if ip_address else ""
        
        one_hour_ago = timezone.now() - timedelta(hours=1)
        
        session_count = QuickMatchSession.objects.filter(
            session_key_hash=session_hash,
            created_at__gte=one_hour_ago
        ).count()
        if session_count >= 10:
            raise QuickMatchRateLimitExceeded("Too many quick matches from this session.")
            
        if ip_hash:
            ip_count = QuickMatchSession.objects.filter(
                ip_hash=ip_hash,
                created_at__gte=one_hour_ago
            ).count()
            if ip_count >= 20:
                raise QuickMatchRateLimitExceeded("Too many quick matches from this IP.")

        # Normalize entered skills
        normalized_skills = [normalize_skill_text(s) for s in entered_skills]
        normalized_skills = [s for s in normalized_skills if s]

        # Process Job Skills
        job_skills = list(job.job_skills.select_related("skill").all())
        req_skills = [js for js in job_skills if js.requirement_type == RequirementType.REQUIRED]
        opt_skills = [js for js in job_skills if js.requirement_type == RequirementType.OPTIONAL]
        
        if not req_skills and job_skills:
            req_skills = job_skills
            opt_skills = []

        matched_skills = []
        missing_skills = []
        
        req_matched = 0
        for js in req_skills:
            skill_name = js.skill.canonical_name
            normalized_skill_name = normalize_skill_text(skill_name)
            if normalized_skill_name in normalized_skills:
                req_matched += 1
                matched_skills.append({"name": skill_name, "type": "required"})
            else:
                missing_skills.append({"name": skill_name, "requirement_type": "required"})
                
        opt_matched = 0
        for js in opt_skills:
            skill_name = js.skill.canonical_name
            normalized_skill_name = normalize_skill_text(skill_name)
            if normalized_skill_name in normalized_skills:
                opt_matched += 1
                matched_skills.append({"name": skill_name, "type": "optional"})
            else:
                missing_skills.append({"name": skill_name, "requirement_type": "optional"})

        req_score = (req_matched / len(req_skills) * 100) if req_skills else 100
        opt_score = (opt_matched / len(opt_skills) * 100) if opt_skills else 100
        tech_score = (req_score * 0.8) + (opt_score * 0.2)
        tech_score = max(0, min(100, round(tech_score)))

        # Experience score fallback
        exp_score = 70
        j_level = job.experience_level.lower() if job.experience_level else ""
        p_level = experience_level.lower() if experience_level else ""
        
        if "intern" in j_level or "student" in j_level:
            exp_score = 100 if "intern" in p_level or "student" in p_level or "junior" in p_level else 80
        elif "junior" in j_level:
            exp_score = 100 if "junior" in p_level or "mid" in p_level or "senior" in p_level else 40
        elif "mid" in j_level:
            exp_score = 100 if "mid" in p_level else 40
        elif "senior" in j_level:
            exp_score = 100 if "senior" in p_level else 30

        # Language score fallback
        france_first = job.country.lower() == "france" if job.country else True
        lang_score = 70
        has_french_level = QuickMatchService._has_french_level(french_level)
        
        if france_first and not has_french_level:
            lang_score = 40
        elif has_french_level:
            lang_score = 80

        # Fit score (assume 70 for role and location since we don't have them in quick match)
        fit_score = tech_score * 0.45 + exp_score * 0.20 + 70 * 0.15 + lang_score * 0.10 + 70 * 0.10
        fit_score = max(0, min(100, round(fit_score)))

        risk_flags = []
        if any(ms['requirement_type'] == 'required' for ms in missing_skills):
            risk_flags.append('missing_required_skills')
        if france_first and not has_french_level:
            risk_flags.append('french_level_missing')
            
        expires_at = timezone.now() + timedelta(hours=24)
        
        session = QuickMatchSession.objects.create(
            session_key_hash=session_hash,
            ip_hash=ip_hash,
            job=job,
            entered_skills_json=entered_skills,
            normalized_skills_json=normalized_skills,
            experience_level=experience_level,
            french_level=french_level,
            estimated_fit_score=fit_score,
            matched_skills_json=matched_skills,
            missing_skills_json=missing_skills,
            risk_flags_json=risk_flags,
            expires_at=expires_at
        )
        
        return session
