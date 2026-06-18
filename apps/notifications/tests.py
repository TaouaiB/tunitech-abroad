from django.test import TestCase
from django.db import IntegrityError
from apps.accounts.models import User
from .models import EmailPreference, EmailBatch, EmailEvent, EmailUnsubscribeToken

def create_test_user(username: str, email: str, password: str = "password123") -> User:
    user = User(username=username, email=email)
    user.set_password(password)
    user.save()
    return user

class EmailPreferenceTests(TestCase):
    def test_email_preference_creation(self):
        user = create_test_user(username="epuser", email="ep@example.test", password="pw")
        pref = EmailPreference.objects.create(user=user)
        
        self.assertEqual(pref.user, user)
        self.assertFalse(pref.product_updates_enabled)
        self.assertFalse(pref.weekly_digest_enabled)
        self.assertTrue(pref.cv_analysis_email_enabled)

class EmailModelsTests(TestCase):
    def setUp(self):
        self.user = create_test_user(username="testuser", email="test@example.test")
        
    def test_email_batch_creation(self):
        batch = EmailBatch.objects.create(batch_type="weekly_digest", status="pending")
        self.assertEqual(batch.batch_type, "weekly_digest")
        self.assertEqual(batch.status, "pending")
        self.assertIsNotNone(batch.public_id)

    def test_email_event_creation(self):
        batch = EmailBatch.objects.create()
        event = EmailEvent.objects.create(
            user=self.user,
            batch=batch,
            email_type="weekly_digest",
            to_email="test@example.test",
            subject="Test Subject",
            template_name="test_template",
            status="queued",
            idempotency_key="key_123"
        )
        self.assertEqual(event.status, "queued")
        self.assertEqual(event.idempotency_key, "key_123")
        self.assertIsNotNone(event.public_id)

    def test_email_event_idempotency_key_is_unique(self):
        EmailEvent.objects.create(
            user=self.user,
            email_type="weekly_digest",
            to_email="test@example.test",
            subject="Test Subject",
            template_name="test_template",
            idempotency_key="unique_key_123"
        )

        with self.assertRaises(IntegrityError):
            EmailEvent.objects.create(
                user=self.user,
                email_type="weekly_digest",
                to_email="test@example.test",
                subject="Test Subject",
                template_name="test_template",
                idempotency_key="unique_key_123"
            )

    def test_email_unsubscribe_token_creation(self):
        token = EmailUnsubscribeToken.objects.create(user=self.user, email_type="weekly_digest")
        self.assertIsNotNone(token.token)
        self.assertIsNotNone(token.public_id)
        self.assertEqual(token.email_type, "weekly_digest")

    def test_email_unsubscribe_token_is_unique(self):
        token = EmailUnsubscribeToken.objects.create(user=self.user, email_type="weekly_digest")

        with self.assertRaises(IntegrityError):
            EmailUnsubscribeToken.objects.create(
                user=self.user,
                email_type="weekly_digest",
                token=token.token,
            )

from django.core import mail
from apps.notifications.services.email_sender import EmailSenderService

class EmailSenderServiceTests(TestCase):
    def setUp(self):
        self.user = create_test_user(username="sender", email="sender@example.test")
        
    def test_send_email_success(self):
        event = EmailSenderService.send(
            to="test@example.test",
            subject="Test Subject",
            template_name="test_template",
            context={"name": "Bob"},
            idempotency_key="key_send_1"
        )
        self.assertEqual(event.status, "sent")
        self.assertEqual(len(mail.outbox), 1)
        
        email = mail.outbox[0]
        self.assertEqual(email.subject, "Test Subject")
        self.assertIn("Hello Bob", email.body)
        self.assertEqual(email.to, ["test@example.test"])
        
    def test_duplicate_idempotency_key_does_not_send(self):
        EmailSenderService.send(
            to="test@example.test",
            subject="Test Subject",
            template_name="test_template",
            context={"name": "Bob"},
            idempotency_key="key_send_2"
        )
        self.assertEqual(len(mail.outbox), 1)
        
        event2 = EmailSenderService.send(
            to="test@example.test",
            subject="Test Subject 2",
            template_name="test_template",
            context={"name": "Bob"},
            idempotency_key="key_send_2"
        )
        # Should not send again
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(event2.status, "sent")  # It returns the existing event
        self.assertEqual(event2.subject, "Test Subject")

    def test_send_email_failure_records_failed_event(self):
        event = EmailSenderService.send(
            to="test@example.test",
            subject="Missing Template",
            template_name="missing_template",
            context={"name": "Bob"},
            idempotency_key="key_missing_template"
        )

        self.assertEqual(event.status, "failed")
        self.assertIn("missing_template", event.error_message)
        self.assertEqual(len(mail.outbox), 0)

