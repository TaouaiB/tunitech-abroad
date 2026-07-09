from django.test import TestCase
from apps.accounts.models import User
from apps.profiles.models import CandidateProfile

def create_test_user(username: str, email: str, password: str = "password123") -> User:
    user = User(username=username, email=email)
    user.set_password(password)
    user.save()
    return user

class DashboardViewsTests(TestCase):
    pass

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

        self.assertContains(response, "Supprimer définitivement")
        self.assertContains(response, "Compte & Sécurité")
        self.assertContains(response, "Préférences Email")
        self.assertContains(response, "Comptes liés")
        self.assertNotContains(response, "Zone Dangereuse")
        self.assertNotContains(response, "Action irréversible. Toutes vos données seront supprimées.")
