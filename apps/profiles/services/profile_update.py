from apps.profiles.models import CandidateProfile, ProfileSkill
from .completeness import ProfileCompletenessService

class ProfileUpdateService:
    @classmethod
    def update_profile(cls, user, cleaned_data) -> CandidateProfile:
        profile = getattr(user, 'candidate_profile', None)
        if not profile:
            profile = CandidateProfile(user=user)

        for field, value in cleaned_data.items():
            if hasattr(profile, field):
                setattr(profile, field, value)

        profile.save()
        ProfileCompletenessService.calculate(profile)

        try:
            from apps.recommendations.services.staleness import RecommendationStalenessService
            RecommendationStalenessService.mark_user_recommendations_stale(user, reason="profile_updated")
        except ImportError:
            pass

        return profile

    @classmethod
    def add_profile_skill(cls, user, raw_skill_text: str) -> ProfileSkill:
        from apps.skills.services.normalizer import SkillNormalizerService, normalize_skill_text

        raw_skill_text = (raw_skill_text or "").strip()
        if not raw_skill_text:
            raise ValueError("Skill name cannot be empty.")
        if len(raw_skill_text) > ProfileSkill.raw_name.field.max_length:
            raise ValueError("Skill name is too long.")

        profile, _ = CandidateProfile.objects.get_or_create(user=user)

        result = SkillNormalizerService.normalize_many(
            [raw_skill_text],
            source_type="manual",
            source_id=profile.id,
        )

        if result.canonical_skills:
            skill = result.canonical_skills[0]
            normalized_name = normalize_skill_text(skill.canonical_name)
            raw_name = skill.canonical_name
        else:
            skill = None
            normalized_name = normalize_skill_text(raw_skill_text)
            raw_name = raw_skill_text

        profile_skill, _ = ProfileSkill.objects.update_or_create(
            profile=profile,
            normalized_name=normalized_name,
            defaults={
                "skill": skill,
                "raw_name": raw_name,
                "source": "manual",
                "is_confirmed": True,
                "confidence": 100,
            },
        )

        ProfileCompletenessService.calculate(profile)
        cls._mark_recommendations_stale(user)

        return profile_skill

    @classmethod
    def remove_profile_skill(cls, user, normalized_name: str) -> bool:
        profile = getattr(user, 'candidate_profile', None)
        if not profile:
            return False

        normalized_name = (normalized_name or "").strip()
        if not normalized_name:
            return False

        deleted_count, _ = ProfileSkill.objects.filter(
            profile=profile,
            normalized_name=normalized_name,
        ).delete()

        if deleted_count:
            ProfileCompletenessService.calculate(profile)
            cls._mark_recommendations_stale(user)
            return True
        return False

    @classmethod
    def _mark_recommendations_stale(cls, user) -> None:
        try:
            from apps.recommendations.services.staleness import RecommendationStalenessService
            RecommendationStalenessService.mark_user_recommendations_stale(
                user, reason="profile_skills_updated"
            )
        except ImportError:
            pass
