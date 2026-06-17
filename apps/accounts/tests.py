from django.test import TestCase
from apps.accounts.models import User
from django.db.utils import IntegrityError
from django.db import connection
from types import SimpleNamespace
from .services.account_provisioning import AccountProvisioningService
from .signals import populate_profile_from_social_data

def create_test_user(username: str, email: str, password: str = "password123") -> User:
    user = User(username=username, email=email)
    user.set_password(password)
    user.save()
    return user

class UserModelTests(TestCase):
    def test_custom_user_model(self):
        self.assertEqual(User.__name__, 'User')
        self.assertEqual(User._meta.app_label, 'accounts')
    
    def test_user_creation(self):
        user = create_test_user(username="testuser", email="test@example.test", password="password123")
        self.assertEqual(user.email, "test@example.test")
        self.assertTrue(user.public_id)

    def test_duplicate_email_rejected(self):
        create_test_user(username="u1", email="duplicate@example.test", password="password123")
        with self.assertRaises(IntegrityError):
            create_test_user(username="u2", email="duplicate@example.test", password="password456")

    def test_no_auth_user_table(self):
        with connection.cursor() as cursor:
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
            tables = [row[0] for row in cursor.fetchall()]
        self.assertIn("accounts_user", tables)
        self.assertNotIn("auth_user", tables)

class AccountProvisioningServiceTests(TestCase):
    def test_idempotent_provisioning(self):
        user = create_test_user(username="provuser", email="prov@example.test", password="password123")
        
        # Test Phase 2: Creates CandidateProfile and EmailPreference idempotently
        from apps.profiles.models import CandidateProfile
        from apps.notifications.models import EmailPreference
        
        AccountProvisioningService.provision_new_user(user)
        self.assertTrue(CandidateProfile.objects.filter(user=user).exists())
        self.assertTrue(EmailPreference.objects.filter(user=user).exists())
        
        # Call again to test idempotency
        AccountProvisioningService.provision_new_user(user)
        self.assertEqual(CandidateProfile.objects.filter(user=user).count(), 1)
        self.assertEqual(EmailPreference.objects.filter(user=user).count(), 1)

    def test_social_account_provisioning(self):
        user = create_test_user(username="socialuser", email="social@example.test", password="password123")
        try:
            from allauth.socialaccount.models import SocialAccount
            SocialAccount.objects.create(
                user=user, 
                provider='github', 
                uid='12345',
                extra_data={'name': 'Github User', 'html_url': 'https://github.com/ghuser', 'location': 'Tunis'}
            )
            
            from apps.profiles.models import CandidateProfile
            AccountProvisioningService.provision_new_user(user)
            
            profile = CandidateProfile.objects.get(user=user)
            self.assertEqual(profile.full_name, 'Github User')
            self.assertEqual(profile.github_url, 'https://github.com/ghuser')
            self.assertEqual(profile.location, 'Tunis')
        except ImportError:
            pass

    def test_oauth_socialaccount_extra_data_mapping(self):
        user = create_test_user(username="oauthuser", email="oauth@example.test", password="password123")
        AccountProvisioningService.provision_new_user(user)

        google_login = SimpleNamespace(
            user=user,
            account=SimpleNamespace(
                provider="google",
                extra_data={
                    "name": "Google Candidate",
                    "email": "google@example.test",
                    "picture": "https://lh3.googleusercontent.test/avatar.png",
                    "profile": "https://profiles.google.test/candidate",
                },
            ),
        )
        populate_profile_from_social_data(user, google_login)
        user.candidate_profile.refresh_from_db()
        self.assertEqual(user.candidate_profile.full_name, "Google Candidate")
        self.assertEqual(user.candidate_profile.avatar_url, "https://lh3.googleusercontent.test/avatar.png")
        self.assertEqual(user.candidate_profile.website_url, "https://profiles.google.test/candidate")

        github_user = create_test_user(username="githuboauth", email="github-oauth@example.test", password="password123")
        AccountProvisioningService.provision_new_user(github_user)
        github_login = SimpleNamespace(
            user=github_user,
            account=SimpleNamespace(
                provider="github",
                extra_data={
                    "name": "GitHub Candidate",
                    "email": "github@example.test",
                    "avatar_url": "https://avatars.githubusercontent.test/u/1",
                    "html_url": "https://github.com/candidate",
                    "location": "Tunis",
                },
            ),
        )
        populate_profile_from_social_data(github_user, github_login)
        github_user.candidate_profile.refresh_from_db()
        self.assertEqual(github_user.candidate_profile.full_name, "GitHub Candidate")
        self.assertEqual(github_user.candidate_profile.avatar_url, "https://avatars.githubusercontent.test/u/1")
        self.assertEqual(github_user.candidate_profile.github_url, "https://github.com/candidate")
        self.assertEqual(github_user.candidate_profile.location, "Tunis")

class AuthViewsTests(TestCase):
    def test_login_page_status_code(self):
        response = self.client.get('/accounts/login/')
        self.assertEqual(response.status_code, 200)

    def test_signup_page_status_code(self):
        response = self.client.get('/accounts/signup/')
        self.assertEqual(response.status_code, 200)

    def test_confirm_email_route_uses_project_layout(self):
        response = self.client.get("/accounts/confirm-email/")
        self.assertEqual(response.status_code, 200)
        template_names = [template.name for template in response.templates if template.name]
        self.assertIn("account/verification_sent.html", template_names)
        html = response.content.decode()
        self.assertIn('data-project-layout="tunitech-abroad"', html)
        self.assertIn("TuniTech", html)
        self.assertNotIn("<h1>Verify Your Email Address</h1>", html)
