from django.test import TestCase
from apps.accounts.models import User

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
