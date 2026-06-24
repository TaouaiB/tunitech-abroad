from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from apps.skills.models import Skill, SkillAlias, UnmatchedSkillCandidate
from apps.skills.services.normalizer import SkillNormalizerService, normalize_skill_text
from apps.skills.services.review import UnmatchedSkillReviewService

UserModel = get_user_model()

def create_test_user(
    *,
    username: str,
    email: str,
    password: str = "pw",
    is_staff: bool = False,
) -> AbstractBaseUser:
    user = UserModel.objects.create(
        username=username,
        email=email,
        is_staff=is_staff,
    )
    user.set_password(password)
    user.save(update_fields=["password"])
    return user

class NormalizerServiceTests(TestCase):
    def setUp(self):
        self.react = Skill.objects.create(canonical_name="React", slug="react")
        SkillAlias.objects.create(skill=self.react, alias="ReactJS", normalized_alias="reactjs")

        self.postgres = Skill.objects.create(canonical_name="PostgreSQL", slug="postgresql")
        SkillAlias.objects.create(skill=self.postgres, alias="Postgres", normalized_alias="postgres")

        self.python = Skill.objects.create(canonical_name="Python", slug="python")
        SkillAlias.objects.create(skill=self.python, alias="Python3", normalized_alias="python3")

    def test_text_normalization(self):
        self.assertEqual(normalize_skill_text("ReactJS"), "reactjs")
        self.assertEqual(normalize_skill_text("C++"), "c++")
        self.assertEqual(normalize_skill_text("C#"), "c#")
        self.assertEqual(normalize_skill_text(".NET Core"), ".net core")
        self.assertEqual(normalize_skill_text(" Node.js  "), "node.js")
        self.assertEqual(normalize_skill_text("Café"), "cafe")

    def test_normalize_many_matched(self):
        result = SkillNormalizerService.normalize_many(["ReactJS", "Postgres", "Python3", "Unknown Skill", "ReactJS"], source_type="cv")
        self.assertEqual(len(result.canonical_skills), 3)
        self.assertIn(self.react, result.canonical_skills)
        self.assertIn(self.postgres, result.canonical_skills)
        self.assertIn(self.python, result.canonical_skills)

        self.assertEqual(len(result.unmatched_candidates), 1)
        self.assertEqual(result.unmatched_candidates[0].raw_skill_text, "Unknown Skill")
        self.assertEqual(result.unmatched_candidates[0].occurrence_count, 1)

    def test_normalize_many_increment_count(self):
        # First extraction
        SkillNormalizerService.normalize_many(["New Unknown"], source_type="cv")
        candidate = UnmatchedSkillCandidate.objects.get(normalized_text="new unknown")
        self.assertEqual(candidate.occurrence_count, 1)

        # Second extraction with same skill
        SkillNormalizerService.normalize_many(["New Unknown", "New Unknown"], source_type="cv")
        candidate.refresh_from_db()
        # Should be 2 because the normalizer deduplicates the input list internally
        self.assertEqual(candidate.occurrence_count, 2)

    def test_does_not_auto_create_skill(self):
        SkillNormalizerService.normalize_many(["Magic"], source_type="cv")
        self.assertFalse(Skill.objects.filter(canonical_name="Magic").exists())

    def test_inactive_skill_ignored(self):
        inactive_skill = Skill.objects.create(canonical_name="Inactive", slug="inactive", is_active=False)
        SkillAlias.objects.create(skill=inactive_skill, alias="InactiveJS", normalized_alias="inactivejs")

        result = SkillNormalizerService.normalize_many(["InactiveJS"], source_type="cv")
        self.assertEqual(len(result.canonical_skills), 0)
        self.assertEqual(len(result.unmatched_candidates), 1)
        self.assertEqual(result.unmatched_candidates[0].raw_skill_text, "InactiveJS")

    def test_materialization_with_new_aliases(self):
        from apps.skills.services.seed import SkillSeedService
        SkillSeedService.seed_initial_taxonomy()

        test_aliases = ["API REST", "Cybersécurité", "Cloud", "Assistance technique"]
        result = SkillNormalizerService.normalize_many(test_aliases, source_type="cv")

        canonical_names = [s.canonical_name for s in result.canonical_skills]
        self.assertIn("REST API", canonical_names)
        self.assertIn("Cybersecurity", canonical_names)
        self.assertIn("Cloud", canonical_names)
        self.assertIn("IT Support", canonical_names)
        self.assertEqual(len(result.unmatched_candidates), 0)

class ReviewServiceTests(TestCase):
    def setUp(self):
        self.staff_user = create_test_user(username="staff", email="staff@example.test", password="pw", is_staff=True)
        self.regular_user = create_test_user(username="regular", email="user@example.test", password="pw", is_staff=False)
        self.candidate = UnmatchedSkillCandidate.objects.create(
            raw_skill_text="React JS",
            normalized_text="react js",
            source_type="cv"
        )
        self.skill = Skill.objects.create(canonical_name="React", slug="react")

    def test_staff_can_map(self):
        UnmatchedSkillReviewService.map_candidate(self.candidate.id, self.skill.id, self.staff_user)
        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.status, "mapped")
        self.assertEqual(self.candidate.mapped_skill, self.skill)
        self.assertEqual(self.candidate.reviewed_by, self.staff_user)

        # Check if alias was created
        self.assertTrue(SkillAlias.objects.filter(normalized_alias="react js", skill=self.skill).exists())

    def test_staff_can_ignore(self):
        UnmatchedSkillReviewService.ignore_candidate(self.candidate.id, self.staff_user)
        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.status, "ignored")
        self.assertEqual(self.candidate.reviewed_by, self.staff_user)

    def test_non_staff_cannot_map(self):
        with self.assertRaises(PermissionError):
            UnmatchedSkillReviewService.map_candidate(self.candidate.id, self.skill.id, self.regular_user)
