import re
from decimal import Decimal
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
from apps.skills.services.extraction_policy import classify_skill_candidate
from apps.skills.services.normalizer import SkillExtractionResult, normalize_skill_text
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

        def add_policy_candidate(raw: str, requirement_type: str, confidence: str, canonical_name: str | None = None, category: str | None = None) -> None:
            decision = classify_skill_candidate(raw_text=raw, canonical_name=canonical_name, category=category)
            if not decision.materialize:
                return
            if not decision.can_be_required and requirement_type == RequirementType.REQUIRED.value:
                requirement_type = RequirementType.DETECTED.value
            if decision.confidence_ceiling is not None:
                confidence = str(min(decision.confidence_ceiling, Decimal(confidence)).quantize(Decimal("0.001")))
            raw_skills_dict[raw] = {"type": requirement_type, "confidence": confidence}

        # Check description context
        strong_requirement_context = bool(STRONG_REQUIREMENT_CONTEXT_PATTERN.search(combined_text))

        for req in required_raw:
            if isinstance(req, str) and req.strip():
                if any(g in req.lower() for g in GENERIC_FT_LABELS):
                    add_policy_candidate(req, RequirementType.DETECTED.value, "0.400")
                else:
                    add_policy_candidate(req, RequirementType.REQUIRED.value, "1.000")

        for opt in optional_raw:
            if isinstance(opt, str) and opt.strip() and opt not in raw_skills_dict:
                if any(g in opt.lower() for g in GENERIC_FT_LABELS):
                    add_policy_candidate(opt, RequirementType.DETECTED.value, "0.400")
                elif strong_requirement_context:
                    add_policy_candidate(opt, RequirementType.REQUIRED.value, "1.000")
                else:
                    add_policy_candidate(opt, RequirementType.OPTIONAL.value, "1.000")

        # Find aliases in text
        aliases = list(
            SkillAlias.objects.filter(skill__is_active=True)
            .select_related("skill")
            .values("normalized_alias", "skill__canonical_name", "skill__category")
        )
        aliases.sort(key=lambda row: len(row["normalized_alias"]), reverse=True)
        occupied_spans: list[tuple[int, int]] = []

        def pattern_for_alias(alias: str) -> re.Pattern:
            escaped = re.escape(alias)
            return re.compile(rf"(?<![\w+#]){escaped}(?![\w+#])")

        def span_available(start: int, end: int) -> bool:
            return all(end <= used_start or start >= used_end for used_start, used_end in occupied_spans)

        for row in aliases:
            alias = row["normalized_alias"]
            if not alias or (len(alias) < 2 and alias not in {"c", "r"}):
                continue
            if alias in {normalize_skill_text(key) for key in raw_skills_dict}:
                continue
            for match in pattern_for_alias(alias).finditer(combined_text):
                if not span_available(match.start(), match.end()):
                    continue
                if not is_allowed_skill_match(
                    raw_text=alias,
                    canonical_name=row["skill__canonical_name"],
                    alias=alias,
                    context=combined_text,
                ):
                    continue
                req_type = RequirementType.REQUIRED.value if strong_requirement_context else RequirementType.DETECTED.value
                conf = "1.000" if strong_requirement_context else "0.700"
                candidate = evidence_candidate_for_match(
                    alias=alias,
                    canonical_name=row["skill__canonical_name"],
                    context=combined_text,
                )
                before_count = len(raw_skills_dict)
                add_policy_candidate(
                    candidate,
                    req_type,
                    conf,
                    canonical_name=row["skill__canonical_name"],
                    category=row["skill__category"],
                )
                if len(raw_skills_dict) > before_count:
                    occupied_spans.append((match.start(), match.end()))
                break

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
