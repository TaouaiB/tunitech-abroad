from dataclasses import dataclass
from typing import List, Optional, Set, Dict
from django.db import transaction
from django.db.models import F
from apps.skills.models import Skill, SkillAlias, UnmatchedSkillCandidate
import re
import unicodedata

@dataclass
class SkillExtractionResult:
    canonical_skills: List[Skill]
    unmatched_candidates: List[UnmatchedSkillCandidate]
    raw_candidates: List[str]
    confidence: Optional[float] = None

def normalize_skill_text(text: str | None) -> str:
    if not text:
        return ""
    text = text.lower()
    text = ''.join(c for c in unicodedata.normalize('NFKD', text) if not unicodedata.combining(c))
    text = re.sub(r'[^\w\s#\.+]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

class SkillNormalizerService:
    @classmethod
    def normalize_many(
        cls,
        raw_skills: List[str],
        source_type: str,
        source_id: Optional[int] = None,
    ) -> SkillExtractionResult:
        if not raw_skills:
            return SkillExtractionResult(canonical_skills=[], unmatched_candidates=[], raw_candidates=[])
            
        # Deduplicate raw candidates keeping order
        unique_raw_skills = list(dict.fromkeys(skill for skill in raw_skills if skill and skill.strip()))
        
        canonical_skills_set: Set[Skill] = set()
        unmatched_candidates_list: List[UnmatchedSkillCandidate] = []
        
        normalized_to_raw: Dict[str, str] = {}
        for raw in unique_raw_skills:
            normalized = normalize_skill_text(raw)
            if normalized:
                if normalized not in normalized_to_raw:
                    normalized_to_raw[normalized] = raw
                    
        normalized_texts = list(normalized_to_raw.keys())
        
        # Look up aliases
        aliases = SkillAlias.objects.filter(
            normalized_alias__in=normalized_texts,
            skill__is_active=True
        ).select_related('skill')
        alias_map = {alias.normalized_alias: alias.skill for alias in aliases}
        
        with transaction.atomic():
            for normalized, raw in normalized_to_raw.items():
                if normalized in alias_map:
                    canonical_skills_set.add(alias_map[normalized])
                else:
                    candidate, created = UnmatchedSkillCandidate.objects.get_or_create(
                        normalized_text=normalized,
                        source_type=source_type,
                        defaults={
                            'raw_skill_text': raw,
                            'source_model': None,
                            'source_object_id': source_id,
                            'occurrence_count': 1,
                        }
                    )
                    if not created:
                        UnmatchedSkillCandidate.objects.filter(pk=candidate.pk).update(
                            occurrence_count=F('occurrence_count') + 1
                        )
                        candidate.refresh_from_db(fields=['occurrence_count'])
                    
                    unmatched_candidates_list.append(candidate)
        
        return SkillExtractionResult(
            canonical_skills=list(canonical_skills_set),
            unmatched_candidates=unmatched_candidates_list,
            raw_candidates=unique_raw_skills
        )
