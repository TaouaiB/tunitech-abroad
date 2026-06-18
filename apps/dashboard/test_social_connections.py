from allauth.socialaccount.models import SocialAccount
from django.contrib.messages import get_messages
from django.core import signing
from django.test import TestCase

from apps.accounts.models import User
from apps.dashboard.views import SOCIAL_DISCONNECT_SIGNING_SALT


def create_user(username: str, email: str) -> User:
    return User.objects.create(username=username, email=email)


class SocialConnectionDisconnectTests(TestCase):
    def test_disconnect_form_does_not_render_raw_account_id(self):
        user = create_user(username="socialuser", email="social@example.test")
        self.client.force_login(user)
        account = SocialAccount.objects.create(id=987654321, user=user, provider="google", uid="12345")

        response = self.client.get("/dashboard/account/connections/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="disconnect_token" value="')
        self.assertNotContains(response, "disconnect" + "_id")
        self.assertNotContains(response, f'value="{account.id}"')
        self.assertNotContains(response, f'value="{account.id}:')
        self.assertNotContains(response, str(account.id))

    def test_valid_signed_token_disconnects_current_users_account(self):
        user = create_user(username="socialuser2", email="social2@example.test")
        self.client.force_login(user)
        account = SocialAccount.objects.create(user=user, provider="github", uid="67890")
        token = signing.dumps({"account_id": account.id}, salt=SOCIAL_DISCONNECT_SIGNING_SALT)

        response = self.client.post("/dashboard/account/connections/", {"disconnect_token": token})

        self.assertRedirects(response, "/dashboard/account/connections/")
        self.assertFalse(SocialAccount.objects.filter(id=account.id).exists())

    def test_tampered_token_is_rejected(self):
        user = create_user(username="socialuser3", email="social3@example.test")
        self.client.force_login(user)
        account = SocialAccount.objects.create(user=user, provider="google", uid="abcde")

        response = self.client.post(
            "/dashboard/account/connections/",
            {"disconnect_token": f"invalid_token:{account.id}"},
        )

        self.assertRedirects(response, "/dashboard/account/connections/")
        self.assertTrue(SocialAccount.objects.filter(id=account.id).exists())
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Requête de déconnexion invalide" in m.message for m in messages))

    def test_token_for_another_users_account_does_not_disconnect_anything(self):
        current_user = create_user(username="currentuser", email="current@example.test")
        other_user = create_user(username="otheruser", email="other@example.test")
        account = SocialAccount.objects.create(user=other_user, provider="google", uid="other_google")
        token = signing.dumps({"account_id": account.id}, salt=SOCIAL_DISCONNECT_SIGNING_SALT)

        self.client.force_login(current_user)
        response = self.client.post("/dashboard/account/connections/", {"disconnect_token": token})

        self.assertRedirects(response, "/dashboard/account/connections/")
        self.assertTrue(SocialAccount.objects.filter(id=account.id).exists())
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Impossible de déconnecter ce compte" in m.message for m in messages))
