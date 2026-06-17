from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch

from apps.accounts.models import User
from apps.analytics.models import UserEvent
from apps.cvs.models import CVUpload, CVParsedData
from apps.jobs.models import JobSource, NormalizedJob, RawJobRecord, SourceType
from apps.llm.models import LLMRequestLog
from apps.matching.models import MatchResult
from apps.notifications.models import EmailEvent, EmailPreference
from apps.profiles.models import CandidateProfile, ProfileSkill
from apps.recommendations.models import JobRecommendation, RecommendationRun, SavedJob
from .models import ConsentRecord, DeletionRequest
from .services.consent import ConsentService
from .services.account_deletion import AccountDeletionService

def create_test_user(username: str, email: str, password: str = "password123") -> User:
    user = User(username=username, email=email)
    user.set_password(password)
    user.save()
    return user

class ConsentTests(TestCase):
    def test_consent_service_records(self):
        user = create_test_user(username="consentuser", email="consent@example.test", password="pw")

        record = ConsentService.record(
            user=user,
            consent_type="terms",
            consent_version="v1.0",
            accepted=True,
            ip_address="127.0.0.1",
            user_agent="TestAgent"
        )

        self.assertEqual(record.user, user)
        self.assertEqual(record.consent_type, "terms")
        self.assertEqual(record.consent_version, "v1.0")
        self.assertEqual(record.consent_text, "")
        self.assertTrue(record.accepted)
        self.assertEqual(record.ip_address, "127.0.0.1")
        self.assertEqual(record.user_agent, "TestAgent")

    def test_consent_service_records_stable_text_and_source(self):
        user = create_test_user(username="consentuser2", email="consent2@example.test", password="pw")

        record = ConsentService.record(
            user=user,
            consent_type="privacy_policy",
            consent_text="Politique de confidentialite MVP.",
            consent_version="2026-06",
            request_meta={"source_path": "/privacy/"},
        )

        self.assertEqual(record.consent_text, "Politique de confidentialite MVP. Source: /privacy/")

class PrivacyRoutesTests(TestCase):
    def test_privacy_policy_route(self):
        response = self.client.get("/privacy/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "privacy/privacy_policy.html")

    def test_terms_route(self):
        response = self.client.get("/terms/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "privacy/terms.html")

    def test_privacy_url_names(self):
        self.assertEqual(reverse("privacy:privacy_policy"), "/privacy/")
        self.assertEqual(reverse("privacy:terms"), "/terms/")


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }
)
class PrivacyDashboardRoutesTests(TestCase):
    def setUp(self):
        self.user = create_test_user(username="accountuser", email="account@example.test", password="pw")

    def test_account_page_requires_login(self):
        response = self.client.get("/dashboard/account/")
        self.assertEqual(response.status_code, 302)

    def test_delete_account_page_requires_login(self):
        response = self.client.get("/dashboard/settings/delete-account/")
        self.assertEqual(response.status_code, 302)

    def test_account_page_renders_for_authenticated_user(self):
        self.client.force_login(self.user)
        response = self.client.get("/dashboard/account/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/account.html")

    def test_delete_account_post_requires_confirmation(self):
        self.client.force_login(self.user)
        response = self.client.post("/dashboard/settings/delete-account/", {"confirmation": "WRONG"})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(DeletionRequest.objects.filter(user=self.user).exists())

    def test_delete_account_post_creates_request(self):
        self.client.force_login(self.user)
        with patch("apps.privacy.tasks.process_account_deletion.delay"):
            response = self.client.post("/dashboard/settings/delete-account/", {"confirmation": "DELETE"})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(DeletionRequest.objects.filter(user=self.user, status="pending").exists())


