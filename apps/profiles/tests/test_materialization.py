from django.test import TestCase

from apps.accounts.models import User
from apps.profiles.models import CandidateProfile, ProfileSkill
from apps.profiles.services.materialization import ProfileSkillMaterializationService
from apps.skills.models import Skill, SkillAlias
from apps.skills.services.normalizer import normalize_skill_text


def make_user(username: str, email: str) -> User:
    user = User(username=username, email=email)
    user.set_password("pw")
    user.save()
    return user


class ProfileSkillMaterializationTests(TestCase):
    def setUp(self):
        self.user = make_user("matuser", "mat@example.test")
        self.profile = CandidateProfile.objects.create(user=self.user, target_country="France")
        self.python = Skill.objects.create(
            canonical_name="Python", slug="python", category="programming_language"
        )
        SkillAlias.objects.create(
            skill=self.python,
            alias="Python",
            normalized_alias=normalize_skill_text("Python"),
        )

    def test_create_linked_row(self):
        result = ProfileSkillMaterializationService.materialize(
            profile=self.profile,
            skill=self.python,
            source="cv_upload",
            confidence=80,
            is_confirmed=False,
        )

        self.assertTrue(result.created)
        self.assertTrue(result.changed)
        self.assertIsNotNone(result.profile_skill)
        self.assertEqual(result.profile_skill.skill, self.python)
        self.assertEqual(result.profile_skill.normalized_name, "python")

    def test_repair_existing_null_linked_row(self):
        existing = ProfileSkill.objects.create(
            profile=self.profile,
            raw_name="Python",
            normalized_name="python",
            source="cv_upload",
            confidence=80,
            is_confirmed=False,
        )

        result = ProfileSkillMaterializationService.materialize(
            profile=self.profile,
            skill=self.python,
            source="cv_upload",
            confidence=80,
            is_confirmed=False,
        )

        self.assertTrue(result.linked_existing)
        self.assertTrue(result.changed)
        existing.refresh_from_db()
        self.assertEqual(existing.skill, self.python)

    def test_same_link_remains_unchanged(self):
        ProfileSkill.objects.create(
            profile=self.profile,
            skill=self.python,
            raw_name="Python",
            normalized_name="python",
            source="cv_upload",
            confidence=80,
            is_confirmed=False,
        )

        result = ProfileSkillMaterializationService.materialize(
            profile=self.profile,
            skill=self.python,
            source="cv_upload",
            confidence=80,
            is_confirmed=False,
        )

        self.assertTrue(result.unchanged)
        self.assertFalse(result.changed)

    def test_conflicting_non_null_link_is_preserved_and_reported(self):
        java = Skill.objects.create(
            canonical_name="Java", slug="java", category="programming_language"
        )
        existing = ProfileSkill.objects.create(
            profile=self.profile,
            skill=java,
            raw_name="Java-ish",
            normalized_name="python",
            source="manual",
            confidence=100,
            is_confirmed=True,
        )

        result = ProfileSkillMaterializationService.materialize(
            profile=self.profile,
            skill=self.python,
            source="cv_upload",
            confidence=80,
            is_confirmed=False,
        )

        self.assertTrue(result.conflict)
        self.assertFalse(result.changed)
        self.assertEqual(result.conflict_skill_id, java.pk)
        existing.refresh_from_db()
        self.assertEqual(existing.skill, java)
        self.assertEqual(existing.source, "manual")

    def test_manual_confirmed_metadata_is_not_downgraded(self):
        existing = ProfileSkill.objects.create(
            profile=self.profile,
            raw_name="Python",
            normalized_name="python",
            source="manual",
            confidence=100,
            is_confirmed=True,
        )

        ProfileSkillMaterializationService.materialize(
            profile=self.profile,
            skill=self.python,
            source="cv_upload",
            confidence=80,
            is_confirmed=False,
        )

        existing.refresh_from_db()
        self.assertEqual(existing.skill, self.python)
        self.assertEqual(existing.source, "manual")
        self.assertEqual(existing.confidence, 100)
        self.assertTrue(existing.is_confirmed)

    def test_repeated_execution_is_idempotent(self):
        for _ in range(3):
            result = ProfileSkillMaterializationService.materialize(
                profile=self.profile,
                skill=self.python,
                source="cv_upload",
                confidence=80,
                is_confirmed=False,
            )

        self.assertEqual(ProfileSkill.objects.filter(profile=self.profile, normalized_name="python").count(), 1)
        self.assertTrue(result.unchanged)

    def test_no_duplicate_normalized_row(self):
        ProfileSkillMaterializationService.materialize(
            profile=self.profile,
            skill=self.python,
            source="cv_upload",
            confidence=80,
            is_confirmed=False,
        )
        ProfileSkillMaterializationService.materialize(
            profile=self.profile,
            skill=self.python,
            source="cv_upload",
            confidence=80,
            is_confirmed=False,
        )

        self.assertEqual(ProfileSkill.objects.filter(profile=self.profile, normalized_name="python").count(), 1)

    def test_legacy_alias_row_is_converted_to_canonical(self):
        alias_row = ProfileSkill.objects.create(
            profile=self.profile,
            raw_name="Python3",
            normalized_name="python3",
            source="cv_upload",
            confidence=80,
            is_confirmed=False,
        )

        result = ProfileSkillMaterializationService.materialize(
            profile=self.profile,
            skill=self.python,
            source="cv_upload",
            confidence=80,
            is_confirmed=False,
            raw_name="Python",
            existing_profile_skill=alias_row,
        )

        self.assertTrue(result.linked_existing)
        self.assertTrue(result.changed)
        alias_row.refresh_from_db()
        self.assertEqual(alias_row.skill, self.python)
        self.assertEqual(alias_row.normalized_name, "python")
        self.assertEqual(alias_row.raw_name, "Python")

    def test_legacy_alias_row_with_existing_canonical_links_canonical(self):
        canonical_row = ProfileSkill.objects.create(
            profile=self.profile,
            raw_name="Python",
            normalized_name="python",
            source="cv_upload",
            confidence=80,
            is_confirmed=False,
        )
        alias_row = ProfileSkill.objects.create(
            profile=self.profile,
            raw_name="Python3",
            normalized_name="python3",
            source="cv_upload",
            confidence=80,
            is_confirmed=False,
        )

        result = ProfileSkillMaterializationService.materialize(
            profile=self.profile,
            skill=self.python,
            source="cv_upload",
            confidence=80,
            is_confirmed=False,
            existing_profile_skill=alias_row,
        )

        self.assertTrue(result.linked_existing)
        self.assertTrue(result.changed)
        canonical_row.refresh_from_db()
        self.assertEqual(canonical_row.skill, self.python)
        self.assertFalse(
            ProfileSkill.objects.filter(pk=alias_row.pk).exists()
        )

    def test_legacy_alias_row_keeps_confirmed_alias(self):
        alias_row = ProfileSkill.objects.create(
            profile=self.profile,
            raw_name="Python3",
            normalized_name="python3",
            source="manual",
            confidence=100,
            is_confirmed=True,
        )

        result = ProfileSkillMaterializationService.materialize(
            profile=self.profile,
            skill=self.python,
            source="cv_upload",
            confidence=80,
            is_confirmed=False,
            existing_profile_skill=alias_row,
        )

        self.assertTrue(result.linked_existing)
        self.assertTrue(result.changed)
        alias_row.refresh_from_db()
        self.assertEqual(alias_row.skill, self.python)
        self.assertEqual(alias_row.normalized_name, "python")
        self.assertEqual(alias_row.source, "manual")
        self.assertTrue(alias_row.is_confirmed)

    def test_legacy_alias_conflict_with_different_canonical_skill(self):
        java = Skill.objects.create(
            canonical_name="Java", slug="java", category="programming_language"
        )
        ProfileSkill.objects.create(
            profile=self.profile,
            raw_name="Java",
            normalized_name="python",
            skill=java,
            source="manual",
            confidence=100,
            is_confirmed=True,
        )
        alias_row = ProfileSkill.objects.create(
            profile=self.profile,
            raw_name="Python3",
            normalized_name="python3",
            source="cv_upload",
            confidence=80,
            is_confirmed=False,
        )

        result = ProfileSkillMaterializationService.materialize(
            profile=self.profile,
            skill=self.python,
            source="cv_upload",
            confidence=80,
            is_confirmed=False,
            existing_profile_skill=alias_row,
        )

        self.assertTrue(result.conflict)
        self.assertFalse(result.changed)
        self.assertEqual(result.conflict_skill_id, java.pk)
        alias_row.refresh_from_db()
        self.assertIsNone(alias_row.skill)
