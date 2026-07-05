from django.test import TestCase
from django.urls import reverse
from apps.accounts.models import User

class DashboardRouteTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="password123")

    def test_dashboard_root_redirects_to_jobs(self):
        response = self.client.get("/dashboard/")
        self.assertRedirects(response, "/jobs/", fetch_redirect_response=False)

    def test_dashboard_cv_requires_login_and_works(self):
        # Redirects to login if anonymous
        response = self.client.get("/dashboard/cv/")
        self.assertEqual(response.status_code, 302)
        
        # Works if logged in
        self.client.force_login(self.user)
        response = self.client.get("/dashboard/cv/")
        self.assertEqual(response.status_code, 200)

    def test_dashboard_account_requires_login_and_works(self):
        # Redirects to login if anonymous
        response = self.client.get("/dashboard/account/")
        self.assertEqual(response.status_code, 302)

        # Works if logged in
        self.client.force_login(self.user)
        response = self.client.get("/dashboard/account/")
        self.assertEqual(response.status_code, 200)

    def test_standalone_thirdparty_routes_are_404(self):
        routes = ["/3rdparty/", "/third-party/", "/thirdparty/"]
        for route in routes:
            response = self.client.get(route)
            self.assertEqual(response.status_code, 404)
