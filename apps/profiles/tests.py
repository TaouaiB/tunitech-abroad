import importlib.util
from django.test import TestCase
from apps.accounts.models import User
from django.db import IntegrityError
from .models import CandidateProfile, ProfileSkill
from .forms import ProfileForm
from .services.completeness import ProfileCompletenessService

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
