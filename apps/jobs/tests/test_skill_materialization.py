from django.test import TestCase
from django.core.management import call_command
from django.utils import timezone
from apps.jobs.models import NormalizedJob, NormalizedJobSkill, RequirementType, SkillSource, SkillExtractionStatus, JobSource, RawJobRecord
from apps.skills.models import Skill, SkillAlias, UnmatchedSkillCandidate
from apps.llm.models import JobEnrichment
from apps.jobs.services.skill_materialization import JobSkillMaterializationService
from apps.llm.services.job_enrichment import enrich_job
from unittest.mock import patch, MagicMock

class SkillMaterializationTests(TestCase):
    def setUp(self):
        source = JobSource.objects.create(name="test_source", slug="test_source", is_active=True)
        raw_record = RawJobRecord.objects.create(
            source=source,
            source_job_id="test_1",
            raw_payload_json={},
            payload_hash="testhash",
            first_seen_at=timezone.now(),
            last_seen_at=timezone.now(),
            last_fetched_at=timezone.now(),
        )
        self.job = NormalizedJob.objects.create(
            title="Python Developer",
            description="We need a Python developer.",
            status="active",
            source=source,
            source_job_id="test_1",
            raw_record=raw_record,
            first_seen_at=timezone.now(),
            last_seen_at=timezone.now(),
            last_fetched_at=timezone.now(),
        )
        self.python_skill = Skill.objects.create(canonical_name="Python", slug="python", is_active=True)
        SkillAlias.objects.create(skill=self.python_skill, normalized_alias="python")
        SkillAlias.objects.create(skill=self.python_skill, normalized_alias="python3")
        
        self.django_skill = Skill.objects.create(canonical_name="Django", slug="django", is_active=True)
        SkillAlias.objects.create(skill=self.django_skill, normalized_alias="django")
        SkillAlias.objects.create(skill=self.django_skill, normalized_alias="django framework")

    def test_provider_raw_skills_create_normalized_job_skill(self):
        self.job.required_skills_json = ["Python", "UnknownSkill"]
        self.job.optional_skills_json = ["Django", "Python"] # Python is in both, should be required
        self.job.save()

        result = JobSkillMaterializationService.materialize_for_job(self.job, source="rule")
        
        self.assertEqual(result.status, "success")
        self.job.refresh_from_db()
        self.assertEqual(self.job.skill_extraction_status, SkillExtractionStatus.SUCCESS)

        skills = list(NormalizedJobSkill.objects.filter(job=self.job))
        self.assertEqual(len(skills), 2)
        
        python_job_skill = next(s for s in skills if s.skill == self.python_skill)
        self.assertEqual(python_job_skill.requirement_type, RequirementType.REQUIRED.value)
        self.assertEqual(python_job_skill.source, SkillSource.RULE.value)

        django_job_skill = next(s for s in skills if s.skill == self.django_skill)
        self.assertEqual(django_job_skill.requirement_type, RequirementType.OPTIONAL.value)

        # Check unknowns
        self.assertTrue(UnmatchedSkillCandidate.objects.filter(normalized_text="unknownskill").exists())
        
        # Check no duplicates
        self.assertEqual(NormalizedJobSkill.objects.filter(job=self.job, skill=self.python_skill).count(), 1)

    def test_llm_skills_create_normalized_job_skill(self):
        enrichment = JobEnrichment.objects.create(
            job=self.job,
            payload_hash="testhash",
            status=JobEnrichment.Status.SUCCESS,
            validated_output_json={
                "required_skills": [{"name": "python3", "evidence": "X"}],
                "optional_skills": [{"name": "django framework", "evidence": "Y"}, {"name": "NewLLMSkill", "evidence": "Z"}]
            }
        )

        result = JobSkillMaterializationService.materialize_for_job(self.job, source="llm", enrichment=enrichment)
        
        skills = list(NormalizedJobSkill.objects.filter(job=self.job))
        self.assertEqual(len(skills), 2)
        
        # Aliases mapped
        python_job_skill = next(s for s in skills if s.skill == self.python_skill)
        self.assertEqual(python_job_skill.requirement_type, RequirementType.REQUIRED.value)
        self.assertEqual(python_job_skill.source, SkillSource.LLM.value)

        # Check unmatched
        self.assertTrue(UnmatchedSkillCandidate.objects.filter(normalized_text="newllmskill").exists())

    def test_llm_plain_string_skills_are_supported(self):
        enrichment = JobEnrichment.objects.create(
            job=self.job,
            payload_hash="testhash",
            status=JobEnrichment.Status.SUCCESS,
            validated_output_json={
                "required_skills": ["Python"],
                "optional_skills": ["Django"],
            }
        )

        result = JobSkillMaterializationService.materialize_for_job(self.job, source="llm", enrichment=enrichment)

        self.assertEqual(result.status, "success")
        self.assertTrue(NormalizedJobSkill.objects.filter(
            job=self.job,
            skill=self.python_skill,
            requirement_type=RequirementType.REQUIRED.value,
            source=SkillSource.LLM.value,
        ).exists())
        self.assertTrue(NormalizedJobSkill.objects.filter(
            job=self.job,
            skill=self.django_skill,
            requirement_type=RequirementType.OPTIONAL.value,
            source=SkillSource.LLM.value,
        ).exists())

    def test_empty_materialization_does_not_remain_pending(self):
        result = JobSkillMaterializationService.materialize_for_job(self.job, source="rule")

        self.job.refresh_from_db()
        self.assertEqual(result.status, SkillExtractionStatus.NOT_ENOUGH_TEXT)
        self.assertEqual(self.job.skill_extraction_status, SkillExtractionStatus.NOT_ENOUGH_TEXT)

    def test_admin_rows_are_preserved(self):
        # Create an ADMIN skill
        NormalizedJobSkill.objects.create(
            job=self.job,
            skill=self.django_skill,
            requirement_type=RequirementType.REQUIRED.value,
            source=SkillSource.ADMIN.value,
            confidence=1.0
        )
        
        self.job.required_skills_json = ["Python"]
        self.job.save()

        JobSkillMaterializationService.materialize_for_job(self.job, source="rule")

        skills = NormalizedJobSkill.objects.filter(job=self.job)
        self.assertEqual(skills.count(), 2)
        self.assertTrue(skills.filter(skill=self.django_skill, source=SkillSource.ADMIN.value).exists())
        self.assertTrue(skills.filter(skill=self.python_skill, source=SkillSource.RULE.value).exists())

    @patch('apps.llm.services.job_enrichment.OpenRouterClient.chat')
    @patch('apps.llm.services.job_enrichment.job_qualifies_for_enrichment', return_value=True)
    def test_successful_enrichment_triggers_materialization(self, mock_qualifies, mock_chat):
        mock_chat.return_value = (
            '{"is_it_role": true, "role_family": "software_development", "required_skills": [{"name": "Python", "evidence": "x"}], "confidence": "high"}',
            {"total_tokens": 100}
        )
        
        enrichment = enrich_job(self.job, force=True)
        self.assertEqual(enrichment.status, JobEnrichment.Status.SUCCESS)
        
        # Check if materialization was triggered
        self.job.refresh_from_db()
        self.assertEqual(self.job.skill_extraction_status, SkillExtractionStatus.SUCCESS)
        self.assertTrue(NormalizedJobSkill.objects.filter(job=self.job, skill=self.python_skill, source=SkillSource.LLM.value).exists())

    def test_backfill_command_is_idempotent(self):
        enrichment = JobEnrichment.objects.create(
            job=self.job,
            payload_hash="testhash",
            status=JobEnrichment.Status.SUCCESS,
            validated_output_json={
                "required_skills": [{"name": "Python", "evidence": "X"}],
            }
        )
        self.job.skill_extraction_status = SkillExtractionStatus.PENDING
        self.job.save()

        # First run
        call_command('materialize_job_skills', active_only=True, limit=10)
        self.job.refresh_from_db()
        self.assertEqual(self.job.skill_extraction_status, SkillExtractionStatus.SUCCESS)
        self.assertEqual(NormalizedJobSkill.objects.filter(job=self.job).count(), 1)
        
        # Change something to test idempotency (should not duplicate)
        call_command('materialize_job_skills', active_only=True, limit=10, force=True)
        self.assertEqual(NormalizedJobSkill.objects.filter(job=self.job).count(), 1)
