from pathlib import Path

from django.test import TestCase
from django.conf import settings
from django.core.management import call_command
from .models import SystemSetting
from .services.system_setting import SystemSettingService

__path__ = [str(Path(__file__).with_name("tests"))]

class CoreTests(TestCase):
    def test_system_setting_creation_and_lookup(self):
        SystemSetting.objects.create(key="max_upload_size", value={"mb": 5})

        val = SystemSettingService.get_value("max_upload_size")
        self.assertEqual(val, {"mb": 5})

        default_val = SystemSettingService.get_value("missing_key", default="fallback")
        self.assertEqual(default_val, "fallback")


class SettingsSafetyTests(TestCase):
    def test_sessions_use_cached_database_backend(self):
        self.assertEqual(settings.SESSION_ENGINE, "django.contrib.sessions.backends.cached_db")
        self.assertEqual(settings.SESSION_CACHE_ALIAS, "default")

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
        self.staff_user = User.objects.create(username="staff", email="staff@example.test", is_staff=True, is_superuser=True, is_active=True)
        self.staff_user.set_password("pass")
        self.staff_user.save()

        self.normal_user = User.objects.create(username="normal", email="normal@example.test", is_staff=False, is_active=True)
        self.normal_user.set_password("pass")
        self.normal_user.save()

    def test_unauthenticated_user_redirected(self):
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)

    def test_normal_user_denied(self):
        self.client.login(email="normal@example.test", password="pass")
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 302)

    def test_staff_user_can_access(self):
        self.client.login(email="staff@example.test", password="pass")
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 200)

    def test_representative_admin_page_loads(self):
        self.client.login(email="staff@example.test", password="pass")
        response = self.client.get("/admin/core/systemsetting/")
        self.assertEqual(response.status_code, 200)

    @patch('apps.cvs.admin.parse_cv.delay')
    def test_representative_admin_action_calls_task(self, mock_delay):
        from apps.cvs.models import CVUpload
        cv = CVUpload.objects.create(user=self.normal_user, original_filename="test.pdf", file_hash="abc", file_size=10, is_active=True)

        self.client.login(email="staff@example.test", password="pass")
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
    @override_settings(DEBUG=False, ALLOWED_HOSTS=["testserver"])
    def test_custom_404_page(self):
        response = self.client.get('/this-url-does-not-exist-12345/')
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, '404.html')
        self.assertContains(response, '404', status_code=404)
        self.assertContains(response, 'Page introuvable', status_code=404)
        self.assertContains(response, 'Retour aux offres', status_code=404)
        self.assertNotContains(response, 'Using the URLconf defined', status_code=404)

    @override_settings(DEBUG=False, ALLOWED_HOSTS=["testserver"])
    def test_recommendations_root_returns_404(self):
        # We explicitly don't have a /recommendations/ URL, it should be /dashboard/recommendations/
        response = self.client.get('/recommendations/')
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, '404.html')
        self.assertContains(response, 'Page introuvable', status_code=404)

    def test_custom_500_template_exists(self):
        from django.template.loader import get_template
        from django.template import TemplateDoesNotExist
        try:
            get_template("500.html")
        except TemplateDoesNotExist:
            self.fail("500.html template does not exist")


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
from django.test import TestCase, override_settings
from django.urls import reverse
from django.core import mail
from apps.core.models import ContactMessage
from apps.core.services.contact import ContactService

class ContactTests(TestCase):
    def test_about_page_returns_200(self):
        response = self.client.get(reverse('core:about'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/about.html')

    def test_anonymous_about_has_privacy_terms_modals_without_account_cta(self):
        response = self.client.get(reverse('core:about'))

        self.assertContains(response, 'data-modal-open="privacy-modal"')
        self.assertContains(response, 'data-modal-open="terms-modal"')
        self.assertContains(response, 'id="privacy-modal"')
        self.assertContains(response, 'id="terms-modal"')
        self.assertNotContains(response, "Gérer les paramètres")

    def test_contact_form_valid_post(self):
        url = reverse('core:about')
        data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'subject': 'Compte',
            'message': 'Hello world!',
        }
        with override_settings(CELERY_TASK_ALWAYS_EAGER=True, CONTACT_EMAIL_RECIPIENTS=['admin@example.com']):
            response = self.client.post(url, data)
        self.assertRedirects(response, url)
        self.assertEqual(ContactMessage.objects.count(), 1)
        msg = ContactMessage.objects.first()
        self.assertEqual(msg.name, 'Test User')

    def test_contact_form_invalid_post(self):
        url = reverse('core:about')
        data = {
            'name': '',
            'email': 'invalid',
            'subject': '',
            'message': '',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ContactMessage.objects.count(), 0)
        self.assertContains(response, "Veuillez corriger")

    def test_honeypot_submission_fails(self):
        url = reverse('core:about')
        data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'subject': 'Compte',
            'message': 'Hello world!',
            'website': 'http://spam.com',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ContactMessage.objects.count(), 0)

    @override_settings(CONTACT_EMAIL_RECIPIENTS=['admin@example.com'], DEFAULT_FROM_EMAIL='test@test.com')
    def test_service_send_success(self):
        msg = ContactMessage.objects.create(
            name='A', email='a@a.com', subject='Subj', message='Msg',
            status=ContactMessage.Status.PENDING
        )
        ContactService.send_contact_message_email(message_id=msg.id)
        msg.refresh_from_db()
        self.assertEqual(msg.status, ContactMessage.Status.SENT)
        self.assertEqual(len(mail.outbox), 1)

    @override_settings(CONTACT_EMAIL_RECIPIENTS=[])
    def test_service_send_no_recipient(self):
        msg = ContactMessage.objects.create(
            name='A', email='a@a.com', subject='Subj', message='Msg',
            status=ContactMessage.Status.PENDING
        )
        ContactService.send_contact_message_email(message_id=msg.id)
        msg.refresh_from_db()
        self.assertEqual(msg.status, ContactMessage.Status.FAILED)
        self.assertEqual(msg.last_error_code, "recipient_not_configured")
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(CONTACT_EMAIL_RECIPIENTS=['admin@example.com'], DEFAULT_FROM_EMAIL='test@test.com')
    def test_service_send_failure_stores_safe_error_code(self):
        msg = ContactMessage.objects.create(
            name='A',
            email='a@a.com',
            subject='Subj',
            message='Msg',
            status=ContactMessage.Status.PENDING,
        )

        with patch('apps.core.services.contact.send_mail', side_effect=RuntimeError("provider secret")):
            ContactService.send_contact_message_email(message_id=msg.id)

        msg.refresh_from_db()
        self.assertEqual(msg.status, ContactMessage.Status.FAILED)
        self.assertEqual(msg.last_error_code, "email_send_failed")
        self.assertNotIn("provider secret", msg.last_error_code)
