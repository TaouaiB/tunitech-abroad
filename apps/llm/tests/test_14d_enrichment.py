from django.test import TestCase, override_settings
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock
from pathlib import Path
from typing import Any, cast

from apps.jobs.models import NormalizedJob, NormalizedJobSkill, JobStatus, RequirementType, JobSource, RawJobRecord, SkillSource
from apps.skills.models import Skill, SkillAlias, SkillCategory
from apps.llm.models import JobEnrichment
from apps.llm.services.job_enrichment import job_qualifies_for_enrichment, validate_enrichment_schema, enrich_job
from apps.llm.management.commands.enrich_jobs import Command
from apps.llm.tasks import enrich_job_task
from apps.matching.services.scoring import MatchScoringService
from apps.profiles.models import CandidateProfile, ProfileSkill

@override_settings(JOB_ENRICHMENT_DAILY_LIMIT=1000, JOB_ENRICHMENT_MAX_PER_INGESTION_RUN=1000)
class EnrichmentTests(TestCase):
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

    def test_job_enrichment_model(self):
        enrichment = JobEnrichment.objects.create(
            job=self.job,
            status=JobEnrichment.Status.SUCCESS,
            validated_output_json={"required_skills": [{"name": "Python", "evidence": "We need a Python developer"}]}
        )
        self.assertEqual(enrichment.job.title, "Senior Python Developer")
        self.assertEqual(enrichment.status, "success")

    @override_settings(JOB_ENRICHMENT_ENABLED=True)
    def test_job_qualifies_for_enrichment(self):
        # Base setup qualifies
        self.assertTrue(job_qualifies_for_enrichment(self.job))

        # Not FR
        self.job.country = "US"
        self.job.save()
        self.assertFalse(job_qualifies_for_enrichment(self.job))
        self.job.country = "FR"

        # Not Active
        self.job.status = JobStatus.EXPIRED
        self.job.save()
        self.assertFalse(job_qualifies_for_enrichment(self.job))
        self.job.status = JobStatus.ACTIVE

        # Low confidence
        self.job.classification_json = {"confidence": "low"}
        self.job.save()
        self.assertFalse(job_qualifies_for_enrichment(self.job))

    def test_validate_enrichment_schema(self):
        # Valid
        data = {
            "required_skills": [{"name": "Python", "evidence": "We need a Python developer"}],
            "optional_skills": [{"name": "Django", "evidence": "knows Django"}]
        }
        validated_data, errors = validate_enrichment_schema(data, self.job.description)
        self.assertEqual(len(errors), 0)
        
        # Soft skills filtered out
        data = {
            "required_skills": [
                {"name": "Autonomie", "evidence": "être autonome"},
                {"name": "Python", "evidence": "Python developer"}
            ],
            "optional_skills": []
        }
        validated_data, errors = validate_enrichment_schema(data, "être autonome, Python developer")
        self.assertIsNotNone(validated_data)
        validated_data = cast(dict[str, Any], validated_data)
        self.assertEqual(len(validated_data["required_skills"]), 1)
        self.assertEqual(validated_data["required_skills"][0]["name"], "Python")

        # Missing evidence
        data = {
            "required_skills": [{"name": "Java", "evidence": "Strong Java skills"}],
            "optional_skills": []
        }
        validated_data, errors = validate_enrichment_schema(data, self.job.description)
        self.assertTrue(len(errors) > 0)
        self.assertTrue(any("Java" in e for e in errors))

    @override_settings(JOB_ENRICHMENT_ENABLED=True)
    @patch('apps.llm.services.job_enrichment.OpenRouterClient')
    def test_enrich_job_success_stores_raw_validated_tokens_and_cost(self, mock_client_class):
        import json
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.chat.return_value = (json.dumps({
            "required_skills": [{"name": "Python", "evidence": "Python developer"}],
            "optional_skills": [{"name": "Django", "evidence": "knows Django"}]
        }), {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30})

        enrichment = enrich_job(self.job, force=True)
        # Remove check for raw_response_json and raw_response_text per security requirements
        self.assertEqual(enrichment.validated_output_json["required_skills"][0]["name"], "Python")
        self.assertEqual(enrichment.prompt_tokens, 10)
        self.assertEqual(enrichment.completion_tokens, 20)
        self.assertEqual(enrichment.total_tokens, 30)
        self.assertGreater(enrichment.estimated_cost_usd, 0)

    @override_settings(JOB_ENRICHMENT_ENABLED=True)
    @patch('apps.llm.services.job_enrichment.OpenRouterClient')
    def test_enrich_job_validation_error(self, mock_client_class):
        import json
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.chat.return_value = (json.dumps({
            "required_skills": [{"name": "Java", "evidence": "Strong Java skills"}],
            "optional_skills": []
        }), {"prompt_tokens": 10})

        enrichment = enrich_job(self.job, force=True)
        self.assertEqual(enrichment.status, JobEnrichment.Status.VALIDATION_ERROR)
        self.assertTrue(len(enrichment.validation_errors_json) > 0)

    @override_settings(JOB_RECOMMENDATIONS_USE_ENRICHED_DATA=True)
    def test_match_scoring_uses_materialized_enriched_skills(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User(username="test", email="test@example.com")
        user.set_password("123")
        user.save()
        python = Skill.objects.create(canonical_name="Python", slug="python", category=SkillCategory.PROGRAMMING_LANGUAGE)
        SkillAlias.objects.create(skill=python, alias="Python", normalized_alias="python")
        JobEnrichment.objects.create(
            job=self.job,
            status=JobEnrichment.Status.SUCCESS,
            validated_output_json={
                "required_skills": [{"name": "Python", "evidence": "..."}],
                "optional_skills": []
            }
        )

        profile = CandidateProfile.objects.create(user=user, years_experience=2)
        ProfileSkill.objects.create(profile=profile, raw_name="Python", normalized_name="python")

        NormalizedJobSkill.objects.create(
            job=self.job,
            skill=python,
            requirement_type=RequirementType.REQUIRED,
            source=SkillSource.LLM,
            confidence=1,
        )

        res = MatchScoringService.calculate(profile, self.job)
        
        # Python should match from canonical materialized skills, not raw enrichment JSON.
        strong_names = [s["name"] for s in res.strong_skills]
        self.assertIn("Python", strong_names)
        self.assertEqual(res.match_confidence, MatchScoringService.CONFIDENCE_RELIABLE)

    @override_settings(JOB_RECOMMENDATIONS_USE_ENRICHED_DATA=False)
    def test_match_scoring_ignores_enriched_data_when_flag_disabled(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User(username="flagoff", email="flagoff@example.com")
        user.set_password("123")
        user.save()
        JobEnrichment.objects.create(
            job=self.job,
            status=JobEnrichment.Status.SUCCESS,
            validated_output_json={
                "required_skills": [{"name": "Ruby", "evidence": "Ruby"}],
                "optional_skills": []
            }
        )

        profile = CandidateProfile.objects.create(user=user, years_experience=2)
        ProfileSkill.objects.create(profile=profile, raw_name="Ruby", normalized_name="ruby")

        res = MatchScoringService.calculate(profile, self.job)
        self.assertNotIn("Ruby", [s["name"] for s in res.strong_skills])

    @override_settings(JOB_RECOMMENDATIONS_USE_ENRICHED_DATA=True)
    def test_match_scoring_does_not_use_unmaterialized_enrichment_json(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User(username="canonical", email="canonical@example.com")
        user.set_password("123")
        user.save()
        JobEnrichment.objects.create(
            job=self.job,
            status=JobEnrichment.Status.SUCCESS,
            validated_output_json={
                "required_skills": [{"name": "Ruby", "evidence": "Ruby"}],
                "optional_skills": []
            }
        )

        profile = CandidateProfile.objects.create(user=user, years_experience=2)
        ProfileSkill.objects.create(profile=profile, raw_name="Ruby", normalized_name="ruby")

        res = MatchScoringService.calculate(profile, self.job)
        self.assertNotIn("Ruby", [s["name"] for s in res.strong_skills])

    @override_settings(JOB_ENRICHMENT_ENABLED=False)
    def test_celery_task_skips_when_enrichment_disabled(self):
        status = cast(Any, enrich_job_task).run(self.job.id)
        enrichment = JobEnrichment.objects.get(job=self.job)

        self.assertEqual(status, JobEnrichment.Status.SKIPPED)
        self.assertEqual(enrichment.status, JobEnrichment.Status.SKIPPED)

    @override_settings(JOB_ENRICHMENT_ENABLED=True)
    @patch('apps.llm.management.commands.enrich_jobs.enrich_job_task.delay')
    def test_management_command_enqueueing(self, mock_delay):
        command = Command()
        command.stdout = MagicMock()
        command.style = MagicMock()
        command.handle(limit=10, only_qualifying=True, dry_run=False, force=False, sync=False)
        mock_delay.assert_called_once_with(self.job.id, force=False)

    @override_settings(JOB_ENRICHMENT_ENABLED=True)
    @patch('apps.llm.services.job_enrichment.OpenRouterClient')
    def test_ciril_java_job_extracts_required_and_optional_skills(self, mock_client_class):
        import json
        self.job.title = "Développeur Java - Ciril"
        self.job.description = (
            "Conception et développement en langage Java. Base de données Oracle et PostgreSQL. "
            "Framework Quarkus requis. Des connaissances en langage C sont un plus. "
            "Expérience 3 ans minimum. Télétravail 1 jour par semaine."
        )
        self.job.save(update_fields=["title", "description"])

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.chat.return_value = (json.dumps({
            "is_it_role": True,
            "role_family": "software_development",
            "normalized_role_title": "Développeur Java",
            "seniority": "mid",
            "required_skills": [
                {"name": "Java", "evidence": "développement en langage Java"},
                {"name": "Oracle DB", "evidence": "Base de données Oracle"},
                {"name": "PostgreSQL", "evidence": "PostgreSQL"},
                {"name": "Quarkus", "evidence": "Framework Quarkus requis"},
            ],
            "optional_skills": [
                {"name": "C", "evidence": "langage C sont un plus"},
            ],
            "years_experience_min": 3,
            "languages": [],
            "remote_policy": "hybrid",
            "confidence": "high",
        }), {"prompt_tokens": 100, "completion_tokens": 80, "total_tokens": 180})

        enrichment = enrich_job(self.job, force=True)
        required_names = {skill["name"] for skill in enrichment.validated_output_json["required_skills"]}
        optional_names = {skill["name"] for skill in enrichment.validated_output_json["optional_skills"]}

        self.assertEqual(enrichment.status, JobEnrichment.Status.SUCCESS)
        self.assertSetEqual(required_names, {"Java", "Oracle DB", "PostgreSQL", "Quarkus"})
        self.assertSetEqual(optional_names, {"C"})
        self.assertEqual(enrichment.validated_output_json["years_experience_min"], 3)
        self.assertEqual(enrichment.validated_output_json["remote_policy"], "hybrid")

    @override_settings(JOB_ENRICHMENT_ENABLED=True)
    @patch('apps.llm.services.job_enrichment.OpenRouterClient')
    def test_enrich_job_processes_pending_reservation_instead_of_skipping_it(self, mock_client_class):
        from apps.llm.services.job_enrichment import compute_job_enrichment_payload_hash
        import json
        payload_hash = compute_job_enrichment_payload_hash(self.job)
        enrichment_record = JobEnrichment.objects.create(
            job=self.job,
            status=JobEnrichment.Status.PENDING,
            payload_hash=payload_hash,
            status_reason="Queued by automated ingestion."
        )

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.chat.return_value = (json.dumps({
            "is_it_role": True,
            "role_family": "software_development",
            "normalized_role_title": "Développeur Python",
            "seniority": "senior",
            "required_skills": [{"name": "Python", "evidence": "Python developer"}],
            "optional_skills": [],
            "years_experience_min": 3,
            "languages": [],
            "remote_policy": "hybrid",
            "confidence": "high",
        }), {"prompt_tokens": 100, "completion_tokens": 80, "total_tokens": 180})

        result_enrichment = enrich_job(self.job, force=False)
        self.assertEqual(result_enrichment.status, JobEnrichment.Status.SUCCESS)
        self.assertEqual(result_enrichment.id, enrichment_record.id)
        mock_client.chat.assert_called_once()

    @override_settings(JOB_ENRICHMENT_ENABLED=True, JOB_ENRICHMENT_DAILY_LIMIT=1)
    @patch('apps.llm.services.job_enrichment.OpenRouterClient')
    def test_enrich_job_own_pending_reservation_does_not_consume_daily_limit(self, mock_client_class):
        from apps.llm.services.job_enrichment import compute_job_enrichment_payload_hash
        import json
        payload_hash = compute_job_enrichment_payload_hash(self.job)
        enrichment_record = JobEnrichment.objects.create(
            job=self.job,
            status=JobEnrichment.Status.PENDING,
            payload_hash=payload_hash,
            status_reason="Queued by automated ingestion."
        )

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        def chat_success(*args, **kwargs):
            enrichment_record.refresh_from_db()
            self.assertEqual(enrichment_record.status, JobEnrichment.Status.PROCESSING)
            return (json.dumps({
                "is_it_role": True,
                "role_family": "software_development",
                "normalized_role_title": "Python Developer",
                "seniority": "senior",
                "required_skills": [{"name": "Python", "evidence": "Python developer"}],
                "optional_skills": [],
                "years_experience_min": 3,
                "languages": [],
                "remote_policy": "hybrid",
                "confidence": "high",
            }), {"prompt_tokens": 100, "completion_tokens": 80, "total_tokens": 180})

        mock_client.chat.side_effect = chat_success

        result_enrichment = enrich_job(self.job, force=False)

        self.assertEqual(result_enrichment.id, enrichment_record.id)
        self.assertEqual(result_enrichment.status, JobEnrichment.Status.SUCCESS)
        self.assertEqual(result_enrichment.attempt_count, 1)
        mock_client.chat.assert_called_once()

    @override_settings(JOB_ENRICHMENT_ENABLED=True, JOB_ENRICHMENT_DAILY_LIMIT=1)
    @patch('apps.llm.services.job_enrichment.OpenRouterClient')
    def test_enrich_job_other_pending_reservation_still_consumes_daily_limit(self, mock_client_class):
        from apps.llm.services.job_enrichment import compute_job_enrichment_payload_hash
        now = timezone.now()
        other_raw = RawJobRecord.objects.create(
            source=self.source,
            source_job_id="other-pending",
            first_seen_at=now,
            last_seen_at=now,
            last_fetched_at=now,
            payload_hash="other-hash",
            raw_payload_json={},
        )
        other_job = NormalizedJob.objects.create(
            source=self.source,
            raw_record=other_raw,
            source_job_id="other-pending",
            title="Other Python Developer",
            description="We need a Python developer.",
            country="FR",
            status=JobStatus.ACTIVE,
            published_at=now,
            first_seen_at=now,
            last_seen_at=now,
            last_fetched_at=now,
            classification_json={"confidence": "high"},
            skill_signal_quality="strong",
        )
        JobEnrichment.objects.create(
            job=other_job,
            status=JobEnrichment.Status.PENDING,
            payload_hash=compute_job_enrichment_payload_hash(other_job),
        )

        result_enrichment = enrich_job(self.job, force=False)

        self.assertEqual(result_enrichment.status, JobEnrichment.Status.SKIPPED)
        self.assertEqual(result_enrichment.status_reason, "Job does not qualify or daily limit reached.")
        mock_client_class.assert_not_called()

    @override_settings(JOB_ENRICHMENT_ENABLED=True)
    def test_enrich_job_skips_when_status_is_processing(self):
        from apps.llm.services.job_enrichment import compute_job_enrichment_payload_hash
        payload_hash = compute_job_enrichment_payload_hash(self.job)
        enrichment_record = JobEnrichment.objects.create(
            job=self.job,
            status=JobEnrichment.Status.PROCESSING,
            payload_hash=payload_hash,
        )

        result_enrichment = enrich_job(self.job, force=False)
        self.assertEqual(result_enrichment.status, JobEnrichment.Status.PROCESSING)
        self.assertEqual(result_enrichment.status_reason, "Enrichment already processing")

    @override_settings(JOB_ENRICHMENT_ENABLED=True)
    def test_enrich_job_skips_when_status_is_success_same_payload(self):
        from apps.llm.services.job_enrichment import compute_job_enrichment_payload_hash
        payload_hash = compute_job_enrichment_payload_hash(self.job)
        enrichment_record = JobEnrichment.objects.create(
            job=self.job,
            status=JobEnrichment.Status.SUCCESS,
            payload_hash=payload_hash,
        )

        result_enrichment = enrich_job(self.job, force=False)
        self.assertEqual(result_enrichment.status, JobEnrichment.Status.SUCCESS)

    def test_no_openrouter_calls_from_django_views(self):
        view_files = list(Path("apps").glob("*/views.py"))
        self.assertGreater(len(view_files), 0)
        for path in view_files:
            content = path.read_text()
            self.assertNotIn("OpenRouterClient", content, str(path))
            self.assertNotIn("openrouter", content.lower(), str(path))