from apps.notifications.services.preferences import EmailPreferenceService
from apps.privacy.models import ConsentRecord
from django.urls import reverse

class EmailPreferenceServiceTests(TestCase):
    def setUp(self):
        self.user = create_test_user(username="prefuser", email="pref@example.test")
        
    def test_update_preferences_creates_consent(self):
        pref = EmailPreferenceService.update_preferences(self.user, {"weekly_digest_enabled": True})
        self.assertTrue(pref.weekly_digest_enabled)
        
        # Should create a consent record
        self.assertEqual(ConsentRecord.objects.filter(user=self.user, consent_type="email_digest").count(), 1)
        
        # Updating again should not create another consent record
        pref = EmailPreferenceService.update_preferences(self.user, {"weekly_digest_enabled": True})
        self.assertEqual(ConsentRecord.objects.filter(user=self.user, consent_type="email_digest").count(), 1)

    def test_unsubscribe_valid_token(self):
        token = EmailUnsubscribeToken.objects.create(user=self.user, email_type="weekly_digest")
        pref = EmailPreference.objects.create(user=self.user, weekly_digest_enabled=True)
        
        result = EmailPreferenceService.unsubscribe(str(token.token))
        self.assertTrue(result.success)
        
        pref.refresh_from_db()
        self.assertFalse(pref.weekly_digest_enabled)
        
        token.refresh_from_db()
        self.assertIsNotNone(token.used_at)

    def test_unsubscribe_reused_token_is_idempotent(self):
        token = EmailUnsubscribeToken.objects.create(user=self.user, email_type="weekly_digest")
        pref = EmailPreference.objects.create(user=self.user, weekly_digest_enabled=True)

        first_result = EmailPreferenceService.unsubscribe(str(token.token))
        pref.weekly_digest_enabled = True
        pref.save(update_fields=["weekly_digest_enabled"])
        second_result = EmailPreferenceService.unsubscribe(str(token.token))

        pref.refresh_from_db()
        self.assertTrue(first_result.success)
        self.assertTrue(second_result.success)
        self.assertTrue(pref.weekly_digest_enabled)

    def test_unsubscribe_product_update_token(self):
        token = EmailUnsubscribeToken.objects.create(user=self.user, email_type="product_update")
        pref = EmailPreference.objects.create(
            user=self.user,
            weekly_digest_enabled=True,
            product_updates_enabled=True,
        )

        result = EmailPreferenceService.unsubscribe(str(token.token))

        pref.refresh_from_db()
        self.assertTrue(result.success)
        self.assertTrue(pref.weekly_digest_enabled)
        self.assertFalse(pref.product_updates_enabled)

    def test_unsubscribe_all_token(self):
        token = EmailUnsubscribeToken.objects.create(user=self.user, email_type="all")
        pref = EmailPreference.objects.create(
            user=self.user,
            weekly_digest_enabled=True,
            product_updates_enabled=True,
        )

        result = EmailPreferenceService.unsubscribe(str(token.token))

        pref.refresh_from_db()
        self.assertTrue(result.success)
        self.assertFalse(pref.weekly_digest_enabled)
        self.assertFalse(pref.product_updates_enabled)

    def test_unsubscribe_malformed_token_is_safe(self):
        result = EmailPreferenceService.unsubscribe("not-a-uuid")

        self.assertFalse(result.success)
        self.assertEqual(result.error, "Invalid token format")

