from django.test import TestCase
from django.utils import timezone
from apps.jobs.models import (
    JobSource, RawJobRecord, NormalizedJob, NormalizedJobSkill, 
    RequirementType, SkillSource, JobStatus
)
from apps.jobs.services.presentation import JobPresentationService
from apps.jobs.templatetags.job_presentation import is_valid_badge
from apps.jobs.admin import NoSkillsFilter, NormalizedJobAdmin
from django.contrib.admin.sites import AdminSite
from unittest.mock import patch
from io import StringIO
from django.core.management import call_command
from django.urls import reverse
import json

class PresentationBadgeTest(TestCase):
    def test_is_valid_badge(self):
        self.assertFalse(is_valid_badge(""))
        self.assertFalse(is_valid_badge("   "))
        self.assertFalse(is_valid_badge(None))
        self.assertFalse(is_valid_badge("unknown"))
        self.assertFalse(is_valid_badge("UNKNOWN"))
        self.assertFalse(is_valid_badge("n/a"))
        self.assertFalse(is_valid_badge("null"))
        self.assertFalse(is_valid_badge("none"))
        self.assertFalse(is_valid_badge("-"))
        self.assertFalse(is_valid_badge("t"))
        self.assertTrue(is_valid_badge("Junior"))
        self.assertTrue(is_valid_badge("C"))
        self.assertTrue(is_valid_badge("100% Télétravail"))

class AdminSkillReviewTest(TestCase):
    def setUp(self):
        self.source = JobSource.objects.create(name="Test Source", slug="test-source", source_type="api")
        self.raw = RawJobRecord.objects.create(
            source=self.source, source_job_id="123", raw_payload_json={}, payload_hash="abc",
            first_seen_at=timezone.now(), last_seen_at=timezone.now(), last_fetched_at=timezone.now()
        )
        self.job1 = NormalizedJob.objects.create(
            source=self.source, raw_record=self.raw, source_job_id="123", title="No Skills Job",
            first_seen_at=timezone.now(), last_seen_at=timezone.now(), last_fetched_at=timezone.now(),
            status=JobStatus.ACTIVE
        )
        self.raw2 = RawJobRecord.objects.create(
            source=self.source, source_job_id="456", raw_payload_json={}, payload_hash="def",
            first_seen_at=timezone.now(), last_seen_at=timezone.now(), last_fetched_at=timezone.now()
        )
        self.job2 = NormalizedJob.objects.create(
            source=self.source, raw_record=self.raw2, source_job_id="456", title="Has Skills Job",
            first_seen_at=timezone.now(), last_seen_at=timezone.now(), last_fetched_at=timezone.now(),
            status=JobStatus.ACTIVE
        )
        
        from apps.skills.models import Skill
        self.skill = Skill.objects.create(canonical_name="Python", slug="python")
        NormalizedJobSkill.objects.create(
            job=self.job2, skill=self.skill, requirement_type=RequirementType.REQUIRED.value,
            source=SkillSource.RULE.value
        )
        
        self.site = AdminSite()

    def test_no_skills_filter(self):
        class DummyRequest:
            pass

        admin_model = NormalizedJobAdmin(NormalizedJob, self.site)
        filter_no = NoSkillsFilter(DummyRequest(), {'has_skills': 'no'}, NormalizedJob, admin_model)
        with patch.object(filter_no, 'value', return_value='no'):
            qs_no = filter_no.queryset(DummyRequest(), NormalizedJob.objects.all())
            self.assertEqual(qs_no.count(), 1)
            self.assertEqual(qs_no.first().id, self.job1.id)

        filter_yes = NoSkillsFilter(DummyRequest(), {'has_skills': 'yes'}, NormalizedJob, admin_model)
        with patch.object(filter_yes, 'value', return_value='yes'):
            qs_yes = filter_yes.queryset(DummyRequest(), NormalizedJob.objects.all())
            self.assertEqual(qs_yes.count(), 1)
            self.assertEqual(qs_yes.first().id, self.job2.id)

    def test_admin_queryset_exposes_review_columns(self):
        class DummyRequest:
            pass

        admin_model = NormalizedJobAdmin(NormalizedJob, self.site)
        job = admin_model.get_queryset(DummyRequest()).get(id=self.job2.id)

        self.assertEqual(admin_model.job_skill_count(job), 1)
        self.assertEqual(admin_model.enrichment_status(job), "-")

    def test_manual_admin_normalized_job_skill_creation_uses_canonical_skill(self):
        skill = self.skill
        row = NormalizedJobSkill.objects.create(
            job=self.job1,
            skill=skill,
            requirement_type=RequirementType.REQUIRED.value,
            source=SkillSource.ADMIN.value,
            confidence="1.000",
        )

        self.assertEqual(row.skill.canonical_name, "Python")
        self.assertEqual(row.source, SkillSource.ADMIN.value)
        self.assertEqual(self.job1.job_skills.count(), 1)

    @patch('apps.jobs.services.skill_extraction.JobSkillExtractionService.extract_for_job')
    def test_re_extract_skills_action(self, mock_extract):
        from apps.jobs.services.admin_operations import JobAdminOperationsService
        JobAdminOperationsService.re_extract_skills([self.job1.id])
        mock_extract.assert_called_once()
        self.assertEqual(mock_extract.call_args[0][0].id, self.job1.id)

    @patch("apps.jobs.services.skill_materialization.JobSkillMaterializationService.materialize_for_job")
    def test_rematerialize_from_enrichment_uses_existing_successful_enrichment_only(self, mock_materialize):
        from apps.jobs.services.admin_operations import JobAdminOperationsService
        from apps.llm.models import JobEnrichment

        JobEnrichment.objects.create(
            job=self.job1,
            status=JobEnrichment.Status.SUCCESS,
            payload_hash="hash-job-1",
            validated_output_json={"required_skills": [{"name": "Python"}], "optional_skills": []},
        )

        count = JobAdminOperationsService.rematerialize_from_enrichment([self.job1.id, self.job2.id])

        self.assertEqual(count, 1)
        mock_materialize.assert_called_once()
        self.assertEqual(mock_materialize.call_args.kwargs["job"].id, self.job1.id)
        self.assertEqual(mock_materialize.call_args.kwargs["source"], "llm")

