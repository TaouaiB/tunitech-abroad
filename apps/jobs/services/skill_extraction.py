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


class JobSkillExtractionService:
    @staticmethod
    def extract_for_job(job: NormalizedJob) -> SkillExtractionResult:
        combined_text = f"{job.title} {job.description}".lower()
        
        required_raw = job.required_skills_json if isinstance(job.required_skills_json, list) else []
        optional_raw = job.optional_skills_json if isinstance(job.optional_skills_json, list) else []

        raw_skills_dict: Dict[str, str] = {}
        
        for req in required_raw:
            if isinstance(req, str) and req.strip():
                raw_skills_dict[req] = RequirementType.REQUIRED.value
        for opt in optional_raw:
            if isinstance(opt, str) and opt.strip() and opt not in raw_skills_dict:
                raw_skills_dict[opt] = RequirementType.OPTIONAL.value
                
        # Find aliases in text
        aliases = list(SkillAlias.objects.filter(skill__is_active=True).values_list('normalized_alias', flat=True))
        
        # Sort aliases by length descending so longer phrases match first
        aliases.sort(key=len, reverse=True)
        
        for alias in aliases:
            if not alias or len(alias) < 2:
                continue
            # Simple text match (could be improved with regex \b boundaries)
            # But doing \b on things with symbols like c++ or c# is tricky
            # We will just do a simple substring for now, or word boundary if purely alphanumeric
            if alias.isalnum():
                pattern = rf"\b{re.escape(alias)}\b"
                if re.search(pattern, combined_text):
                    if alias not in raw_skills_dict:
                        raw_skills_dict[alias] = RequirementType.DETECTED.value
            else:
                if alias in combined_text:
                    if alias not in raw_skills_dict:
                        raw_skills_dict[alias] = RequirementType.DETECTED.value

        all_raw_skills = list(raw_skills_dict.keys())
        required_skills = [
            raw for raw, requirement_type in raw_skills_dict.items()
            if requirement_type == RequirementType.REQUIRED.value
        ]
        optional_skills = [
            raw for raw, requirement_type in raw_skills_dict.items()
            if requirement_type == RequirementType.OPTIONAL.value
        ]

        result = SkillNormalizerService.normalize_many(
            raw_skills=all_raw_skills,
            source_type="job",
            source_id=job.id,
        )

        with transaction.atomic():
            for skill in result.canonical_skills:
                # Approximate requirement type mapping
                # We need to find which raw skill mapped to this canonical skill
                # Then map that raw skill to requirement type
                req_type = RequirementType.DETECTED.value
                skill_aliases = [
                    normalize_skill_text(alias.normalized_alias)
                    for alias in SkillAlias.objects.filter(skill=skill)
                ]
                
                # Check which of our raw_skills mapped to it
                for raw, type_ in raw_skills_dict.items():
                    norm_raw = normalize_skill_text(raw)
                    if norm_raw in skill_aliases:
                        # Prioritize REQUIRED over OPTIONAL over DETECTED
                        if type_ == RequirementType.REQUIRED.value:
                            req_type = type_
                            break
                        elif type_ == RequirementType.OPTIONAL.value and req_type != RequirementType.REQUIRED.value:
                            req_type = type_

                NormalizedJobSkill.objects.update_or_create(
                    job=job,
                    skill=skill,
                    requirement_type=req_type,
                    defaults={
                        "source": SkillSource.RULE.value,
                        "confidence": 1.0,
                    }
                )

            job.required_skills_json = required_skills
            job.optional_skills_json = optional_skills
            job.skill_extraction_status = SkillExtractionStatus.SUCCESS
            job.save(update_fields=["required_skills_json", "optional_skills_json", "skill_extraction_status"])

        return result
