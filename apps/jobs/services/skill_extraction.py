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

        from apps.jobs.services.skill_materialization import JobSkillMaterializationService

        materialization_result = JobSkillMaterializationService.materialize_for_job(
            job=job,
            source="rule",
            raw_skills_dict=raw_skills_dict
        )

        from apps.jobs.models import NormalizedJobSkill
        canonical_skills = [s.skill for s in NormalizedJobSkill.objects.filter(job=job).select_related('skill')]

        return SkillExtractionResult(
            canonical_skills=canonical_skills,
            unmatched_candidates=[],
            raw_candidates=list(raw_skills_dict.keys())
        )
