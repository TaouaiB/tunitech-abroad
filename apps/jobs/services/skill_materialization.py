import logging
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Optional

from django.db import transaction

from apps.jobs.models import (
    NormalizedJob,
    NormalizedJobSkill,
    RequirementType,
    SkillSource,
    SkillExtractionStatus,
)
from apps.skills.models import Skill, SkillAlias
from apps.skills.services.normalizer import SkillNormalizerService, normalize_skill_text

logger = logging.getLogger(__name__)


def _candidate_name(candidate: Any) -> str:
    if isinstance(candidate, str):
        return candidate.strip()
    if isinstance(candidate, dict):
        for key in ("name", "skill", "label", "libelle"):
            value = candidate.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return ""


def _candidate_confidence(candidate: Any) -> Decimal:
    if not isinstance(candidate, dict):
        return Decimal("1.000")
    value = candidate.get("confidence")
    if value is None:
        return Decimal("1.000")
    try:
        confidence = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal("1.000")
    return max(Decimal("0.000"), min(Decimal("1.000"), confidence)).quantize(Decimal("0.001"))


def _requirement_priority(requirement_type: str) -> int:
    return {
        RequirementType.REQUIRED.value: 3,
        RequirementType.OPTIONAL.value: 2,
        RequirementType.DETECTED.value: 1,
        RequirementType.UNKNOWN.value: 0,
    }.get(requirement_type, 0)

@dataclass(frozen=True)
class JobSkillMaterializationResult:
    job_id: int
    created_count: int
    updated_count: int
    matched_required_count: int
    matched_optional_count: int
    unmatched_count: int
    source: str
    status: str

