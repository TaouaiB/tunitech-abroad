from django.test import TestCase
from apps.accounts.models import User

class DashboardViewsTests(TestCase):
    def test_dashboard_anonymous_redirect(self):
        response = self.client.get('/dashboard/')
        self.assertRedirects(response, '/accounts/login/?next=/dashboard/')

    def test_dashboard_authenticated_access(self):
        user = User.objects.create_user(username="dashuser", email="dash@example.com", password="password123")
        self.client.force_login(user)
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 200)
