from django.test import TestCase
from django.core.management import call_command
from .models import SystemSetting
from .services.system_setting import SystemSettingService

class CoreTests(TestCase):
    def test_system_setting_creation_and_lookup(self):
        SystemSetting.objects.create(key="max_upload_size", value={"mb": 5})
        
        val = SystemSettingService.get_value("max_upload_size")
        self.assertEqual(val, {"mb": 5})
        
        default_val = SystemSettingService.get_value("missing_key", default="fallback")
        self.assertEqual(default_val, "fallback")

from unittest.mock import patch
from django.urls import reverse

class HealthCheckTests(TestCase):
    def test_health_check_healthy(self):
        response = self.client.get(reverse('health'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    @patch('apps.core.services.health.connection.ensure_connection')
    def test_health_check_db_failure(self, mock_conn):
        mock_conn.side_effect = Exception("DB down")
        response = self.client.get(reverse('health'))
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["database"], "error")

    @patch('apps.core.services.health.cache.set')
    def test_health_check_redis_failure(self, mock_cache_set):
        mock_cache_set.side_effect = Exception("Redis down")
        response = self.client.get(reverse('health'))
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["redis"], "error")


from django.contrib.auth import get_user_model
User = get_user_model()

class AdminAccessTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create(username="staff", email="staff@example.com", is_staff=True, is_superuser=True, is_active=True)
        self.staff_user.set_password("pass")
        self.staff_user.save()

        self.normal_user = User.objects.create(username="normal", email="normal@example.com", is_staff=False, is_active=True)
        self.normal_user.set_password("pass")
        self.normal_user.save()

    def test_unauthenticated_user_redirected(self):
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)

    def test_normal_user_denied(self):
        self.client.login(email="normal@example.com", password="pass")
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 302)

    def test_staff_user_can_access(self):
        self.client.login(email="staff@example.com", password="pass")
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 200)

    def test_representative_admin_page_loads(self):
        self.client.login(email="staff@example.com", password="pass")
        response = self.client.get("/admin/core/systemsetting/")
        self.assertEqual(response.status_code, 200)

    @patch('apps.cvs.admin.parse_cv.delay')
    def test_representative_admin_action_calls_task(self, mock_delay):
        from apps.cvs.models import CVUpload
        cv = CVUpload.objects.create(user=self.normal_user, original_filename="test.pdf", file_hash="abc", file_size=10, is_active=True)

        self.client.login(email="staff@example.com", password="pass")
        data = {
            'action': 'reparse_cvs',
            '_selected_action': [cv.id]
        }
        response = self.client.post("/admin/cvs/cvupload/", data, follow=True)
        self.assertEqual(response.status_code, 200)
        mock_delay.assert_called_once_with(cv.id)

        messages = list(response.context['messages'])
        self.assertTrue(any("Queued 1 CVs for reparsing" in str(m) for m in messages))

from django.test import override_settings

class ErrorPageTests(TestCase):
    @override_settings(DEBUG=False)
    def test_custom_404_page(self):
        response = self.client.get('/this-url-does-not-exist-12345/')
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, '404.html')
        self.assertContains(response, '404', status_code=404)
        self.assertContains(response, 'trouver la page', status_code=404)
        self.assertNotContains(response, 'Using the URLconf defined in', status_code=404)

    @override_settings(DEBUG=False)
    def test_recommendations_root_returns_404(self):
        # We explicitly don't have a /recommendations/ URL, it should be /dashboard/recommendations/
        response = self.client.get('/recommendations/')
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, '404.html')


class DemoSeedCommandTests(TestCase):
    def test_seed_demo_data_creates_searchable_demo_jobs_idempotently(self):
        from apps.jobs.models import JobStatus, NormalizedJob

        call_command("seed_demo_data", verbosity=0)

        demo_jobs = NormalizedJob.objects.filter(
            status=JobStatus.ACTIVE,
            title__startswith="[DEMO]",
            source__slug="france_travail",
        )
        first_count = demo_jobs.count()

        self.assertGreaterEqual(first_count, 5)
        self.assertTrue(demo_jobs.filter(description__icontains="Offre fictive").exists())
        response = self.client.get("/jobs/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "[DEMO]", count=first_count)

        call_command("seed_demo_data", verbosity=0)

        self.assertEqual(
            NormalizedJob.objects.filter(
                status=JobStatus.ACTIVE,
                title__startswith="[DEMO]",
                source__slug="france_travail",
            ).count(),
            first_count,
        )
