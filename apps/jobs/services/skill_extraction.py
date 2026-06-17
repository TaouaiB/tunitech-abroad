import re
from typing import Dict

from django.db import transaction

from apps.jobs.models import (
    NormalizedJob,
    NormalizedJobSkill,
    RequirementType,
    SkillSource,
    SkillExtractionStatus,
)
from apps.skills.services.normalizer import SkillNormalizerService, SkillExtractionResult, normalize_skill_text
from apps.skills.models import SkillAlias

GENERIC_FT_LABELS = [
    "application web",
    "concevoir une application web",
    "concevoir et développer une solution digitale",
    "développer un logiciel, un système d'informations, une application",
    "analyser, exploiter, structurer des données",
    "recueillir et analyser les besoins client",
    "coder des données",
    "tester un logiciel",
    "collaborer avec des équipes multidisciplinaires",
    "optimiser les processus de qualité pour assurer la fiabilité des logiciels",
    "développer un logiciel",
    "application métier",
]

class JobSkillExtractionService:
    @staticmethod
    def extract_for_job(job: NormalizedJob) -> SkillExtractionResult:
        description_lower = (job.description or "").lower()
        combined_text = f"{job.title} {job.description}".lower()
        
        required_raw = job.required_skills_json if isinstance(job.required_skills_json, list) else []
        optional_raw = job.optional_skills_json if isinstance(job.optional_skills_json, list) else []

        raw_skills_dict: Dict[str, str] = {}
        
        # Check description context
        strong_requirement_context = bool(re.search(r'(maîtrise de|maitrise de|compétences techniques indispensables|indispensable|exigé|exige|obligatoire|stack technique|compétences techniques|environnement technique|profil recherché)', combined_text))

        for req in required_raw:
            if isinstance(req, str) and req.strip():
                if any(g in req.lower() for g in GENERIC_FT_LABELS):
                    raw_skills_dict[req] = RequirementType.DETECTED.value # Downgrade generic FT
                else:
                    raw_skills_dict[req] = RequirementType.REQUIRED.value
                    
        for opt in optional_raw:
            if isinstance(opt, str) and opt.strip() and opt not in raw_skills_dict:
                if any(g in opt.lower() for g in GENERIC_FT_LABELS):
                    raw_skills_dict[opt] = RequirementType.DETECTED.value
                elif strong_requirement_context:
                    raw_skills_dict[opt] = RequirementType.REQUIRED.value
                else:
                    raw_skills_dict[opt] = RequirementType.OPTIONAL.value
                
        # Find aliases in text
        aliases = list(SkillAlias.objects.filter(skill__is_active=True).values_list('normalized_alias', flat=True))
        aliases.sort(key=len, reverse=True)
        
        for alias in aliases:
            if not alias or len(alias) < 2:
                continue
            if alias.isalnum():
                pattern = rf"\b{re.escape(alias)}\b"
                if re.search(pattern, combined_text):
                    if alias not in raw_skills_dict:
                        req_type = RequirementType.REQUIRED.value if strong_requirement_context else RequirementType.DETECTED.value
                        raw_skills_dict[alias] = req_type
            else:
                if alias in combined_text:
                    if alias not in raw_skills_dict:
                        req_type = RequirementType.REQUIRED.value if strong_requirement_context else RequirementType.DETECTED.value
                        raw_skills_dict[alias] = req_type

        all_raw_skills = list(raw_skills_dict.keys())

        result = SkillNormalizerService.normalize_many(
            raw_skills=all_raw_skills,
            source_type="job",
            source_id=job.id,
        )

        with transaction.atomic():
            # Clear old skills
            NormalizedJobSkill.objects.filter(job=job).delete()
            
            canonical_skills_saved = []

            for skill in result.canonical_skills:
                req_type = RequirementType.DETECTED.value
                skill_aliases = [
                    normalize_skill_text(a.normalized_alias)
                    for a in SkillAlias.objects.filter(skill=skill)
                ]
                
                for raw, type_ in raw_skills_dict.items():
                    norm_raw = normalize_skill_text(raw)
                    if norm_raw in skill_aliases:
                        if type_ == RequirementType.REQUIRED.value:
                            req_type = type_
                            break
                        elif type_ == RequirementType.OPTIONAL.value and req_type != RequirementType.REQUIRED.value:
                            req_type = type_
                
                NormalizedJobSkill.objects.create(
                    job=job,
                    skill=skill,
                    requirement_type=req_type,
                    source=SkillSource.RULE.value,
                    confidence=1.0,
                )
                canonical_skills_saved.append((skill, req_type))

            # Recalculate required/optional json based on actual normalized skills
            new_required = [s.canonical_name for s, t in canonical_skills_saved if t == RequirementType.REQUIRED.value]
            new_optional = [s.canonical_name for s, t in canonical_skills_saved if t in [RequirementType.OPTIONAL.value, RequirementType.DETECTED.value]]

            # Skill Signal Quality Logic
            skill_signal_quality = "unknown"
            classification_json = job.classification_json or {}
            family = classification_json.get("family", "unknown")
            is_it = classification_json.get("is_it", False)

            if not is_it or family == "non_it":
                skill_signal_quality = "excluded_non_it"
            else:
                if len(new_required) > 0:
                    skill_signal_quality = "strong"
                elif len(new_optional) > 0:
                    skill_signal_quality = "partial"
                elif any(any(g in r.lower() for g in GENERIC_FT_LABELS) for r in all_raw_skills):
                    skill_signal_quality = "generic_only"
                else:
                    skill_signal_quality = "missing"

            job.required_skills_json = new_required
            job.optional_skills_json = new_optional
            job.skill_extraction_status = SkillExtractionStatus.SUCCESS
            job.skill_signal_quality = skill_signal_quality
            job.save(update_fields=["required_skills_json", "optional_skills_json", "skill_extraction_status", "skill_signal_quality"])

        return result
