import os
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from unittest.mock import patch

from apps.analytics.services.admin_metrics import AdminMetricsService
from apps.cvs.admin import CVUploadAdmin
from apps.cvs.models import CVUpload
from apps.jobs.admin import mark_jobs_expired, mark_jobs_stale
from apps.jobs.models import JobStatus, NormalizedJob
from apps.llm.admin import JobEnrichmentAdmin, LLMRequestLogAdmin
from apps.llm.models import JobEnrichment, LLMRequestLog
from apps.privacy.admin import DeletionRequestAdmin
from apps.privacy.models import DeletionRequest
from django.contrib.admin.sites import site

User = get_user_model()

class AdminOperationsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('admin_operations')

        self.normal_user = User.objects.create_user(
            email="normal@example.com",
            password="password",
            username="normal"
        )
        self.staff_user = User.objects.create_user(
            email="staff@example.com",
            password="password",
            username="staff",
            is_staff=True
        )

    def test_anonymous_access_blocked(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, f"/admin/login/?next={self.url}")

    def test_normal_user_access_blocked(self):
        self.client.force_login(self.normal_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response.url)

    def test_staff_user_access_granted(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Operations Dashboard")

    def test_admin_metrics_stability(self):
        metrics = AdminMetricsService.get_dashboard_metrics()
        expected_keys = [
            'users_total', 'new_signups_7d', 'active_users_7d',
            'cv_uploads_7d', 'cv_parse_failures_7d', 'cv_parses_pending_stuck',
            'active_jobs', 'jobs_ingested_24h', 'stale_expired_jobs',
            'latest_successful_ingestion', 'latest_failed_ingestion',
            'recommendation_runs_24h', 'recommendation_failures_24h',
            'stale_recommendations', 'saved_jobs_count',
            'llm_calls_today', 'llm_failures_today',
            'emails_sent_24h', 'emails_failed_24h',
            'pending_deletion_requests'
        ]
        for key in expected_keys:
            self.assertIn(key, metrics)

    def test_admin_metrics_keys_do_not_expose_sensitive_names(self):
        metrics = AdminMetricsService.get_dashboard_metrics()
        blocked_fragments = ["secret", "api_key", "token", "raw_text", "payload", "file_url"]
        for key, value in metrics.items():
            lower_key = key.lower()
            self.assertFalse(any(fragment in lower_key for fragment in blocked_fragments))
            if isinstance(value, str):
                lower_value = value.lower()
                self.assertFalse(any(fragment in lower_value for fragment in blocked_fragments))

class AdminSafetyTests(TestCase):
    def test_docs_exist(self):
        self.assertTrue(os.path.exists('docs/admin/admin_operations_14j.md'))
        self.assertTrue(os.path.exists('docs/admin/admin_analytics_14j.md'))

    def test_cv_raw_text_excluded(self):
        from apps.cvs.admin import CVParsedDataAdmin
        from apps.cvs.models import CVParsedData
        model_admin = CVParsedDataAdmin(CVParsedData, site)
        self.assertIn('raw_text', model_admin.exclude)

    def test_cv_file_excluded(self):
        model_admin = CVUploadAdmin(CVUpload, site)
        self.assertIn('file', model_admin.exclude)

    def test_llm_payloads_hidden(self):
        model_admin = LLMRequestLogAdmin(LLMRequestLog, site)
        list_display = model_admin.get_list_display(None)
        # Verify no raw payloads like prompt or completion text are in list display
        self.assertNotIn('prompt_text', list_display)
        self.assertNotIn('completion_text', list_display)
        self.assertNotIn('payload', list_display)

    def test_job_enrichment_admin_hides_raw_payloads(self):
        model_admin = JobEnrichmentAdmin(JobEnrichment, site)
        list_display = model_admin.get_list_display(None)
        self.assertNotIn("raw_request_json", list_display)
        self.assertNotIn("raw_response_text", list_display)
        self.assertNotIn("raw_response_json", list_display)
        self.assertIn("raw_request_json", model_admin.exclude)
        self.assertIn("raw_response_text", model_admin.exclude)
        self.assertIn("raw_response_json", model_admin.exclude)

    def test_unsubscribe_token_hidden(self):
        from apps.notifications.admin import EmailUnsubscribeTokenAdmin
        from apps.notifications.models import EmailUnsubscribeToken
        model_admin = EmailUnsubscribeTokenAdmin(EmailUnsubscribeToken, site)
        self.assertIn('token', model_admin.exclude)

class AdminActionDelegationTests(TestCase):
    @patch('apps.privacy.tasks.process_account_deletion.delay')
    def test_deletion_request_action_delegation(self, mock_delay):
        user = User.objects.create_user(email="user@example.com", username="user", password="password")
        deletion_req = DeletionRequest.objects.create(user=user, status='pending')

        admin_instance = DeletionRequestAdmin(DeletionRequest, site)
        # Mock request with messages
        from django.contrib.messages.storage.fallback import FallbackStorage
        from django.test import RequestFactory
        request = RequestFactory().post('/')
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

        queryset = DeletionRequest.objects.filter(id=deletion_req.id)

        # Call the action
        from apps.privacy.admin import process_deletion_requests
        process_deletion_requests(admin_instance, request, queryset)

        # Verify the celery task was called via .delay
        mock_delay.assert_called_once_with(deletion_req.id)

    @patch('apps.jobs.services.admin_operations.JobAdminOperationsService.mark_selected_jobs_status')
    def test_normalized_job_mark_stale_delegates_to_service(self, mock_mark_status):
        mock_mark_status.return_value = 1
        admin_instance = site._registry[NormalizedJob]
        request = self._request_with_messages()

        mark_jobs_stale(admin_instance, request, NormalizedJob.objects.none())

        mock_mark_status.assert_called_once()
        self.assertEqual(mock_mark_status.call_args.args[1], JobStatus.STALE)

    @patch('apps.jobs.services.admin_operations.JobAdminOperationsService.mark_selected_jobs_status')
    def test_normalized_job_mark_expired_delegates_to_service(self, mock_mark_status):
        mock_mark_status.return_value = 1
        admin_instance = site._registry[NormalizedJob]
        request = self._request_with_messages()

        mark_jobs_expired(admin_instance, request, NormalizedJob.objects.none())

        mock_mark_status.assert_called_once()
        self.assertEqual(mock_mark_status.call_args.args[1], JobStatus.EXPIRED)

    def _request_with_messages(self):
        from django.contrib.messages.storage.fallback import FallbackStorage
        from django.test import RequestFactory

        request = RequestFactory().post('/')
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        return request
