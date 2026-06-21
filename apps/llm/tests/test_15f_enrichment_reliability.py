import json
from django.test import TestCase, override_settings
from unittest.mock import patch, MagicMock
from django.utils import timezone
from apps.jobs.models import JobStatus, NormalizedJob, JobSource, RawJobRecord
from apps.llm.models import JobEnrichment
from apps.llm.services.job_enrichment import enrich_job, _extract_json, EnrichmentReason, get_openrouter_circuit_status

class EnrichmentReliabilityTests(TestCase):
    def setUp(self):
        self.source = JobSource.objects.create(name="Test Source", slug="test-source", source_type="fixture")
        self.raw = RawJobRecord.objects.create(
            source=self.source,
            source_job_id="test1",
            first_seen_at=timezone.now(),
            last_seen_at=timezone.now(),
            last_fetched_at=timezone.now(),
            payload_hash="hash1",
            raw_payload_json={}
        )
        self.job = NormalizedJob.objects.create(
            source=self.source,
            raw_record=self.raw,
            source_job_id="test1",
            title="Senior Python Developer",
            description="We need a Python developer who knows Django.",
            country="FR",
            status=JobStatus.ACTIVE,
            published_at=timezone.now(),
            first_seen_at=timezone.now(),
            last_seen_at=timezone.now(),
            last_fetched_at=timezone.now(),
            classification_json={"confidence": "high", "family": "software"},
            skill_signal_quality="strong",
        )

    def test_extract_json(self):
        # Plain JSON
        plain = '{"key": "value"}'
        self.assertEqual(_extract_json(plain), '{"key": "value"}')

        # Markdown code fences
        fenced = '```json\n{"key": "value"}\n```'
        self.assertEqual(_extract_json(fenced), '{"key": "value"}')

        # Prose before and after
        prose = 'Here is the JSON:\n```\n{"key": "value"}\n```\nHope it helps!'
        self.assertEqual(_extract_json(prose), '{"key": "value"}')

        # No code fences, just prose
        prose_no_fence = 'Here is the output: {"key": "value"} Done.'
        self.assertEqual(_extract_json(prose_no_fence), '{"key": "value"}')

    @patch("apps.llm.services.job_enrichment.OpenRouterClient.chat")
    def test_json_parsing_success_with_prose(self, mock_chat):
        mock_chat.return_value = (
            'Here is the JSON: ```json\n{"is_it_role": true, "role_family": "software_development"}\n```',
            {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
        )

        enrichment = enrich_job(self.job, force=True)
        self.assertEqual(enrichment.status, JobEnrichment.Status.SUCCESS)
        self.assertEqual(enrichment.validated_output_json["role_family"], "software_development")
        self.assertIn("Here is the JSON", enrichment.raw_response_text)

    @patch("apps.llm.services.job_enrichment.OpenRouterClient.chat")
    def test_invalid_json_retry_success(self, mock_chat):
        # First call returns invalid JSON, second call returns valid JSON
        mock_chat.side_effect = [
            ('Not a json at all', {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}),
            ('{"is_it_role": true, "role_family": "software_development"}', {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}),
        ]

        enrichment = enrich_job(self.job, force=True)
        self.assertEqual(enrichment.status, JobEnrichment.Status.SUCCESS)
        self.assertEqual(enrichment.status_reason, EnrichmentReason.INVALID_JSON_RETRY_SUCCESS)
        self.assertEqual(enrichment.validated_output_json["role_family"], "software_development")
        self.assertEqual(mock_chat.call_count, 2)
        
    @patch("apps.llm.services.job_enrichment.OpenRouterClient.chat")
    def test_invalid_json_retry_failure(self, mock_chat):
        mock_chat.side_effect = [
            ('Not a json', {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}),
            ('Still not a json', {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}),
        ]

        enrichment = enrich_job(self.job, force=True)
        self.assertEqual(enrichment.status, JobEnrichment.Status.VALIDATION_ERROR)
        self.assertEqual(enrichment.status_reason, EnrichmentReason.INVALID_JSON_RETRY_FAILED)
        self.assertEqual(mock_chat.call_count, 2)

    @override_settings(OPENROUTER_CIRCUIT_BREAKER_ENABLED=True, OPENROUTER_CIRCUIT_BREAKER_FAILURE_THRESHOLD=1)
    @patch("apps.llm.services.job_enrichment.OpenRouterClient.chat")
    def test_invalid_json_does_not_open_circuit(self, mock_chat):
        mock_chat.side_effect = [
            ('Not a json', {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}),
            ('Still not a json', {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}),
        ]

        enrichment = enrich_job(self.job, force=True)
        self.assertEqual(enrichment.status, JobEnrichment.Status.VALIDATION_ERROR)
        
        status = get_openrouter_circuit_status()
        self.assertFalse(status["is_open"])

    @override_settings(OPENROUTER_CIRCUIT_BREAKER_ENABLED=True, OPENROUTER_CIRCUIT_BREAKER_FAILURE_THRESHOLD=1)
    @patch("apps.llm.services.job_enrichment.OpenRouterClient.chat")
    def test_provider_outage_opens_circuit(self, mock_chat):
        import urllib.error
        err = urllib.error.HTTPError("url", 429, "Too Many Requests", {}, None)
        mock_chat.side_effect = err
        
        enrichment = enrich_job(self.job, force=True)
        self.assertEqual(enrichment.status, JobEnrichment.Status.FAILED)
        self.assertEqual(enrichment.status_reason, EnrichmentReason.RATE_LIMITED)
        
        status = get_openrouter_circuit_status()
        self.assertTrue(status["is_open"])

    @patch("apps.llm.services.job_enrichment.OpenRouterClient.chat")
    def test_skipped_reason_consistency(self, mock_chat):
        # Job that shouldn't be enriched
        self.job.status = JobStatus.EXPIRED
        self.job.save()
        
        enrichment = enrich_job(self.job)
        self.assertEqual(enrichment.status, JobEnrichment.Status.SKIPPED)
        self.assertEqual(enrichment.total_tokens, 0)
        self.assertEqual(mock_chat.call_count, 0)

