import json
from io import BytesIO
from unittest.mock import patch, MagicMock
import urllib.error
from django.test import TestCase, override_settings
from django.utils import timezone
from decimal import Decimal
from apps.jobs.models import NormalizedJob, JobSource, SourceType, RemoteType, JobType, ExperienceLevel, RawJobRecord
from apps.llm.models import JobEnrichment
from apps.llm.services.job_enrichment import enrich_job

class LLMErrorHandlingTests(TestCase):
    def setUp(self):
        source = JobSource.objects.create(name="FT", slug="ft", source_type=SourceType.API)
        raw_record = RawJobRecord.objects.create(
            source=source,
            source_job_id="123",
            raw_payload_json={},
            payload_hash="hash",
            first_seen_at=timezone.now(),
            last_seen_at=timezone.now(),
            last_fetched_at=timezone.now()
        )
        self.job = NormalizedJob.objects.create(
            source=source,
            raw_record=raw_record,
            source_job_id="123",
            title="Test Job",
            description="A job",
            remote_type=RemoteType.UNKNOWN,
            job_type=JobType.UNKNOWN,
            experience_level=ExperienceLevel.UNKNOWN,
            first_seen_at=timezone.now(),
            last_seen_at=timezone.now(),
            last_fetched_at=timezone.now()
        )

    def test_enrichment_403_handling(self):
        # We patch OpenRouterClient._make_request to raise a 403 HTTPError
        unsafe_body_marker = " ".join(["untrusted", "provider", "payload"])
        with patch('apps.llm.services.client.OpenRouterClient._make_request') as mock_make_request:
            mock_make_request.side_effect = urllib.error.HTTPError(
                url="http://fakeurl",
                code=403,
                msg="Forbidden",
                hdrs={},
                fp=MagicMock(read=MagicMock(return_value=json.dumps({"error": unsafe_body_marker}).encode("utf-8"))),
            )
            
            enrichment = enrich_job(self.job, force=True)
            
            self.assertEqual(enrichment.status, JobEnrichment.Status.FAILED)
            self.assertEqual(enrichment.status_reason, "forbidden/provider_blocked")
            self.assertIn("HTTP Error 403", enrichment.last_error)
            self.assertNotIn(unsafe_body_marker, enrichment.last_error)
            self.assertEqual(mock_make_request.call_count, 1)
            
            # Verify no tokens or payload recorded
            self.assertEqual(enrichment.total_tokens, 0)
            self.assertEqual(enrichment.estimated_cost_usd, Decimal("0"))
            self.assertEqual(enrichment.raw_request_json, {})
            self.assertEqual(enrichment.raw_response_text, "")

    @override_settings(JOB_ENRICHMENT_ENABLED=True, JOB_ENRICHMENT_MAX_RETRIES=2)
    def test_enrichment_403_key_daily_limit_is_safe_permanent_classification(self):
        provider_body = json.dumps(
            {"error": {"message": " ".join(["Key", "limit", "exceeded", "(daily", "limit)"]), "code": 403}}
        ).encode("utf-8")
        with patch('apps.llm.services.client.OpenRouterClient._make_request') as mock_make_request:
            mock_make_request.side_effect = urllib.error.HTTPError(
                url="http://fakeurl",
                code=403,
                msg="Forbidden",
                hdrs={},
                fp=BytesIO(provider_body),
            )

            enrichment = enrich_job(self.job, force=True)

            self.assertEqual(enrichment.status, JobEnrichment.Status.FAILED)
            self.assertEqual(enrichment.status_reason, "key_daily_limit_exceeded")
            self.assertEqual(enrichment.last_error, "HTTP Error 403: key_daily_limit_exceeded")
            self.assertNotIn("Key limit exceeded", enrichment.last_error)
            self.assertNotIn("daily limit", enrichment.last_error)
            self.assertNotIn("error", enrichment.last_error)
            self.assertEqual(mock_make_request.call_count, 1)
            self.assertEqual(enrichment.raw_request_json, {})
            self.assertEqual(enrichment.raw_response_text, "")
            self.assertEqual(enrichment.raw_response_json, {})

    def test_enrichment_missing_api_key(self):
        with patch('apps.llm.services.client.OpenRouterClient._make_request') as mock_make_request:
            # client raises ValueError when API key is missing
            mock_make_request.side_effect = ValueError("OPENROUTER_API_KEY is not set.")
            
            enrichment = enrich_job(self.job, force=True)
            
            self.assertEqual(enrichment.status, JobEnrichment.Status.FAILED)
            self.assertEqual(enrichment.status_reason, "missing_api_key")
            self.assertEqual(enrichment.total_tokens, 0)
            self.assertEqual(enrichment.raw_request_json, {})

    @override_settings(JOB_ENRICHMENT_ENABLED=True, LLM_ENABLED=True, OPENROUTER_API_KEY="")
    def test_missing_api_key_does_not_attempt_http_call(self):
        with patch("urllib.request.urlopen") as mock_urlopen:
            enrichment = enrich_job(self.job, force=True)

        self.assertEqual(enrichment.status, JobEnrichment.Status.FAILED)
        self.assertEqual(enrichment.status_reason, "missing_api_key")
        mock_urlopen.assert_not_called()

    @override_settings(JOB_ENRICHMENT_ENABLED=True, JOB_ENRICHMENT_MAX_RETRIES=2)
    def test_429_uses_bounded_retry_backoff(self):
        with patch('apps.llm.services.client.OpenRouterClient._make_request') as mock_make_request, \
             patch('apps.llm.services.job_enrichment._sleep_before_provider_retry') as mock_sleep:
            mock_make_request.side_effect = urllib.error.HTTPError(
                url="http://fakeurl", code=429, msg="Too Many Requests", hdrs={}, fp=None
            )

            enrichment = enrich_job(self.job, force=True)

        self.assertEqual(enrichment.status, JobEnrichment.Status.FAILED)
        self.assertEqual(enrichment.status_reason, "rate_limited")
        self.assertEqual(mock_make_request.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)