class JobSkillMaterializationService:
    @classmethod
    def materialize_for_job(
        cls, 
        job: NormalizedJob, 
        *, 
        source: str = "rule", 
        enrichment=None,
        raw_skills_dict: Optional[Dict[str, str]] = None
    ) -> JobSkillMaterializationResult:
        """
        Materializes raw skills into canonical NormalizedJobSkill rows.
        
        If `source="llm"`, it reads from `enrichment.validated_output_json`.
        If `source="rule"`, it reads from `job.required_skills_json` and `job.optional_skills_json`
        unless `raw_skills_dict` is explicitly provided by the extraction service.
        """
        candidate_confidences: dict[str, Decimal] = {}

        def add_candidate(candidate: Any, requirement_type: str) -> None:
            name = _candidate_name(candidate)
            if not name:
                return
            current_type = raw_skills_dict.get(name)
            if current_type is None or _requirement_priority(requirement_type) > _requirement_priority(current_type):
                raw_skills_dict[name] = requirement_type
            candidate_confidences[name] = max(
                candidate_confidences.get(name, Decimal("0.000")),
                _candidate_confidence(candidate),
            )

        if raw_skills_dict:
            raw_skills_dict = {
                str(skill).strip(): requirement_type
                for skill, requirement_type in raw_skills_dict.items()
                if str(skill).strip()
            }
            candidate_confidences = {skill: Decimal("1.000") for skill in raw_skills_dict}
        else:
            raw_skills_dict = {}

        if source == "llm" and enrichment and enrichment.validated_output_json:
            req_list = enrichment.validated_output_json.get("required_skills", [])
            opt_list = enrichment.validated_output_json.get("optional_skills", [])
            for item in req_list:
                add_candidate(item, RequirementType.REQUIRED.value)
            for item in opt_list:
                add_candidate(item, RequirementType.OPTIONAL.value)
        elif not raw_skills_dict:
            # Fallback for rule source without explicit dict
            req_raw = job.required_skills_json if isinstance(job.required_skills_json, list) else []
            opt_raw = job.optional_skills_json if isinstance(job.optional_skills_json, list) else []
            for r in req_raw:
                add_candidate(r, RequirementType.REQUIRED.value)
            for o in opt_raw:
                add_candidate(o, RequirementType.OPTIONAL.value)

        all_raw_skills = list(raw_skills_dict.keys())

        if not all_raw_skills:
            if job.skill_extraction_status == SkillExtractionStatus.PENDING:
                from apps.jobs.services.skill_signals import compute_deterministic_skill_signal_quality

                signal_result = compute_deterministic_skill_signal_quality(job)
                current_quality = (job.skill_signal_quality or "").strip()
                job.skill_extraction_status = SkillExtractionStatus.NOT_ENOUGH_TEXT
                if not current_quality or current_quality == "unknown":
                    job.skill_signal_quality = signal_result.quality
                job.save(update_fields=["skill_extraction_status", "skill_signal_quality"])
            return JobSkillMaterializationResult(
                job_id=job.id,
                created_count=0,
                updated_count=0,
                matched_required_count=0,
                matched_optional_count=0,
                unmatched_count=0,
                source=source,
                status=job.skill_extraction_status
            )

        try:
            # Step 1: Normalize and match candidates
            result = SkillNormalizerService.normalize_many(
                raw_skills=all_raw_skills,
                source_type="job",
                source_id=job.id,
            )

            with transaction.atomic():
                # Step 2: Clear old skills EXCEPT ADMIN source
                admin_skills = list(NormalizedJobSkill.objects.filter(
                    job=job, source=SkillSource.ADMIN.value
                ).values_list('skill_id', flat=True))
                
                NormalizedJobSkill.objects.filter(job=job).exclude(source=SkillSource.ADMIN.value).delete()

                canonical_skills_saved = []
                created_count = 0
                updated_count = 0
                matched_required = 0
                matched_optional = 0

                skill_source_value = SkillSource.LLM.value if source == "llm" else SkillSource.RULE.value

                for skill in result.canonical_skills:
                    if skill.id in admin_skills:
                        continue # Preserved

                    # Determine requirement type
                    req_type = RequirementType.DETECTED.value
                    skill_aliases = {
                        normalize_skill_text(a.normalized_alias)
                        for a in SkillAlias.objects.filter(skill=skill)
                    }
                    
                    confidence = Decimal("0.000")
                    for raw, type_ in raw_skills_dict.items():
                        norm_raw = normalize_skill_text(raw)
                        if norm_raw in skill_aliases:
                            confidence = max(confidence, candidate_confidences.get(raw, Decimal("1.000")))
                            if type_ == RequirementType.REQUIRED.value:
                                req_type = type_
                                break
                            elif type_ == RequirementType.OPTIONAL.value and req_type != RequirementType.REQUIRED.value:
                                req_type = type_

                    NormalizedJobSkill.objects.create(
                        job=job,
                        skill=skill,
                        requirement_type=req_type,
                        source=skill_source_value,
                        confidence=confidence or Decimal("1.000"),
                    )
                    created_count += 1
                    canonical_skills_saved.append((skill, req_type))

                    if req_type == RequirementType.REQUIRED.value:
                        matched_required += 1
                    else:
                        matched_optional += 1

                # Recompute JSON fields for display using canonical names
                new_required = [s.canonical_name for s, t in canonical_skills_saved if t == RequirementType.REQUIRED.value]
                new_optional = [s.canonical_name for s, t in canonical_skills_saved if t in [RequirementType.OPTIONAL.value, RequirementType.DETECTED.value]]

                # Always add admin skills back to JSON arrays
                admin_rows = NormalizedJobSkill.objects.filter(job=job, source=SkillSource.ADMIN.value).select_related('skill')
                for ar in admin_rows:
                    if ar.requirement_type == RequirementType.REQUIRED.value and ar.skill.canonical_name not in new_required:
                        new_required.append(ar.skill.canonical_name)
                    elif ar.requirement_type in [RequirementType.OPTIONAL.value, RequirementType.DETECTED.value] and ar.skill.canonical_name not in new_optional:
                        new_optional.append(ar.skill.canonical_name)

                job.required_skills_json = new_required
                job.optional_skills_json = new_optional
                
                from apps.jobs.services.skill_signals import compute_deterministic_skill_signal_quality
                signal_result = compute_deterministic_skill_signal_quality(job)
                
                job.skill_extraction_status = SkillExtractionStatus.SUCCESS
                job.skill_signal_quality = signal_result.quality
                job.save(update_fields=["required_skills_json", "optional_skills_json", "skill_extraction_status", "skill_signal_quality"])

            return JobSkillMaterializationResult(
                job_id=job.id,
                created_count=created_count,
                updated_count=updated_count,
                matched_required_count=matched_required,
                matched_optional_count=matched_optional,
                unmatched_count=len(result.unmatched_candidates),
                source=source,
                status="success"
            )

        except Exception as e:
            logger.error(f"Error materializing skills for job {job.id}: {e}")
            job.skill_extraction_status = SkillExtractionStatus.FAILED
            job.save(update_fields=["skill_extraction_status"])
            return JobSkillMaterializationResult(
                job_id=job.id,
                created_count=0,
                updated_count=0,
                matched_required_count=0,
                matched_optional_count=0,
                unmatched_count=0,
                source=source,
                status="failed"
            )
