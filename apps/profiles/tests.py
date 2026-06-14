import importlib.util
from django.test import TestCase
from apps.accounts.models import User
from django.db import IntegrityError
from .models import CandidateProfile, ProfileSkill

def create_test_user(username: str, email: str, password: str = "password123") -> User:
    user = User(username=username, email=email)
    user.set_password(password)
    user.save()
    return user

class ProfileModelsTests(TestCase):
    def setUp(self):
        self.user = create_test_user(username="profileuser", email="profile@example.com", password="pw")

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