class EmailPreferenceViewsTests(TestCase):
    def setUp(self):
        self.user = create_test_user(username="viewuser", email="view@example.test")
        self.client.force_login(self.user)
        
    def test_email_preferences_view_get(self):
        url = reverse("notifications:email_preferences")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_email_preferences_dashboard_route_get(self):
        url = reverse("dashboard:email_preferences")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_email_preferences_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("dashboard:email_preferences"))
        self.assertEqual(response.status_code, 302)
        
    def test_email_preferences_view_post(self):
        url = reverse("notifications:email_preferences")
        response = self.client.post(url, {"weekly_digest_enabled": True})
        self.assertRedirects(response, url)
        
        pref = EmailPreference.objects.get(user=self.user)
        self.assertTrue(pref.weekly_digest_enabled)
        
    def test_unsubscribe_view_success(self):
        token = EmailUnsubscribeToken.objects.create(user=self.user, email_type="weekly_digest")
        url = reverse("notifications:unsubscribe", kwargs={"token": str(token.token)})
        
        self.client.logout() # Ensure it works without login
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)

    def test_unsubscribe_view_get_does_not_mutate(self):
        token = EmailUnsubscribeToken.objects.create(user=self.user, email_type="weekly_digest")
        pref = EmailPreference.objects.create(user=self.user, weekly_digest_enabled=True)
        url = reverse("notifications:unsubscribe", kwargs={"token": str(token.token)})

        self.client.logout()
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        pref.refresh_from_db()
        token.refresh_from_db()
        self.assertTrue(pref.weekly_digest_enabled)
        self.assertIsNone(token.used_at)

    def test_unsubscribe_view_post_mutates(self):
        token = EmailUnsubscribeToken.objects.create(user=self.user, email_type="weekly_digest")
        pref = EmailPreference.objects.create(user=self.user, weekly_digest_enabled=True)
        url = reverse("notifications:unsubscribe", kwargs={"token": str(token.token)})

        self.client.logout()
        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)
        pref.refresh_from_db()
        token.refresh_from_db()
        self.assertFalse(pref.weekly_digest_enabled)
        self.assertIsNotNone(token.used_at)
        
    def test_unsubscribe_view_invalid_token(self):
        import uuid
        url = reverse("notifications:unsubscribe", kwargs={"token": str(uuid.uuid4())})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

from unittest.mock import patch
from apps.notifications.services.weekly_digest import WeeklyDigestService
from apps.recommendations.models import JobRecommendation
from allauth.account.models import EmailAddress
from apps.profiles.models import CandidateProfile
from django.utils import timezone

