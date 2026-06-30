from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core import mail
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from unittest.mock import patch

from apps.core.models import AdminAlertEvent, AdminFileAccessLog
from apps.core.services.alerts import AdminAlertService
from apps.core.services.digest import AdminOpsDigestService
from apps.core.services.health import HealthCheckService
from apps.cvs.models import CVUpload


User = get_user_model()


class Phase16GAdminMonitoringTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_superuser(
            username="owner",
            email="owner@example.test",
            password="pass",
        )
        self.staff = User.objects.create_user(
            username="staff",
            email="staff@example.test",
            password="pass",
            is_staff=True,
        )
        self.user = User.objects.create_user(
            username="candidate",
            email="candidate@example.test",
            password="pass",
        )
        self.cv = CVUpload.objects.create(
            user=self.user,
            file=ContentFile(b"%PDF-1.4\nsafe test pdf", name="cv.pdf"),
            original_filename="cv.pdf",
            file_hash="hash",
            file_size=22,
            mime_type="application/pdf",
            is_active=True,
        )

    def test_cv_download_is_superuser_only_and_logs_access(self):
        self.client.login(email="owner@example.test", password="pass")
        response = self.client.get(reverse("admin_cv_download", kwargs={"public_id": self.cv.public_id}))

        self.assertEqual(response.status_code, 200)
        log = AdminFileAccessLog.objects.get()
        self.assertEqual(log.admin_user, self.owner)
        self.assertEqual(log.object_public_id, self.cv.public_id)
        self.assertEqual(log.action, "download")

    def test_staff_without_superuser_cannot_download_cv(self):
        self.client.login(email="staff@example.test", password="pass")
        response = self.client.get(reverse("admin_cv_download", kwargs={"public_id": self.cv.public_id}))

        self.assertEqual(response.status_code, 403)
        self.assertFalse(AdminFileAccessLog.objects.exists())

    @override_settings(ADMIN_ALERT_EMAIL="ops@example.test", EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_admin_alert_sends_to_env_configured_email_and_redacts_sensitive_keys(self):
        event = AdminAlertService.trigger_alert(
            "celery_heartbeat_missing",
            "critical",
            "Celery heartbeat missing",
            {"token": "do-not-send", "active_jobs": 10},
        )

        self.assertEqual(event.status, "sent")
        self.assertEqual(event.sent_to, "ops@example.test")
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("active_jobs", mail.outbox[0].body)
        self.assertNotIn("do-not-send", mail.outbox[0].body)

    def test_health_check_uses_shared_diagnostics_shape(self):
        payload = HealthCheckService.run()

        self.assertEqual(payload["service"], "health_check")
        self.assertIn("generated_at", payload)
        self.assertIn("counts", payload)
        self.assertIn("statuses", payload)
        self.assertIn("warnings", payload)
        self.assertIn("errors", payload)
        self.assertIn("recommended_actions", payload)

    @override_settings(ADMIN_ALERT_EMAIL="ops@example.test", EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_duplicate_alert_is_deduplicated(self):
        first = AdminAlertService.trigger_alert("zero_visible_jobs", "critical", "No visible jobs")
        second = AdminAlertService.trigger_alert("zero_visible_jobs", "critical", "No visible jobs")

        self.assertEqual(first.id, second.id)
        self.assertEqual(AdminAlertEvent.objects.count(), 1)


# ── Blocker #2 & #3: Digest correctness tests ─────────────────────────────────

class DigestServiceTests(TestCase):
    """Focused tests for AdminOpsDigestService.generate_digest()."""

    def test_generate_digest_runs_without_field_error(self):
        """generate_digest() must not raise FieldError (validates uploaded_at field)."""
        digest = AdminOpsDigestService.generate_digest()
        self.assertIsInstance(digest, dict)

    def test_digest_counts_cvs_using_uploaded_at(self):
        """new_cvs must count CVUpload rows using uploaded_at (not created_at)."""
        user = User.objects.create_user(
            username="cv_user",
            email="cvuser@example.test",
            password="pass",
        )
        CVUpload.objects.create(
            user=user,
            file=ContentFile(b"%PDF-1.4\ntest", name="cv2.pdf"),
            original_filename="cv2.pdf",
            file_hash="hash2",
            file_size=14,
            mime_type="application/pdf",
            is_active=True,
        )
        digest = AdminOpsDigestService.generate_digest()
        # At least one CV exists and was just uploaded (within last 24 h).
        self.assertGreaterEqual(digest["new_cvs"], 1)

    def test_digest_contains_required_keys(self):
        """Digest must include ingestion counts, zero-result search bucket, and LLM flag."""
        digest = AdminOpsDigestService.generate_digest()
        required_keys = [
            "new_users",
            "new_cvs",
            "parse_success",
            "parse_failed",
            "active_jobs",
            "public_jobs",
            "matchable_jobs",
            "unknown_skills",
            "email_failures",
            "ingestion_runs_total",
            "ingestion_runs_failed",
            "zero_result_search_count",
            "total_search_count",
            "llm_cost_unavailable",
        ]
        for key in required_keys:
            with self.subTest(key=key):
                self.assertIn(key, digest)

    def test_digest_llm_cost_flag_is_true(self):
        """llm_cost_unavailable must be True before Phase 9 LLM infrastructure exists."""
        digest = AdminOpsDigestService.generate_digest()
        self.assertTrue(digest["llm_cost_unavailable"])


# ── Blocker #4: Public health endpoint must not leak raw exception strings ─────

class HealthPublicSafetyTests(TestCase):
    """Health endpoint must return safe codes only, not raw exception strings."""

    @patch("apps.core.services.health.connection")
    def test_db_exception_does_not_leak_into_response(self, mock_conn):
        mock_conn.ensure_connection.side_effect = Exception(
            "could not connect to server: password 'super_secret_pw' refused"
        )
        payload = HealthCheckService.run()

        # Safe code must appear.
        self.assertIn("database_unavailable", payload["errors"])

        # Raw exception string must NOT appear anywhere in the response.
        import json
        payload_str = json.dumps(payload)
        self.assertNotIn("super_secret_pw", payload_str)
        self.assertNotIn("could not connect", payload_str)

    @patch("apps.core.services.health.cache")
    def test_redis_exception_does_not_leak_into_response(self, mock_cache):
        mock_cache.set.side_effect = Exception("redis://user:redis_token@127.0.0.1:6379 refused")
        payload = HealthCheckService.run()

        self.assertIn("redis_unavailable", payload["errors"])

        import json
        payload_str = json.dumps(payload)
        self.assertNotIn("redis_token", payload_str)
        self.assertNotIn("redis://user:", payload_str)

    @patch("apps.core.services.health.NormalizedJob")
    def test_jobs_exception_does_not_leak_into_response(self, mock_job):
        mock_job.objects.filter.side_effect = Exception(
            "jobs_check internal_path=/srv/private secret_path exposed"
        )
        payload = HealthCheckService.run()

        self.assertIn("jobs_check_failed", payload["errors"])

        import json
        payload_str = json.dumps(payload)
        self.assertNotIn("internal_path", payload_str)
        self.assertNotIn("secret_path", payload_str)


# ── Blocker #5: ok must not be True when errors are present ───────────────────

class HealthOkSemanticsTests(TestCase):
    """ok=True must only occur when errors is empty."""

    def test_health_endpoint_returns_200_when_shared_ok_is_true(self):
        with patch(
            "config.urls.HealthCheckService.check",
            return_value={"ok": True, "status": "ok"},
        ):
            response = self.client.get(reverse("health"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ok"])

    def test_health_endpoint_returns_503_when_shared_ok_is_false_despite_ok_status(self):
        with patch(
            "config.urls.HealthCheckService.check",
            return_value={
                "ok": False,
                "status": "ok",
                "errors": ["jobs_check_failed"],
            },
        ):
            response = self.client.get(reverse("health"))

        self.assertEqual(response.status_code, 503)
        self.assertFalse(response.json()["ok"])
        self.assertEqual(response.json()["errors"], ["jobs_check_failed"])

    @patch("apps.core.services.health.connection")
    def test_ok_is_false_when_db_fails(self, mock_conn):
        mock_conn.ensure_connection.side_effect = Exception("db down")
        payload = HealthCheckService.run()

        self.assertFalse(payload["ok"])
        self.assertIn("database_unavailable", payload["errors"])

    @patch("apps.core.services.health.cache")
    def test_ok_is_false_when_redis_fails(self, mock_cache):
        mock_cache.set.side_effect = Exception("redis down")
        payload = HealthCheckService.run()

        self.assertFalse(payload["ok"])
        self.assertIn("redis_unavailable", payload["errors"])

    def test_ok_is_true_when_no_errors(self):
        """Nominal run should produce ok=True and empty errors list."""
        payload = HealthCheckService.run()

        if payload["errors"]:
            # In test DB there may be infra unavailable; just verify the logic.
            self.assertFalse(payload["ok"])
        else:
            self.assertTrue(payload["ok"])

    @patch("apps.core.services.health.NormalizedJob")
    def test_ok_is_false_when_jobs_check_fails(self, mock_job):
        mock_job.objects.filter.side_effect = Exception("jobs error")
        payload = HealthCheckService.run()

        # jobs_check_failed goes into errors → ok must be False.
        self.assertIn("jobs_check_failed", payload["errors"])
        self.assertFalse(payload["ok"])

    def test_non_numeric_cached_active_jobs_baseline_does_not_fail_jobs_check(self):
        cache.set("health_last_active_jobs", "not-a-number", timeout=60)

        payload = HealthCheckService.run()

        self.assertNotIn("jobs_check_failed", payload["errors"])
        self.assertTrue(payload["ok"])


# ── Blocker #6: Recursive sanitization of nested sensitive keys ────────────────

class AlertSanitizationTests(TestCase):
    """_sanitize_details must recursively redact nested sensitive keys."""

    def test_nested_sensitive_key_is_redacted(self):
        details = {
            "counts": {"active_jobs": 5},
            "auth": {
                "token": "secret_bearer_xyz",
                "user": "admin",
            },
        }
        result = AdminAlertService._sanitize_details(details)

        # Non-sensitive top-level key preserved.
        self.assertEqual(result["counts"]["active_jobs"], 5)
        # Sensitive nested key redacted.
        self.assertEqual(result["auth"]["token"], "[redacted]")
        # Non-sensitive sibling preserved.
        self.assertEqual(result["auth"]["user"], "admin")

    def test_list_with_nested_sensitive_key_is_redacted(self):
        details = {
            "items": [
                {"password": "abc123", "status": "ok"},
            ]
        }
        result = AdminAlertService._sanitize_details(details)

        self.assertEqual(result["items"][0]["password"], "[redacted]")
        self.assertEqual(result["items"][0]["status"], "ok")

    @override_settings(
        ADMIN_ALERT_EMAIL="ops@example.test",
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    )
    def test_nested_sensitive_keys_not_in_email_body(self):
        details = {
            "env": {"api_key": "super_private_key", "region": "eu-west"},
        }
        event = AdminAlertService.trigger_alert(
            "test_nested_redaction",
            "warning",
            "Nested redaction test",
            details,
        )

        self.assertEqual(len(mail.outbox), 1)
        self.assertNotIn("super_private_key", mail.outbox[0].body)
        self.assertEqual(event.details_json["env"]["api_key"], "[redacted]")
        self.assertEqual(event.details_json["env"]["region"], "eu-west")

    def test_non_sensitive_numeric_values_are_not_redacted(self):
        details = {"active_jobs": 42, "failed_count": 0}
        result = AdminAlertService._sanitize_details(details)

        self.assertEqual(result["active_jobs"], 42)
        self.assertEqual(result["failed_count"], 0)


# ── Blocker #1 repair: Redis robustness — baseline cache and heartbeat ─────────

class HealthRedisRobustnessTests(TestCase):
    """Verify that cache failures inside the Jobs section or Celery heartbeat
    section never produce jobs_check_failed and never crash HealthCheckService."""

    def _make_cache_side_effects(self, *extra_effects):
        """Return a callable suitable for cache.set side_effect.

        The first call (health probe: cache.set('health_check_test', ...)) must
        succeed so Redis is considered available. Subsequent set() calls get the
        provided extra_effects in order.
        """
        effects = [None] + list(extra_effects)
        iterator = iter(effects)

        def _side_effect(*args, **kwargs):
            val = next(iterator, None)
            if isinstance(val, Exception):
                raise val
            return val

        return _side_effect

    def _make_cache_get_side_effects(self, *extra_effects):
        """Return a callable suitable for cache.get side_effect.

        First get() call is the Redis probe ('health_check_test') — return '1'.
        Subsequent get() calls get the provided extra_effects.
        """
        effects = ["1"] + list(extra_effects)
        iterator = iter(effects)

        def _side_effect(*args, **kwargs):
            val = next(iterator, StopIteration)
            if val is StopIteration:
                return None
            if isinstance(val, Exception):
                raise val
            return val

        return _side_effect

    @patch("apps.core.services.health.JobEligibilityService")
    @patch("apps.core.services.health.NormalizedJob")
    @patch("apps.core.services.health.cache")
    def test_baseline_cache_get_failure_does_not_add_jobs_check_failed(
        self, mock_cache, mock_job, mock_eligibility
    ):
        """cache.get('health_last_active_jobs') raising must NOT add jobs_check_failed."""
        mock_job.objects.filter.return_value.count.return_value = 10
        mock_eligibility.filter_matchable.return_value.count.return_value = 10
        mock_eligibility.filter_publicly_visible.return_value.count.return_value = 10
        mock_cache.set.return_value = None
        # probe get returns '1'; baseline get raises
        mock_cache.get.side_effect = self._make_cache_get_side_effects(
            Exception("Redis gone")  # baseline get raises
        )

        payload = HealthCheckService.run()

        self.assertNotIn("jobs_check_failed", payload["errors"])
        # The baseline cache failure adds a warning, not an error.
        self.assertIn("jobs_baseline_cache_unavailable", payload["warnings"])

    @patch("apps.core.services.health.JobEligibilityService")
    @patch("apps.core.services.health.NormalizedJob")
    @patch("apps.core.services.health.cache")
    def test_baseline_cache_set_failure_does_not_add_jobs_check_failed(
        self, mock_cache, mock_job, mock_eligibility
    ):
        """cache.set('health_last_active_jobs', ...) raising must NOT add jobs_check_failed."""
        mock_job.objects.filter.return_value.count.return_value = 10
        mock_eligibility.filter_matchable.return_value.count.return_value = 10
        mock_eligibility.filter_publicly_visible.return_value.count.return_value = 10
        # probe get returns '1'; baseline get returns None (no stored baseline)
        mock_cache.get.side_effect = self._make_cache_get_side_effects(
            None  # baseline get: no stored value
        )
        # first set (probe) succeeds; second set (baseline write) raises
        mock_cache.set.side_effect = self._make_cache_side_effects(
            Exception("Redis gone on set")
        )

        payload = HealthCheckService.run()

        self.assertNotIn("jobs_check_failed", payload["errors"])
        self.assertIn("jobs_baseline_cache_unavailable", payload["warnings"])

    @patch("apps.core.services.health.JobEligibilityService")
    @patch("apps.core.services.health.NormalizedJob")
    @patch("apps.core.services.health.cache")
    def test_heartbeat_cache_get_failure_does_not_crash_and_returns_safe_diagnostic(
        self, mock_cache, mock_job, mock_eligibility
    ):
        """cache.get(CELERY_HEARTBEAT_CACHE_KEY) raising must not crash run()
        and must produce a safe warning code instead of an unhandled exception."""
        mock_job.objects.filter.return_value.count.return_value = 10
        mock_eligibility.filter_matchable.return_value.count.return_value = 10
        mock_eligibility.filter_publicly_visible.return_value.count.return_value = 10
        mock_cache.set.return_value = None
        # probe get returns '1'; baseline get returns None; heartbeat get raises
        mock_cache.get.side_effect = self._make_cache_get_side_effects(
            None,                        # baseline get
            Exception("Redis gone"),     # heartbeat get
        )

        payload = HealthCheckService.run()

        # Must not crash.
        self.assertIsInstance(payload, dict)
        # Must produce a safe warning, not an error.
        self.assertIn("celery_heartbeat_check_unavailable", payload["warnings"])
        self.assertNotIn("jobs_check_failed", payload["errors"])

    @patch("apps.core.services.health.JobEligibilityService")
    @patch("apps.core.services.health.NormalizedJob")
    @patch("apps.core.services.health.cache")
    def test_health_endpoint_returns_json_not_500_when_heartbeat_cache_fails(
        self, mock_cache, mock_job, mock_eligibility
    ):
        """/health/ must return JSON (200 or 503), never a 500 crash."""
        mock_job.objects.filter.return_value.count.return_value = 5
        mock_eligibility.filter_matchable.return_value.count.return_value = 5
        mock_eligibility.filter_publicly_visible.return_value.count.return_value = 5
        mock_cache.set.return_value = None
        mock_cache.get.side_effect = self._make_cache_get_side_effects(
            None,
            Exception("heartbeat cache exploded"),
        )

        response = self.client.get(reverse("health"))

        self.assertIn(response.status_code, [200, 503])
        data = response.json()
        self.assertIn("ok", data)

    @patch("config.urls.HealthCheckService.check")
    def test_health_endpoint_returns_safe_json_when_service_unexpectedly_fails(
        self, mock_check
    ):
        """Unexpected health service exceptions must not make /health/ leak or 500."""
        fake_secret = "health_service_token_SHOULD_NOT_LEAK"
        mock_check.side_effect = Exception(f"provider failed with token={fake_secret}")

        response = self.client.get(reverse("health"))
        data = response.json()

        self.assertEqual(response.status_code, 503)
        self.assertFalse(data["ok"])
        self.assertEqual(data["errors"], ["health_check_unavailable"])

        import json
        payload_text = json.dumps(data)
        self.assertNotIn(fake_secret, payload_text)
        self.assertNotIn("provider failed", payload_text)

# ── Blocker #2 repair: Alert email failure must not log raw exception text ──────

class AlertEmailSafeLogTests(TestCase):
    """Verify that send_mail failure does not expose raw exception text in
    details_json, and that the log message is fixed (not logger.exception)."""

    @override_settings(
        ADMIN_ALERT_EMAIL="ops@example.test",
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    )
    @patch("apps.core.services.alerts.send_mail")
    def test_send_mail_failure_stores_safe_error_code_not_raw_exception(
        self, mock_send_mail
    ):
        """When send_mail raises with a fake secret, details_json must only
        contain the safe code 'email_send_failed', not the raw exception text."""
        fake_secret = "smtp_token_FAKE12345SECRET"
        mock_send_mail.side_effect = Exception(
            f"SMTP auth failed: password={fake_secret}"
        )

        event = AdminAlertService.trigger_alert(
            alert_type="test_email_log_safety",
            severity="critical",
            summary="Test: email send failure safety",
            details={"active_jobs": 1},
        )

        # Safe code must be present.
        self.assertEqual(event.details_json.get("send_error"), "email_send_failed")

        # Raw secret must NOT be anywhere in details_json.
        import json
        details_str = json.dumps(event.details_json)
        self.assertNotIn(fake_secret, details_str)
        self.assertNotIn("smtp_token", details_str)
