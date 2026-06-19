from django.test import TestCase
from apps.accounts.models import User
from apps.profiles.models import CandidateProfile

def create_test_user(username: str, email: str, password: str = "password123") -> User:
    user = User(username=username, email=email)
    user.set_password(password)
    user.save()
    return user

class DashboardViewsTests(TestCase):
    def test_dashboard_anonymous_redirect(self):
        response = self.client.get('/dashboard/')
        self.assertRedirects(response, '/accounts/login/?next=/dashboard/')

    def test_dashboard_authenticated_access(self):
        user = create_test_user(username="dashuser", email="dash@example.test", password="password123")
        self.client.force_login(user)
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 200)

    def test_dashboard_greeting_uses_profile_full_name_before_email(self):
        user = create_test_user(username="nameduser", email="named@example.test", password="password123")
        user.first_name = "Account"
        user.last_name = "Name"
        user.save(update_fields=["first_name", "last_name"])
        CandidateProfile.objects.create(user=user, full_name="Amina Ben Ali")
        self.client.force_login(user)

        response = self.client.get("/dashboard/")

        self.assertContains(response, "Bonjour, Amina Ben Ali !")
        self.assertNotContains(response, "Bonjour, named@example.test !")

    def test_dashboard_greeting_uses_user_full_name_before_email(self):
        user = create_test_user(username="accountname", email="account@example.test", password="password123")
        user.first_name = "Account"
        user.last_name = "Name"
        user.save(update_fields=["first_name", "last_name"])
        self.client.force_login(user)

        response = self.client.get("/dashboard/")

        self.assertContains(response, "Bonjour, Account Name !")
        self.assertNotContains(response, "Bonjour, account@example.test !")

    def test_password_cta_uses_has_usable_password(self):
        user = create_test_user(username="passworduser", email="password@example.test", password="password123")
        self.client.force_login(user)
        response = self.client.get("/dashboard/account/")
        self.assertContains(response, "Changer mon mot de passe")
        self.assertNotContains(response, "Ajouter un mot de passe")

        user.set_unusable_password()
        user.save(update_fields=["password"])
        self.client.force_login(user)
        response = self.client.get("/dashboard/account/")
        self.assertContains(response, "Ajouter un mot de passe")
        self.assertNotContains(response, "Changer mon mot de passe")

    def test_account_delete_copy_is_professional(self):
        user = create_test_user(username="copyuser", email="copy@example.test", password="password123")
        self.client.force_login(user)

        response = self.client.get("/dashboard/account/")

        self.assertContains(response, "Suppression du compte")
        self.assertContains(response, "Action irréversible")
        self.assertContains(response, "Supprimer définitivement mon compte")
        self.assertNotContains(response, "Zone Dangereuse")
