from django.test import Client, TestCase, override_settings
from apps.accounts.models import User
from django.db.utils import IntegrityError
from django.db import connection
from types import SimpleNamespace
from unittest.mock import patch

from allauth.account.models import EmailAddress
from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.models import SocialAccount, SocialLogin
from django.core import mail
from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.backends.db import SessionStore
from django.urls import reverse
from django.test import RequestFactory

from .adapters import TuniTechSocialAccountAdapter
from .services.account_provisioning import AccountProvisioningService
from .services.onboarding import OnboardingRedirectService
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


class AccountFlowTests(TestCase):
    def test_manual_signup_post_with_csrf_redirects_to_cv(self):
        client = Client(enforce_csrf_checks=True)
        response = client.get(reverse("account_signup"))
        csrf_token = response.cookies["csrftoken"].value

        response = client.post(
            reverse("account_signup"),
            {
                "email": "manual-signup@example.test",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
                "csrfmiddlewaretoken": csrf_token,
            },
            HTTP_REFERER=reverse("account_signup"),
        )

        self.assertNotEqual(response.status_code, 403)
        self.assertRedirects(response, reverse("dashboard:cv"), fetch_redirect_response=False)
        self.assertTrue(User.objects.filter(email="manual-signup@example.test").exists())

    def test_onboarding_redirect_service_routes_no_password_user_to_password_step(self):
        user = create_test_user("oauthnopass", "oauthnopass@example.test")
        user.set_unusable_password()
        user.save(update_fields=["password"])
        request = RequestFactory().get("/")
        request.user = user
        request.session = SessionStore()

        self.assertEqual(
            OnboardingRedirectService.get_login_redirect_url(request),
            reverse("account_set_password"),
        )

    def test_onboarding_redirect_service_respects_manual_user_default_url(self):
        user = create_test_user("manualexisting", "manualexisting@example.test")
        request = RequestFactory().get("/")
        request.user = user
        request.session = SessionStore()

        self.assertEqual(
            OnboardingRedirectService.get_login_redirect_url(request, default_url="/jobs/?next=kept"),
            "/jobs/?next=kept",
        )

    def test_no_password_user_cannot_bypass_password_step_via_cv_page(self):
        user = create_test_user("oauthbypass", "oauthbypass@example.test")
        user.set_unusable_password()
        user.save(update_fields=["password"])

        request = RequestFactory().get(reverse("dashboard:cv"))
        request.user = user
        request.session = SessionStore()

        self.assertEqual(
            OnboardingRedirectService.should_redirect_request(request),
            reverse("account_set_password"),
        )

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        ACCOUNT_EMAIL_NOTIFICATIONS=True,
    )
    def test_password_change_sends_security_email(self):
        user = create_test_user("passwordmail", "passwordmail@example.test", "OldPass123!")
        EmailAddress.objects.create(user=user, email=user.email, primary=True, verified=True)
        self.client.force_login(user)

        response = self.client.post(
            reverse("account_change_password"),
            {
                "oldpassword": "OldPass123!",
                "password1": "NewPass123!",
                "password2": "NewPass123!",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("password was changed", mail.outbox[0].subject)

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
            self.assertEqual(profile.full_name, '')
            self.assertEqual(profile.github_url, 'https://github.com/ghuser')
            self.assertEqual(profile.location, 'Tunis')
        except ImportError:
            pass

class SocialAccountAdapterTests(TestCase):
    def setUp(self):
        self.request_factory = RequestFactory()

    def _request(self):
        request = self.request_factory.get("/")
        request.session = SessionStore()
        request._messages = FallbackStorage(request)
        return request

    def _social_login(self, provider="google", email="oauth@example.test", verified=True):
        user = User(username=email.split("@")[0], email=email)
        account = SocialAccount(
            provider=provider,
            uid=f"{provider}-uid",
            extra_data={"email": email, "email_verified": verified, "name": "OAuth User"},
        )
        email_address = EmailAddress(email=email, verified=verified, primary=True)
        return SocialLogin(user=user, account=account, email_addresses=[email_address])

    def test_existing_local_user_google_verified_email_authenticates_by_email(self):
        existing_user = create_test_user(username="existinggoogle", email="same@gmail.test")
        login = self._social_login(provider="google", email="same@gmail.test", verified=True)

        login.lookup()

        self.assertEqual(login.user, existing_user)
        self.assertEqual(login._did_authenticate_by_email, "same@gmail.test")

    def test_unverified_provider_email_does_not_auto_link_existing_user(self):
        existing_user = create_test_user(username="existingunverified", email="same-unverified@example.test")
        login = self._social_login(provider="github", email="same-unverified@example.test", verified=False)

        login.lookup()

        self.assertNotEqual(login.user, existing_user)
        self.assertIsNone(login._did_authenticate_by_email)

    def test_future_provider_is_not_trusted_for_email_authentication_by_default(self):
        create_test_user(username="existingfuture", email="future@example.test")
        login = self._social_login(provider="example", email="future@example.test", verified=True)

        login.lookup()

        self.assertIsNone(login._did_authenticate_by_email)

    def test_new_google_verified_email_creates_provisioned_account_without_confirmation(self):
        login = self._social_login(provider="google", email="new-google@gmail.test", verified=True)

        with patch("allauth.account.adapter.DefaultAccountAdapter.send_confirmation_mail") as send_confirmation_mail:
            TuniTechSocialAccountAdapter().save_user(self._request(), login)

        user = User.objects.get(email="new-google@gmail.test")
        self.assertFalse(user.has_usable_password())
        self.assertTrue(hasattr(user, "candidate_profile"))
        self.assertTrue(hasattr(user, "email_preferences"))
        self.assertTrue(EmailAddress.objects.filter(user=user, email=user.email, verified=True).exists())
        self.assertEqual(send_confirmation_mail.call_count, 0)

    def test_new_github_verified_email_creates_verified_account_without_confirmation(self):
        login = self._social_login(provider="github", email="new-github@example.test", verified=True)

        with patch("allauth.account.adapter.DefaultAccountAdapter.send_confirmation_mail") as send_confirmation_mail:
            TuniTechSocialAccountAdapter().save_user(self._request(), login)

        user = User.objects.get(email="new-github@example.test")
        self.assertFalse(user.has_usable_password())
        self.assertTrue(hasattr(user, "candidate_profile"))
        self.assertTrue(hasattr(user, "email_preferences"))
        self.assertTrue(EmailAddress.objects.filter(user=user, email=user.email, verified=True).exists())
        self.assertEqual(send_confirmation_mail.call_count, 0)

    def test_social_adapter_does_not_send_duplicate_signup_warning_for_existing_google_email(self):
        create_test_user(username="existingwarning", email="warning@gmail.test")
        login = self._social_login(provider="google", email="warning@gmail.test", verified=True)

        with patch("allauth.account.adapter.DefaultAccountAdapter.send_mail") as send_mail:
            login.lookup()

        self.assertEqual(send_mail.call_count, 0)
        self.assertEqual(login._did_authenticate_by_email, "warning@gmail.test")

    def test_pre_social_login_links_google_to_verified_local_email(self):
        existing_user = create_test_user(username="verifiedlocal", email="verified-local@gmail.test")
        EmailAddress.objects.create(user=existing_user, email=existing_user.email, verified=True, primary=True)
        login = self._social_login(provider="google", email=existing_user.email, verified=True)

        with patch.object(login, "connect") as connect:
            TuniTechSocialAccountAdapter().pre_social_login(self._request(), login)

        connect.assert_called_once()
        self.assertEqual(connect.call_args.args[1], existing_user)

    def test_pre_social_login_unverified_provider_collision_is_unsafe(self):
        existing_user = create_test_user(username="unverifiedprovider", email="unverified-provider@gmail.test")
        EmailAddress.objects.create(user=existing_user, email=existing_user.email, verified=True, primary=True)
        login = self._social_login(provider="google", email=existing_user.email, verified=False)

        with self.assertRaises(ImmediateHttpResponse), patch.object(login, "connect") as connect:
            TuniTechSocialAccountAdapter().pre_social_login(self._request(), login)

        connect.assert_not_called()

    def test_pre_social_login_unverified_local_collision_is_unsafe(self):
        existing_user = create_test_user(username="unverifiedlocal", email="unverified-local@gmail.test")
        EmailAddress.objects.create(user=existing_user, email=existing_user.email, verified=False, primary=True)
        login = self._social_login(provider="google", email=existing_user.email, verified=True)

        with self.assertRaises(ImmediateHttpResponse), patch.object(login, "connect") as connect:
            TuniTechSocialAccountAdapter().pre_social_login(self._request(), login)

        connect.assert_not_called()

    def test_pre_social_login_unsafe_collision_message_is_provider_neutral(self):
        existing_user = create_test_user(username="githubcollision", email="github-collision@example.test")
        EmailAddress.objects.create(user=existing_user, email=existing_user.email, verified=False, primary=True)
        login = self._social_login(provider="github", email=existing_user.email, verified=True)
        request = self._request()

        with self.assertRaises(ImmediateHttpResponse):
            TuniTechSocialAccountAdapter().pre_social_login(request, login)

        messages = [str(message) for message in get_messages(request)]
        self.assertIn(
            "Connexion sociale non liée automatiquement : vérifiez d'abord votre adresse email locale.",
            messages,
        )

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
        self.assertEqual(user.candidate_profile.full_name, "")
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
        self.assertEqual(github_user.candidate_profile.full_name, "")
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

    def test_auth_templates_do_not_include_fake_success_toasts(self):
        login_response = self.client.get("/accounts/login/")
        signup_response = self.client.get("/accounts/signup/", follow=True)

        self.assertEqual(login_response.status_code, 200)
        self.assertEqual(signup_response.status_code, 200)
        self.assertNotContains(login_response, "data-success")
        self.assertNotContains(signup_response, "data-success")
        self.assertContains(login_response, 'data-auth-form="true"')
        self.assertContains(signup_response, 'data-auth-form="true"')

    def test_login_and_signup_pages_are_split(self):
        login_response = self.client.get("/accounts/login/")
        signup_response = self.client.get("/accounts/signup/")

        self.assertContains(login_response, 'action="/accounts/login/"', html=False)
        self.assertNotContains(login_response, 'action="/accounts/signup/"', html=False)
        self.assertContains(login_response, "Pas encore de compte ? Créer un compte")

        self.assertContains(signup_response, 'action="/accounts/signup/"', html=False)
        self.assertNotContains(signup_response, 'action="/accounts/login/"', html=False)
        self.assertContains(signup_response, "Déjà un compte ? Connexion")

    def test_wrong_email_password_login_does_not_authenticate(self):
        user = create_test_user(username="wrong-login", email="wrong-login@example.test", password="password123")
        EmailAddress.objects.create(user=user, email=user.email, verified=True, primary=True)

        response = self.client.post(
            "/accounts/login/",
            {"login": "wrong-login@example.test", "password": "not-the-password"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotContains(response, "Signed in")
        self.assertNotContains(response, "Connecté")
        self.assertContains(response, "has-error")
        self.assertContains(response, "toast bad")

    def test_existing_normal_email_password_login_still_works(self):
        user = create_test_user(username="normal-login", email="normal-login@example.test", password="password123")
        EmailAddress.objects.create(user=user, email=user.email, verified=True, primary=True)

        response = self.client.post(
            "/accounts/login/",
            {"login": "normal-login@example.test", "password": "password123"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/jobs/")

    def test_invalid_signup_post_reaches_allauth_without_fake_success(self):
        response = self.client.post(
            "/accounts/signup/",
            {
                "email": "bad-email",
                "password1": "short",
                "password2": "different",
                "first_name": "Bad",
                "last_name": "Signup",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "data-success")
        self.assertNotContains(response, "Account created")
        self.assertContains(response, "has-error")

    def test_normal_email_signup_redirects_to_cv_and_sends_verification_email(self):
        response = self.client.post(
            "/accounts/signup/",
            {
                "email": "normal-signup@example.test",
                "password1": "SafePassword123!",
                "password2": "SafePassword123!",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/dashboard/cv/", response["Location"])
        user = User.objects.get(email="normal-signup@example.test")
        email_address = EmailAddress.objects.get(user=user, email=user.email)
        self.assertFalse(email_address.verified)

    def test_confirm_email_route_uses_project_layout(self):
        response = self.client.get("/accounts/confirm-email/")
        self.assertEqual(response.status_code, 200)
        template_names = [template.name for template in response.templates if template.name]
        self.assertIn("account/verification_sent.html", template_names)
        html = response.content.decode()
        self.assertIn('data-project-layout="tunitech-abroad"', html)
        self.assertIn("TuniAtlas", html)
        self.assertNotIn("<h1>Verify Your Email Address</h1>", html)

from django.template.loader import render_to_string

class AccountEmailTemplateTests(TestCase):
    def setUp(self):
        self.user = create_test_user("emailtester", "emailtester@example.com")

    def test_password_reset_email_renders_with_branded_content(self):
        context = {
            "user": self.user,
            "password_reset_url": "http://example.com/reset/xyz"
        }

        # Test subject
        subject = render_to_string("account/email/password_reset_key_subject.txt", context).strip("\n")
        self.assertEqual(subject, "Reset your TuniAtlas password")
        self.assertNotIn("\n", subject)

        # Test text message
        txt_body = render_to_string("account/email/password_reset_key_message.txt", context)
        self.assertIn("TuniAtlas", txt_body)
        self.assertIn("http://example.com/reset/xyz", txt_body)

        # Test html message
        html_body = render_to_string("account/email/password_reset_key_message.html", context)
        self.assertIn("TuniAtlas", html_body)
        self.assertIn("http://example.com/reset/xyz", html_body)

    def test_confirmation_email_renders_with_branded_content(self):
        context = {
            "user": self.user,
            "activate_url": "http://example.com/activate/xyz"
        }

        # Test subject
        subject = render_to_string("account/email/email_confirmation_signup_subject.txt", context).strip("\n")
        self.assertEqual(subject, "Confirm your TuniAtlas account")
        self.assertNotIn("\n", subject)

        # Test text message
        txt_body = render_to_string("account/email/email_confirmation_signup_message.txt", context)
        self.assertIn("TuniAtlas", txt_body)
        self.assertIn("http://example.com/activate/xyz", txt_body)

        # Test html message
        html_body = render_to_string("account/email/email_confirmation_signup_message.html", context)
        self.assertIn("TuniAtlas", html_body)
        self.assertIn("http://example.com/activate/xyz", html_body)
