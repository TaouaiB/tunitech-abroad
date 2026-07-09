import importlib.util
from django.test import TestCase
from apps.accounts.models import User
from django.db import IntegrityError
from .models import CandidateProfile, ProfileSkill
from .forms import ProfileForm
from .services.completeness import ProfileCompletenessService
from .services.backfill import ProfileSkillBackfillService
from apps.skills.models import Skill, SkillAlias, UnmatchedSkillCandidate
from apps.skills.services.normalizer import normalize_skill_text
from apps.profiles.services.profile_update import ProfileUpdateService
from unittest.mock import patch

def create_test_user(username: str, email: str, password: str = "password123") -> User:
    user = User(username=username, email=email)
    user.set_password(password)
    user.save()
    return user

class ProfileModelsTests(TestCase):
    def setUp(self):
        self.user = create_test_user(username="profileuser", email="profile@example.test", password="pw")

    def test_candidate_profile_creation(self):
        profile = CandidateProfile.objects.create(user=self.user, target_country="France")
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.target_country, "France")
        self.assertIsNotNone(profile.public_id)

    def test_profile_skill_uniqueness(self):
        profile = CandidateProfile.objects.create(user=self.user)
        ProfileSkill.objects.create(profile=profile, raw_name="Python", normalized_name="python")

        with self.assertRaises(IntegrityError):
            ProfileSkill.objects.create(profile=profile, raw_name="Python 3", normalized_name="python")

    def test_phase_boundary(self):
        # Phase 3 introduced apps.skills
        self.assertIsNotNone(importlib.util.find_spec("apps.skills"))
        # Phase 4 introduced apps.jobs
        self.assertIsNotNone(importlib.util.find_spec("apps.jobs"))
        # Ensure Phase 5+ apps/models do not exist yet
        self.assertIsNone(importlib.util.find_spec("apps.matches"))

    def test_completeness_rejects_dummy_and_invalid_choice_values(self):
        profile = CandidateProfile.objects.create(
            user=self.user,
            full_name="qsdqsd",
            phone="qsd",
            location="qsd",
            current_level="qsd",
            target_roles=["qsd"],
            target_job_types=["qsd"],
            target_type="qsd",
            french_level="qsd",
            english_level="qsd",
            relocation_preference="qsd",
            remote_preference="qsd",
            linkedin_url="https://linkedin.com/in/valid",
        )

        report = ProfileCompletenessService.get_report(profile)
        self.assertLess(report["score"], 50)
        self.assertIn("Nom complet", report["missing"])
        self.assertIn("Rôles ciblés", report["missing"])
        self.assertIn("Niveau de carrière", report["missing"])

    def test_profile_form_rejects_invalid_urls_and_choices(self):
        form = ProfileForm(data={
            "full_name": "Aymen Ben Salah",
            "phone": "+216 55 123 456",
            "location": "Tunis, Tunisia",
            "linkedin_url": "linkedin.com/in/aymen",
            "github_url": "https://github.com/aymen",
            "portfolio_url": "not-a-url",
            "website_url": "",
            "current_level": "qsd",
            "years_experience": "1",
            "target_roles": "qsd",
            "target_job_types": ["full_time_job"],
            "target_type": "job",
            "french_level": "fluent",
            "english_level": "fluent",
            "relocation_preference": "yes",
            "remote_preference": "hybrid",
        })

        self.assertFalse(form.is_valid())
        self.assertIn("linkedin_url", form.errors)
        self.assertIn("portfolio_url", form.errors)
        self.assertIn("current_level", form.errors)

    def test_profile_skill_backfill_maps_alias_and_is_idempotent_for_unmatched(self):
        profile = CandidateProfile.objects.create(user=self.user)
        dotnet = Skill.objects.create(canonical_name=".NET", slug="dotnet", category="backend")
        SkillAlias.objects.create(
            skill=dotnet,
            alias=".NET Core",
            normalized_alias=normalize_skill_text(".NET Core"),
        )
        mapped = ProfileSkill.objects.create(
            profile=profile,
            raw_name=".NET Core",
            normalized_name=normalize_skill_text(".NET Core"),
        )
        ProfileSkill.objects.create(
            profile=profile,
            raw_name="Unknown Skill",
            normalized_name=normalize_skill_text("Unknown Skill"),
            source="cv_upload",
        )

        first = ProfileSkillBackfillService.backfill_profile_skills()
        second = ProfileSkillBackfillService.backfill_profile_skills()

        mapped.refresh_from_db()
        self.assertEqual(mapped.skill, dotnet)
        self.assertEqual(first["mapped_to_canonical"], 1)
        self.assertEqual(second["mapped_to_canonical"], 0)
        candidate = UnmatchedSkillCandidate.objects.get(normalized_text="unknown skill", source_type="cv")
        self.assertEqual(candidate.occurrence_count, 1)


