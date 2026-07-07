from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.profiles.models import CandidateProfile, ProfileSkill
from apps.skills.models import Skill, SkillAlias
from apps.skills.services.normalizer import normalize_skill_text


def create_test_user(username: str, email: str, password: str = "password123") -> User:
    user = User(username=username, email=email)
    user.set_password(password)
    user.save()
    return user


class DashboardProfileSkillViewTests(TestCase):
    def setUp(self):
        self.user = create_test_user(
            username="dashboardskilluser",
            email="dashboardskills@example.test",
        )
        self.profile = CandidateProfile.objects.create(user=self.user, target_country="France")
        self.client.force_login(self.user)

        self.python = Skill.objects.create(canonical_name="Python", slug="python")
        SkillAlias.objects.create(
            skill=self.python,
            alias="Python3",
            normalized_alias=normalize_skill_text("Python3"),
        )

    def test_logged_in_post_add_skill_redirects_and_creates_skill(self):
        response = self.client.post(
            reverse("dashboard:profile"),
            {"skill_action": "add", "skill_name": "Python3"},
        )

        self.assertRedirects(response, reverse("dashboard:profile") + "#profile-skills")
        self.assertTrue(
            ProfileSkill.objects.filter(
                profile=self.profile,
                normalized_name=normalize_skill_text("Python"),
                skill=self.python,
                is_confirmed=True,
            ).exists()
        )

    def test_logged_in_post_remove_skill_redirects_and_removes_skill(self):
        ProfileSkill.objects.create(
            profile=self.profile,
            raw_name="Python",
            normalized_name=normalize_skill_text("Python"),
            skill=self.python,
            source="manual",
            is_confirmed=True,
        )

        response = self.client.post(
            reverse("dashboard:profile"),
            {"remove_skill": normalize_skill_text("Python")},
        )

        self.assertRedirects(response, reverse("dashboard:profile") + "#profile-skills")
        self.assertFalse(
            ProfileSkill.objects.filter(
                profile=self.profile,
                normalized_name=normalize_skill_text("Python"),
            ).exists()
        )

    def test_anonymous_cannot_add_or_remove_skill(self):
        self.client.logout()

        add_response = self.client.post(
            reverse("dashboard:profile"),
            {"skill_action": "add", "skill_name": "Python"},
        )
        self.assertNotEqual(add_response.status_code, 200)
        self.assertFalse(ProfileSkill.objects.filter(profile=self.profile).exists())

        ProfileSkill.objects.create(
            profile=self.profile,
            raw_name="Python",
            normalized_name=normalize_skill_text("Python"),
            skill=self.python,
            source="manual",
            is_confirmed=True,
        )

        remove_response = self.client.post(
            reverse("dashboard:profile"),
            {"remove_skill": normalize_skill_text("Python")},
        )
        self.assertNotEqual(remove_response.status_code, 200)
        self.assertTrue(
            ProfileSkill.objects.filter(
                profile=self.profile,
                normalized_name=normalize_skill_text("Python"),
            ).exists()
        )