class ExportCommandTest(TestCase):
    def setUp(self):
        self.source = JobSource.objects.create(name="Test Source", slug="test-source", source_type="api")
        self.raw = RawJobRecord.objects.create(
            source=self.source, source_job_id="123", raw_payload_json={}, payload_hash="abc",
            first_seen_at=timezone.now(), last_seen_at=timezone.now(), last_fetched_at=timezone.now()
        )
        self.job1 = NormalizedJob.objects.create(
            source=self.source, raw_record=self.raw, source_job_id="123", title="No Skills Job",
            first_seen_at=timezone.now(), last_seen_at=timezone.now(), last_fetched_at=timezone.now(),
            status=JobStatus.ACTIVE, description="Long description " * 50,
            skill_signal_quality="strong",
        )
        from apps.llm.models import JobEnrichment

        JobEnrichment.objects.create(
            job=self.job1,
            status=JobEnrichment.Status.SUCCESS,
            payload_hash="hash-job-1",
            validated_output_json={
                "required_skills": [{"name": "Python"}],
                "optional_skills": [{"name": "Django"}, {"name": "PostgreSQL"}],
            },
        )
    
    def test_export_command_jsonl(self):
        out = StringIO()
        call_command('export_jobs_needing_skill_review', format='jsonl', stdout=out)
        
        with open('var/review/jobs_needing_skill_review.jsonl', 'r', encoding='utf-8') as f:
            lines = f.readlines()
            self.assertEqual(len(lines), 1)
            record = json.loads(lines[0])
            self.assertEqual(record['title'], "No Skills Job")
            self.assertEqual(record['job_skill_count'], 0)
            self.assertEqual(record["source"], "test-source")
            self.assertEqual(record["source_external_id"], "123")
            self.assertEqual(record["enrichment_status"], "success")
            self.assertEqual(record["enrichment_required_count"], 1)
            self.assertEqual(record["enrichment_optional_count"], 2)
            self.assertEqual(record["job_path"], reverse("jobs:detail", args=[self.job1.public_id]))
            self.assertTrue(len(record['description_excerpt']) <= 300)

    def test_export_command_csv(self):
        out = StringIO()
        call_command('export_jobs_needing_skill_review', format='csv', stdout=out)
        
        with open('var/review/jobs_needing_skill_review.csv', 'r', encoding='utf-8') as f:
            lines = f.readlines()
            self.assertEqual(len(lines), 2) # header + 1 row
            self.assertIn("enrichment_status", lines[0])
            self.assertIn("job_path", lines[0])
            self.assertIn("No Skills Job", lines[1])