class AccountDeletionServiceTests(TestCase):
    def test_request_deletion_idempotent(self):
        user = create_test_user(username="deluser", email="del@example.test", password="pw")
        with patch("apps.privacy.tasks.process_account_deletion.delay"):
            req1 = AccountDeletionService.request_deletion(user)
            req2 = AccountDeletionService.request_deletion(user)
        self.assertEqual(req1.id, req2.id)
        self.assertEqual(req1.status, 'pending')

    def test_process_account_deletion(self):
        user = create_test_user(username="deluser2", email="del2@example.test", password="pw")
        with patch("apps.privacy.tasks.process_account_deletion.delay"):
            req = AccountDeletionService.request_deletion(user)
        processed = AccountDeletionService.process_request(req)

        self.assertEqual(processed.status, 'completed')
        user.refresh_from_db()
        self.assertFalse(user.is_active)
        self.assertTrue(user.email.startswith('deleted-user'))
        self.assertFalse(user.has_usable_password())

    def test_process_account_deletion_failure_retry(self):
        user = create_test_user(username="deluser3", email="del3@example.test", password="pw")
        with patch("apps.privacy.tasks.process_account_deletion.delay"):
            req = AccountDeletionService.request_deletion(user)

        # Simulate a fake failure by temporarily unsetting user
        req.user = None
        failed_req = AccountDeletionService.process_request(req)
        self.assertEqual(failed_req.status, 'failed')
        self.assertEqual(failed_req.attempt_count, 1)

    @patch("os.remove")
    @patch("os.path.exists", return_value=True)
    def test_process_account_deletion_removes_private_candidate_data(self, mock_exists, mock_remove):
        user = create_test_user(username="deluser4", email="del4@example.test", password="pw")
        profile = CandidateProfile.objects.create(user=user, full_name="Private Name")
        ProfileSkill.objects.create(
            profile=profile,
            raw_name="Python",
            normalized_name="python",
            source="cv_upload",
        )
        cv = CVUpload.objects.create(
            user=user,
            file="cvs/1/private.pdf",
            original_filename="private.pdf",
            file_hash="hash",
            file_size=1,
            is_active=True,
        )
        CVParsedData.objects.create(cv_upload=cv, raw_text="private cv text")
        job = self._create_job()
        SavedJob.objects.create(user=user, job=job)
        MatchResult.objects.create(
            user=user,
            profile=profile,
            cv_upload=cv,
            job=job,
            fit_score=80,
            technical_skills_score=80,
            experience_score=80,
            role_title_score=80,
            language_score=80,
            location_score=80,
        )
        JobRecommendation.objects.create(
            user=user,
            profile=profile,
            cv_upload=cv,
            job=job,
            fit_score=80,
            ranking_score="80.00",
            rank=1,
            computed_at=timezone.now(),
            status="active",
        )
        RecommendationRun.objects.create(
            user=user,
            trigger_type="cv_uploaded",
            status="success",
            started_at=timezone.now(),
        )
        EmailPreference.objects.create(user=user, weekly_digest_enabled=True)
        EmailEvent.objects.create(
            user=user,
            to_email=user.email,
            subject="Private subject",
            template_name="digest.html",
            idempotency_key="private-email-event",
        )
        UserEvent.objects.create(user=user, event_type="private_event", metadata={"cv": "private"})
        LLMRequestLog.objects.create(
            user=user,
            purpose="cv_extraction",
            model_name="test-model",
            status="success",
            error_message="private error",
        )

        req = DeletionRequest.objects.create(user=user)
        processed = AccountDeletionService.process_request(req)

        self.assertEqual(processed.status, "completed")
        self.assertFalse(CandidateProfile.objects.filter(pk=profile.pk).exists())
        self.assertFalse(CVParsedData.objects.filter(cv_upload=cv).exists())
        self.assertFalse(CVUpload.objects.filter(pk=cv.pk).exists())
        self.assertTrue(CVUpload.all_objects.filter(pk=cv.pk, deleted_at__isnull=False).exists())
        self.assertFalse(SavedJob.objects.filter(user=user).exists())
        self.assertFalse(MatchResult.objects.filter(user=user).exists())
        self.assertFalse(JobRecommendation.objects.filter(user=user).exists())
        self.assertFalse(EmailPreference.objects.filter(user=user).exists())
        self.assertFalse(UserEvent.objects.filter(user=user).exists())
        self.assertEqual(UserEvent.objects.filter(user=None, metadata={}).count(), 2)
        self.assertEqual(EmailEvent.objects.get(idempotency_key="private-email-event").to_email, "deleted-user@deleted.local")
        self.assertIsNone(LLMRequestLog.objects.get(purpose="cv_extraction").user)
        self.assertIsNone(RecommendationRun.objects.get(trigger_type="cv_uploaded").user)
        mock_remove.assert_called()

    def _create_job(self):
        now = timezone.now()
        source = JobSource.objects.create(name="Test Source", slug="privacy-test", source_type=SourceType.FIXTURE)
        raw = RawJobRecord.objects.create(
            source=source,
            source_job_id="privacy-job-1",
            raw_payload_json={},
            payload_hash="hash",
            first_seen_at=now,
            last_seen_at=now,
            last_fetched_at=now,
        )
        return NormalizedJob.objects.create(
            source=source,
            raw_record=raw,
            source_job_id="privacy-job-1",
            title="Django Developer",
            company_name="Company",
            remote_type="remote",
            job_type="full_time_job",
            experience_level="junior",
            description="Build Django applications",
            first_seen_at=now,
            last_seen_at=now,
            last_fetched_at=now,
        )


class PrivacyTaskTests(TestCase):
    def test_process_account_deletion_task_delegates_to_service(self):
        request = DeletionRequest(id=123, status="pending")
        with patch("apps.privacy.tasks.DeletionRequest.objects.get", return_value=request) as mock_get:
            with patch("apps.privacy.tasks.AccountDeletionService.process_request", return_value=request) as mock_process:
                from apps.privacy.tasks import process_account_deletion

                result = process_account_deletion(123)

        mock_get.assert_called_once_with(id=123)
        mock_process.assert_called_once_with(request)
        self.assertEqual(result, "pending")
