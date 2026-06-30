import json
from decimal import Decimal
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from apps.jobs.models import (
    JobQualityFeedback,
    JobQualityIssue,
    JobSource,
    JobStatus,
    NormalizedJob,
    NormalizedJobSkill,
    RawJobRecord,
    RequirementType,
    SkillSource,
)
from apps.jobs.services.eligibility_diagnostics import JobEligibilityDiagnosticsService
from apps.jobs.services.search import JobSearchService
from apps.jobs.services.skill_extraction import JobSkillExtractionService
from apps.jobs.services.skill_materialization import JobSkillMaterializationService
from apps.skills.models import Skill, SkillAlias


class Phase16EJobSkillDataQualityTests(TestCase):
    def setUp(self):
        self.source = JobSource.objects.create(name="Test Source", slug="phase-16e", source_type="fixture")
        self.python = self._skill("Python", "python")
        self.django = self._skill("Django", "django")
        self.postgresql = self._skill("PostgreSQL", "postgresql")

    def _skill(self, canonical_name, alias):
        skill = Skill.objects.create(canonical_name=canonical_name, slug=alias, is_active=True)
        SkillAlias.objects.create(skill=skill, normalized_alias=alias)
        return skill

    def _job(self, source_job_id, **overrides):
        now = timezone.now()
        raw = RawJobRecord.objects.create(
            source=self.source,
            source_job_id=source_job_id,
            raw_payload_json={},
            payload_hash=f"hash-{source_job_id}",
            first_seen_at=now,
            last_seen_at=now,
            last_fetched_at=now,
        )
        defaults = {
            "source": self.source,
            "raw_record": raw,
            "source_job_id": source_job_id,
            "title": "Backend Developer",
            "company_name": "TuniAtlas",
            "location": "Paris",
            "description": "Build backend services with PostgreSQL.",
            "status": JobStatus.ACTIVE,
            "skill_signal_quality": "strong",
            "classification_json": {"is_it": True, "confidence": "high"},
            "first_seen_at": now,
            "last_seen_at": now,
            "last_fetched_at": now,
            "required_skills_json": [],
            "optional_skills_json": [],
        }
        defaults.update(overrides)
        return NormalizedJob.objects.create(**defaults)

    def test_rule_extraction_classifies_required_optional_and_detected_with_confidence(self):
        job = self._job(
            "classifier",
            required_skills_json=["Python"],
            optional_skills_json=["Django"],
            description="Build backend services with PostgreSQL.",
        )

        JobSkillExtractionService.extract_for_job(job)

        rows = {
            row.skill.canonical_name: row
            for row in NormalizedJobSkill.objects.filter(job=job).select_related("skill")
        }
        self.assertEqual(rows["Python"].requirement_type, RequirementType.REQUIRED)
        self.assertEqual(rows["Python"].confidence, Decimal("1.000"))
        self.assertEqual(rows["Django"].requirement_type, RequirementType.OPTIONAL)
        self.assertEqual(rows["Django"].confidence, Decimal("1.000"))
        self.assertEqual(rows["PostgreSQL"].requirement_type, RequirementType.DETECTED)
        self.assertEqual(rows["PostgreSQL"].confidence, Decimal("0.700"))

    def test_materialization_bounds_candidate_confidence_and_is_idempotent(self):
        job = self._job("confidence")

        for _ in range(2):
            result = JobSkillMaterializationService.materialize_for_job(
                job,
                source=SkillSource.SOURCE_API,
                raw_skills_dict={
                    "Python": {"type": RequirementType.REQUIRED, "confidence": "2"},
                    "Django": {"type": RequirementType.DETECTED, "confidence": "0.333"},
                },
            )
            self.assertEqual(result.status, "success")

        self.assertEqual(NormalizedJobSkill.objects.filter(job=job).count(), 2)
        self.assertEqual(
            NormalizedJobSkill.objects.get(job=job, skill=self.python).confidence,
            Decimal("1.000"),
        )
        self.assertEqual(
            NormalizedJobSkill.objects.get(job=job, skill=self.django).confidence,
            Decimal("0.333"),
        )

    def test_eligibility_diagnostics_reports_quality_buckets(self):
        zero_skill = self._job("zero", skill_signal_quality="missing")
        generic = self._job("generic", skill_signal_quality="generic_only")
        low_confidence = self._job("low-confidence", skill_signal_quality="partial")
        NormalizedJobSkill.objects.create(
            job=low_confidence,
            skill=self.python,
            requirement_type=RequirementType.DETECTED,
            source=SkillSource.RULE,
            confidence=Decimal("0.400"),
        )

        diagnostics = JobEligibilityDiagnosticsService.run()

        self.assertTrue(diagnostics["ok"])
        self.assertEqual(diagnostics["counts"]["zero_skill_jobs"], 2)
        self.assertEqual(diagnostics["counts"]["generic_skill_jobs"], 1)
        self.assertEqual(diagnostics["counts"]["low_confidence_only_jobs"], 1)
        self.assertEqual(
            diagnostics["reasons"]["quality_reasons"]["zero_skill_jobs"],
            diagnostics["counts"]["zero_skill_jobs"],
        )
        self.assertIn(str(zero_skill.public_id), {item["public_id"] for item in diagnostics["top_items"]})
        self.assertIn("exclusion_reasons", diagnostics["reasons"])

    def test_management_commands_support_dry_run_and_rebuild_search_by_skill_name(self):
        job = self._job(
            "commands",
            required_skills_json=["Python"],
            optional_skills_json=["Django"],
        )

        out = StringIO()
        call_command("rematerialize_job_skills", dry_run=True, limit=1, stdout=out)
        self.assertIn("Would rematerialize skills for 1 jobs", out.getvalue())

        call_command("rematerialize_job_skills", limit=1, batch_size=1, stdout=StringIO())
        self.assertEqual(NormalizedJobSkill.objects.filter(job=job).count(), 3)

        out = StringIO()
        call_command("rebuild_job_search_vectors", dry_run=True, limit=1, stdout=out)
        self.assertIn("Would rebuild search vectors for 1 jobs", out.getvalue())

        call_command("rebuild_job_search_vectors", limit=1, batch_size=1, stdout=StringIO())
        result = JobSearchService.search({"q": "Python", "page_size": "10"})
        self.assertIn(job, list(result.page_obj.object_list))

        out = StringIO()
        call_command("inspect_public_job_eligibility", stdout=out)
        payload = json.loads(out.getvalue())
        self.assertEqual(payload["service"], "job_eligibility_diagnostics")
        self.assertIn("public_matchable_total", payload["counts"])

    def test_job_quality_feedback_stores_owner_admin_label(self):
        user = get_user_model().objects.create_user("owner@example.com", password="test-password")
        job = self._job("quality-feedback")
        feedback = JobQualityFeedback.objects.create(
            job=job,
            reason=JobQualityIssue.WRONG_SKILLS,
            notes="Detected skills do not match the description.",
            reviewed_by=user,
        )

        self.assertEqual(feedback.reason, JobQualityIssue.WRONG_SKILLS)
        self.assertEqual(job.quality_feedback.count(), 1)