class WeeklyDigestServiceTests(TestCase):
    def setUp(self):
        self.user = create_test_user(username="digestuser", email="digest@example.test")
        self.user.last_login = timezone.now()
        self.user.save()
        
        self.profile = CandidateProfile.objects.create(user=self.user, profile_completion_score=100)
        
        EmailAddress.objects.create(user=self.user, email="digest@example.test", verified=True, primary=True)
        EmailPreference.objects.create(user=self.user, weekly_digest_enabled=True)
        
        from apps.jobs.models import NormalizedJob, JobSource, RawJobRecord
        source = JobSource.objects.create(name="Test Source", slug="test", source_type="fixture")
        raw = RawJobRecord.objects.create(
            source=source, 
            source_job_id="test", 
            raw_payload_json={}, 
            payload_hash="test", 
            first_seen_at=timezone.now(), 
            last_seen_at=timezone.now(), 
            last_fetched_at=timezone.now()
        )
        job = NormalizedJob.objects.create(
            public_id="00000000-0000-0000-0000-000000000001",
            source=source,
            raw_record=raw,
            source_job_id="test",
            title="Test Job",
            company_name="Test Company",
            location="Paris",
            job_type="full_time_job",
            remote_type="remote",
            experience_level="mid_level",
            first_seen_at=timezone.now(),
            last_seen_at=timezone.now(),
            last_fetched_at=timezone.now()
        )
        JobRecommendation.objects.create(
            user=self.user,
            profile=self.profile,
            job=job,
            fit_score=85,
            ranking_score=8.5,
            rank=1,
            status="active",
            computed_at=timezone.now()
        )
        
    def test_weekly_digest_success(self):
        batch = WeeklyDigestService.send_weekly_digest()
        
        self.assertEqual(batch.status, "completed")
        self.assertEqual(batch.sent_count, 1)
        self.assertEqual(batch.skipped_count, 0)
        self.assertEqual(EmailEvent.objects.filter(email_type="weekly_digest").count(), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("/email/unsubscribe/", mail.outbox[0].body)
        self.assertIn("Test Job", mail.outbox[0].body)
        
    def test_weekly_digest_excludes_unverified(self):
        EmailAddress.objects.filter(user=self.user).update(verified=False)
        batch = WeeklyDigestService.send_weekly_digest()
        
        self.assertEqual(batch.status, "completed")
        self.assertEqual(batch.sent_count, 0)
        self.assertEqual(batch.skipped_count, 1)
        
    def test_weekly_digest_excludes_disabled_pref(self):
        EmailPreference.objects.filter(user=self.user).update(weekly_digest_enabled=False)
        batch = WeeklyDigestService.send_weekly_digest()
        
        self.assertEqual(batch.status, "completed")
        self.assertEqual(batch.sent_count, 0)
        self.assertEqual(batch.skipped_count, 1)

    def test_weekly_digest_excludes_inactive_user(self):
        from datetime import timedelta
        self.user.last_login = timezone.now() - timedelta(days=30)
        self.user.save(update_fields=["last_login"])

        batch = WeeklyDigestService.send_weekly_digest()

        self.assertEqual(batch.status, "completed")
        self.assertEqual(batch.sent_count, 0)
        self.assertEqual(batch.total_recipients, 0)

    def test_weekly_digest_excludes_incomplete_profile(self):
        self.profile.profile_completion_score = 20
        self.profile.save(update_fields=["profile_completion_score"])

        batch = WeeklyDigestService.send_weekly_digest()

        self.assertEqual(batch.status, "completed")
        self.assertEqual(batch.sent_count, 0)
        self.assertEqual(batch.total_recipients, 0)

    def test_weekly_digest_excludes_user_without_recommendations(self):
        JobRecommendation.objects.filter(user=self.user).delete()

        batch = WeeklyDigestService.send_weekly_digest()

        self.assertEqual(batch.status, "completed")
        self.assertEqual(batch.sent_count, 0)
        self.assertEqual(batch.skipped_count, 1)

    def test_weekly_digest_duplicate_run_does_not_duplicate_email(self):
        first_batch = WeeklyDigestService.send_weekly_digest()
        second_batch = WeeklyDigestService.send_weekly_digest()

        self.assertEqual(first_batch.sent_count, 1)
        self.assertEqual(second_batch.sent_count, 0)
        self.assertEqual(second_batch.skipped_count, 1)
        self.assertEqual(EmailEvent.objects.filter(email_type="weekly_digest").count(), 1)
        self.assertEqual(len(mail.outbox), 1)

    @patch("apps.notifications.tasks.WeeklyDigestService.send_weekly_digest")
    def test_weekly_digest_task_delegates_to_service(self, mock_send):
        from apps.notifications.tasks import send_weekly_digest

        batch = EmailBatch.objects.create(batch_type="weekly_digest")
        mock_send.return_value = batch

        result = send_weekly_digest()

        self.assertEqual(result, str(batch.public_id))
        mock_send.assert_called_once_with(None, None)
