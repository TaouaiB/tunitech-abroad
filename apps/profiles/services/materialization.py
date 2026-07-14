from dataclasses import dataclass

from django.db import transaction

from apps.profiles.models import CandidateProfile, ProfileSkill
from apps.skills.models import Skill
from apps.skills.services.normalizer import normalize_skill_text


@dataclass
class ProfileSkillMaterializationResult:
    """Outcome of materializing one canonical skill onto a profile."""

    created: bool = False
    linked_existing: bool = False
    unchanged: bool = False
    conflict: bool = False
    changed: bool = False
    profile_skill: ProfileSkill | None = None
    conflict_skill_id: int | None = None


class ProfileSkillMaterializationService:
    """
    Correctness boundary for persisting resolved canonical profile skills.

    The service is idempotent and transaction-safe. It never overwrites a
    non-null skill link; conflicts are returned so callers can report them.
    Manually confirmed rows keep their stronger source/confidence metadata.
    """

    @classmethod
    def materialize(
        cls,
        profile: CandidateProfile,
        skill: Skill,
        *,
        source: str = "cv_upload",
        confidence: int = 80,
        is_confirmed: bool = False,
        raw_name: str | None = None,
        existing_profile_skill: ProfileSkill | None = None,
    ) -> ProfileSkillMaterializationResult:
        canonical_normalized = normalize_skill_text(skill.canonical_name)
        if not canonical_normalized:
            return ProfileSkillMaterializationResult()

        raw_name = (raw_name or skill.canonical_name)[: ProfileSkill.raw_name.field.max_length]

        with transaction.atomic():
            canonical_row = cls._get_locked_row(profile, canonical_normalized)

            if existing_profile_skill is None:
                return cls._materialize_canonical(
                    profile=profile,
                    skill=skill,
                    canonical_row=canonical_row,
                    canonical_normalized=canonical_normalized,
                    source=source,
                    confidence=confidence,
                    is_confirmed=is_confirmed,
                    raw_name=raw_name,
                )

            return cls._materialize_legacy(
                profile=profile,
                skill=skill,
                legacy_row=existing_profile_skill,
                canonical_row=canonical_row,
                canonical_normalized=canonical_normalized,
                source=source,
                confidence=confidence,
                is_confirmed=is_confirmed,
                raw_name=raw_name,
            )

    @classmethod
    def _get_locked_row(cls, profile: CandidateProfile, normalized_name: str) -> ProfileSkill | None:
        try:
            return ProfileSkill.objects.select_for_update().get(
                profile=profile, normalized_name=normalized_name
            )
        except ProfileSkill.DoesNotExist:
            return None

    @classmethod
    def _materialize_canonical(
        cls,
        profile: CandidateProfile,
        skill: Skill,
        canonical_row: ProfileSkill | None,
        canonical_normalized: str,
        source: str,
        confidence: int,
        is_confirmed: bool,
        raw_name: str,
    ) -> ProfileSkillMaterializationResult:
        if canonical_row is None:
            profile_skill = ProfileSkill.objects.create(
                profile=profile,
                skill=skill,
                raw_name=raw_name,
                normalized_name=canonical_normalized,
                source=source,
                confidence=confidence,
                is_confirmed=is_confirmed,
            )
            return ProfileSkillMaterializationResult(
                created=True, changed=True, profile_skill=profile_skill
            )

        if canonical_row.skill_id == skill.id:
            return ProfileSkillMaterializationResult(
                unchanged=True, profile_skill=canonical_row
            )

        if canonical_row.skill_id is not None:
            return ProfileSkillMaterializationResult(
                conflict=True,
                profile_skill=canonical_row,
                conflict_skill_id=canonical_row.skill_id,
            )

        cls._link_row(canonical_row, skill, source, confidence, is_confirmed, raw_name)
        return ProfileSkillMaterializationResult(
            linked_existing=True, changed=True, profile_skill=canonical_row
        )

    @classmethod
    def _materialize_legacy(
        cls,
        profile: CandidateProfile,
        skill: Skill,
        legacy_row: ProfileSkill,
        canonical_row: ProfileSkill | None,
        canonical_normalized: str,
        source: str,
        confidence: int,
        is_confirmed: bool,
        raw_name: str,
    ) -> ProfileSkillMaterializationResult:
        # Legacy row is already the canonical row: use canonical path.
        if legacy_row.normalized_name == canonical_normalized:
            return cls._materialize_canonical(
                profile=profile,
                skill=skill,
                canonical_row=legacy_row,
                canonical_normalized=canonical_normalized,
                source=source,
                confidence=confidence,
                is_confirmed=is_confirmed,
                raw_name=raw_name,
            )

        # A canonical row exists for this skill.
        if canonical_row is not None:
            if canonical_row.skill_id is not None and canonical_row.skill_id != skill.id:
                return ProfileSkillMaterializationResult(
                    conflict=True,
                    profile_skill=legacy_row,
                    conflict_skill_id=canonical_row.skill_id,
                )

            # Canonical row is missing the link or already correct.
            if canonical_row.skill_id is None:
                cls._link_row(
                    canonical_row, skill, source, confidence, is_confirmed, raw_name
                )
            # Legacy alias row is redundant unless it is user-controlled.
            if not legacy_row.is_confirmed:
                legacy_row.delete()
            return ProfileSkillMaterializationResult(
                linked_existing=True, changed=True, profile_skill=canonical_row
            )

        # No canonical row exists: convert the legacy row to canonical.
        cls._link_row(legacy_row, skill, source, confidence, is_confirmed, raw_name)
        legacy_row.normalized_name = canonical_normalized
        legacy_row.save(update_fields=["normalized_name"] + cls._link_update_fields(legacy_row))
        return ProfileSkillMaterializationResult(
            linked_existing=True, changed=True, profile_skill=legacy_row
        )

    @classmethod
    def _link_row(
        cls,
        row: ProfileSkill,
        skill: Skill,
        source: str,
        confidence: int,
        is_confirmed: bool,
        raw_name: str,
    ) -> None:
        row.skill = skill
        update_fields = cls._link_update_fields(row)
        if not row.is_confirmed:
            row.source = source
            row.confidence = confidence
            row.is_confirmed = is_confirmed
            row.raw_name = raw_name
        row.save(update_fields=update_fields)

    @classmethod
    def _link_update_fields(cls, row: ProfileSkill) -> list[str]:
        if row.is_confirmed:
            return ["skill", "updated_at"]
        return ["skill", "source", "confidence", "is_confirmed", "raw_name", "updated_at"]

    @classmethod
    def materialize_many(
        cls,
        profile: CandidateProfile,
        skills: list[Skill],
        *,
        source: str = "cv_upload",
        confidence: int = 80,
        is_confirmed: bool = False,
    ) -> dict:
        """Aggregate materialization results for a list of canonical skills."""

        aggregate = {
            "created": 0,
            "linked_existing": 0,
            "unchanged": 0,
            "conflicts": 0,
            "changed": False,
            "results": [],
        }
        for skill in skills:
            result = cls.materialize(
                profile=profile,
                skill=skill,
                source=source,
                confidence=confidence,
                is_confirmed=is_confirmed,
                raw_name=skill.canonical_name,
            )
            if result.created:
                aggregate["created"] += 1
            elif result.linked_existing:
                aggregate["linked_existing"] += 1
            elif result.unchanged:
                aggregate["unchanged"] += 1
            elif result.conflict:
                aggregate["conflicts"] += 1
            if result.changed:
                aggregate["changed"] = True
            aggregate["results"].append(result)
        return aggregate
