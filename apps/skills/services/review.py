from django.utils import timezone
from apps.skills.models import Skill, SkillAlias, UnmatchedSkillCandidate
from apps.skills.services.normalizer import normalize_skill_text

class UnmatchedSkillReviewService:
    @classmethod
    def map_candidate(cls, candidate_id: int, skill_id: int, reviewed_by) -> UnmatchedSkillCandidate:
        if not reviewed_by.is_staff:
            raise PermissionError("Only staff users can review skills.")
            
        candidate = UnmatchedSkillCandidate.objects.get(id=candidate_id)
        skill = Skill.objects.get(id=skill_id)
        
        candidate.mapped_skill = skill
        candidate.status = 'mapped'
        candidate.reviewed_by = reviewed_by
        candidate.reviewed_at = timezone.now()
        candidate.save()
        
        # Create alias if it doesn't exist
        alias_normalized = candidate.normalized_text
        if not SkillAlias.objects.filter(normalized_alias=alias_normalized).exists():
            SkillAlias.objects.create(
                skill=skill,
                alias=candidate.raw_skill_text,
                normalized_alias=alias_normalized,
                language='unknown'
            )
            
        return candidate

    @classmethod
    def ignore_candidate(cls, candidate_id: int, reviewed_by) -> UnmatchedSkillCandidate:
        if not reviewed_by.is_staff:
            raise PermissionError("Only staff users can review skills.")
            
        candidate = UnmatchedSkillCandidate.objects.get(id=candidate_id)
        candidate.status = 'ignored'
        candidate.reviewed_by = reviewed_by
        candidate.reviewed_at = timezone.now()
        candidate.save()
        
        return candidate
