import re
from typing import Dict

from apps.jobs.models import (
    NormalizedJob,
    RequirementType,
)
from apps.skills.services.ambiguity import (
    evidence_candidate_for_match,
    is_allowed_skill_match,
    normalize_context_text,
)
from apps.skills.services.normalizer import SkillExtractionResult
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

STRONG_REQUIREMENT_CONTEXT_PATTERN = re.compile(
    r"\b("
    r"maitrise de|"
    r"competences techniques indispensables|"
    r"indispensable|"
    r"exige|"
    r"obligatoire|"
    r"stack technique|"
    r"competences techniques|"
    r"environnement technique|"
    r"profil recherche|"
    r"required|"
    r"mandatory|"
    r"must have|"
    r"strong experience with|"
    r"proficiency in|"
    r"hands on experience with"
    r")\b"
)

class JobSkillExtractionService:
    @staticmethod
    def extract_for_job(job: NormalizedJob) -> SkillExtractionResult:
        combined_text = normalize_context_text(f"{job.title} {job.description}")

        required_raw = job.required_skills_json if isinstance(job.required_skills_json, list) else []
        optional_raw = job.optional_skills_json if isinstance(job.optional_skills_json, list) else []

        raw_skills_dict: Dict[str, dict] = {}

        # Check description context
        strong_requirement_context = bool(STRONG_REQUIREMENT_CONTEXT_PATTERN.search(combined_text))

        for req in required_raw:
            if isinstance(req, str) and req.strip():
                if any(g in req.lower() for g in GENERIC_FT_LABELS):
                    raw_skills_dict[req] = {"type": RequirementType.DETECTED.value, "confidence": "0.400"}
                else:
                    raw_skills_dict[req] = {"type": RequirementType.REQUIRED.value, "confidence": "1.000"}

        for opt in optional_raw:
            if isinstance(opt, str) and opt.strip() and opt not in raw_skills_dict:
                if any(g in opt.lower() for g in GENERIC_FT_LABELS):
                    raw_skills_dict[opt] = {"type": RequirementType.DETECTED.value, "confidence": "0.400"}
                elif strong_requirement_context:
                    raw_skills_dict[opt] = {"type": RequirementType.REQUIRED.value, "confidence": "1.000"}
                else:
                    raw_skills_dict[opt] = {"type": RequirementType.OPTIONAL.value, "confidence": "1.000"}

        # Find aliases in text
        aliases = list(
            SkillAlias.objects.filter(skill__is_active=True)
            .select_related("skill")
            .values("normalized_alias", "skill__canonical_name")
        )
        aliases.sort(key=lambda row: len(row["normalized_alias"]), reverse=True)

        for row in aliases:
            alias = row["normalized_alias"]
            if not alias or (len(alias) < 2 and alias not in {"c", "r"}):
                continue
            if alias.isalnum():
                pattern = rf"\b{re.escape(alias)}\b"
                if re.search(pattern, combined_text):
                    if alias not in raw_skills_dict and is_allowed_skill_match(
                        raw_text=alias,
                        canonical_name=row["skill__canonical_name"],
                        alias=alias,
                        context=combined_text,
                    ):
                        req_type = RequirementType.REQUIRED.value if strong_requirement_context else RequirementType.DETECTED.value
                        conf = "1.000" if strong_requirement_context else "0.700"
                        candidate = evidence_candidate_for_match(
                            alias=alias,
                            canonical_name=row["skill__canonical_name"],
                            context=combined_text,
                        )
                        raw_skills_dict[candidate] = {"type": req_type, "confidence": conf}
            else:
                if alias in combined_text:
                    if alias not in raw_skills_dict and is_allowed_skill_match(
                        raw_text=alias,
                        canonical_name=row["skill__canonical_name"],
                        alias=alias,
                        context=combined_text,
                    ):
                        req_type = RequirementType.REQUIRED.value if strong_requirement_context else RequirementType.DETECTED.value
                        conf = "1.000" if strong_requirement_context else "0.700"
                        candidate = evidence_candidate_for_match(
                            alias=alias,
                            canonical_name=row["skill__canonical_name"],
                            context=combined_text,
                        )
                        raw_skills_dict[candidate] = {"type": req_type, "confidence": conf}

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