class ProfileUpdateServiceSkillTests(TestCase):
    def setUp(self):
        self.user = create_test_user(username="skilluser", email="skills@example.test", password="pw")
        self.profile = CandidateProfile.objects.create(user=self.user, target_country="France")

        self.python = Skill.objects.create(canonical_name="Python", slug="python")
        SkillAlias.objects.create(
            skill=self.python,
            alias="Python",
            normalized_alias=normalize_skill_text("Python"),
        )
        SkillAlias.objects.create(
            skill=self.python,
            alias="Python3",
            normalized_alias=normalize_skill_text("Python3"),
        )

    def test_add_known_skill_through_alias_maps_to_canonical_skill(self):
        profile_skill = ProfileUpdateService.add_profile_skill(self.user, "Python3")

        self.assertEqual(profile_skill.skill, self.python)
        self.assertEqual(profile_skill.normalized_name, normalize_skill_text("Python"))
        self.assertEqual(profile_skill.source, "manual")
        self.assertTrue(profile_skill.is_confirmed)
        self.assertEqual(profile_skill.confidence, 100)

    def test_add_unknown_skill_creates_unmatched_candidate_and_profile_skill(self):
        profile_skill = ProfileUpdateService.add_profile_skill(self.user, "MagicSkillXYZ")

        self.assertIsNone(profile_skill.skill)
        self.assertEqual(profile_skill.normalized_name, normalize_skill_text("MagicSkillXYZ"))
        self.assertEqual(profile_skill.source, "manual")
        self.assertTrue(profile_skill.is_confirmed)

        candidate = UnmatchedSkillCandidate.objects.get(
            normalized_text=normalize_skill_text("MagicSkillXYZ"),
            source_type="manual",
        )
        self.assertEqual(candidate.raw_skill_text, "MagicSkillXYZ")
        self.assertFalse(Skill.objects.filter(canonical_name="MagicSkillXYZ").exists())

    def test_add_duplicate_does_not_create_duplicate_profile_skill(self):
        ProfileUpdateService.add_profile_skill(self.user, "MagicSkillXYZ")
        ProfileUpdateService.add_profile_skill(self.user, "MagicSkillXYZ")

        self.assertEqual(
            ProfileSkill.objects.filter(
                profile=self.profile,
                normalized_name=normalize_skill_text("MagicSkillXYZ"),
            ).count(),
            1,
        )

    def test_add_existing_cv_skill_marks_it_confirmed(self):
        cv_skill = ProfileSkill.objects.create(
            profile=self.profile,
            raw_name="Python",
            normalized_name=normalize_skill_text("Python"),
            source="cv_upload",
            is_confirmed=False,
            confidence=80,
        )

        profile_skill = ProfileUpdateService.add_profile_skill(self.user, "Python")

        cv_skill.refresh_from_db()
        self.assertEqual(profile_skill.pk, cv_skill.pk)
        self.assertEqual(cv_skill.skill, self.python)
        self.assertEqual(cv_skill.source, "manual")
        self.assertTrue(cv_skill.is_confirmed)
        self.assertEqual(cv_skill.confidence, 100)

    def test_remove_skill_deletes_only_current_user_profile_skill(self):
        ProfileSkill.objects.create(
            profile=self.profile,
            raw_name="Python",
            normalized_name=normalize_skill_text("Python"),
            source="manual",
            is_confirmed=True,
        )

        removed = ProfileUpdateService.remove_profile_skill(
            self.user, normalize_skill_text("Python")
        )

        self.assertTrue(removed)
        self.assertFalse(
            ProfileSkill.objects.filter(
                profile=self.profile, normalized_name=normalize_skill_text("Python")
            ).exists()
        )

    def test_remove_skill_does_not_delete_another_users_same_skill(self):
        other_user = create_test_user(username="otherskilluser", email="otherskills@example.test", password="pw")
        other_profile = CandidateProfile.objects.create(user=other_user, target_country="France")
        ProfileSkill.objects.create(
            profile=other_profile,
            raw_name="Python",
            normalized_name=normalize_skill_text("Python"),
            source="manual",
            is_confirmed=True,
        )

        removed = ProfileUpdateService.remove_profile_skill(
            self.user, normalize_skill_text("Python")
        )

        self.assertFalse(removed)
        self.assertTrue(
            ProfileSkill.objects.filter(
                profile=other_profile, normalized_name=normalize_skill_text("Python")
            ).exists()
        )

    @patch("apps.recommendations.services.staleness.RecommendationStalenessService.mark_user_recommendations_stale")
    def test_add_and_remove_call_staleness_service(self, mock_mark_stale):
        ProfileUpdateService.add_profile_skill(self.user, "Python")
        mock_mark_stale.assert_called_with(self.user, reason="profile_skills_updated")

        ProfileUpdateService.remove_profile_skill(self.user, normalize_skill_text("Python"))
        self.assertEqual(mock_mark_stale.call_count, 2)
