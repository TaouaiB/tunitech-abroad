import os
import json
import tempfile
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from apps.jobs.models import (
    JobSource,
    SourceType,
    RawJobRecord,
    NormalizedJob,
    NormalizedJobSkill,
    RemoteType,
    JobType,
    ExperienceLevel,
    JobStatus,
    NormalizationStatus,
    RequirementType,
)
from apps.jobs.services.source_seed import seed_job_sources
from apps.jobs.services.fixture_ingestion import JobFixtureIngestionService
from apps.jobs.services.classification import JobClassificationService
from apps.jobs.services.normalization import JobNormalizationService
from apps.jobs.services.skill_extraction import JobSkillExtractionService
from apps.jobs.services.freshness import JobFreshnessService
from apps.skills.models import Skill, SkillCategory, SkillAlias
from apps.skills.models import UnmatchedSkillCandidate


class JobServicesTest(TestCase):
    def setUp(self):
        seed_job_sources()
        self.source = JobSource.objects.get(slug="france_travail")
        
        self.skill_python = Skill.objects.create(canonical_name="Python", category=SkillCategory.PROGRAMMING_LANGUAGE, is_active=True)
        SkillAlias.objects.create(skill=self.skill_python, normalized_alias="python")

    def test_source_seeding_idempotency(self):
        count = JobSource.objects.count()
        seed_job_sources()
        self.assertEqual(JobSource.objects.count(), count)

    def test_fixture_ingestion(self):
        fixture_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "fixtures",
            "france_travail_sample_jobs.json"
        )
        
        run1 = JobFixtureIngestionService.load_fixture_file(fixture_path)
        self.assertEqual(run1.status, "success")
        self.assertTrue(run1.created_count > 0)
        self.assertEqual(run1.updated_count, 0)
        self.assertEqual(run1.unchanged_count, 0)

        run2 = JobFixtureIngestionService.load_fixture_file(fixture_path)
        self.assertEqual(run2.status, "success")
        self.assertEqual(run2.created_count, 0)
        self.assertEqual(run2.updated_count, 0)
        self.assertTrue(run2.unchanged_count > 0)

    def test_fixture_ingestion_updates_changed_payload(self):
        first_payload = [{"id": "changed-1", "intitule": "Dev Python", "description": "Django"}]
        second_payload = [{"id": "changed-1", "intitule": "Dev Python", "description": "Django et PostgreSQL"}]

        with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8") as fixture:
            json.dump(first_payload, fixture)
            fixture.flush()
            run1 = JobFixtureIngestionService.load_fixture_file(fixture.name)

            raw = RawJobRecord.objects.get(source=self.source, source_job_id="changed-1")
            first_hash = raw.payload_hash

            fixture.seek(0)
            fixture.truncate()
            json.dump(second_payload, fixture)
            fixture.flush()
            run2 = JobFixtureIngestionService.load_fixture_file(fixture.name)

        raw.refresh_from_db()
        self.assertEqual(run1.created_count, 1)
        self.assertEqual(run2.updated_count, 1)
        self.assertNotEqual(raw.payload_hash, first_hash)
        self.assertEqual(raw.normalization_status, NormalizationStatus.PENDING.value)

    def test_classification_service(self):
        payload = {"typeContrat": "SAI"}
        res = JobClassificationService.classify(payload, "Stage développeur", "Stage")
        self.assertEqual(res["job_type"], JobType.INTERNSHIP.value)

        payload = {"typeContrat": "CDI"}
        res = JobClassificationService.classify(payload, "Remote developer", "Developer")
        self.assertEqual(res["remote_type"], RemoteType.REMOTE.value)

        res = JobClassificationService.classify({"typeContrat": "APP"}, "Alternance développeur hybride", "Apprenti")
        self.assertEqual(res["job_type"], JobType.APPRENTICESHIP.value)
        self.assertEqual(res["remote_type"], RemoteType.HYBRID.value)

        res = JobClassificationService.classify(
            {"typeContrat": "CDD", "langues": [{"libelle": "Anglais", "exigence": "E"}]},
            "Mission sur site, français courant",
            "Développeur",
        )
        self.assertEqual(res["job_type"], JobType.CONTRACT.value)
        self.assertEqual(res["remote_type"], RemoteType.ON_SITE.value)
        self.assertEqual(res["language_requirements"]["english"], RequirementType.REQUIRED.value)
        self.assertEqual(res["language_requirements"]["french"], RequirementType.REQUIRED.value)

    def test_normalization_service(self):
        now = timezone.now()
        raw = RawJobRecord.objects.create(
            source=self.source,
            source_job_id="123",
            raw_payload_json={"intitule": "Dev Python", "description": "Django dev"},
            payload_hash="hash",
            first_seen_at=now,
            last_seen_at=now,
            last_fetched_at=now,
        )

        job = JobNormalizationService.normalize(raw)
        self.assertIsNotNone(job)
        assert job is not None
        self.assertEqual(job.title, "Dev Python")
        raw.refresh_from_db()
        self.assertEqual(raw.normalization_status, NormalizationStatus.SUCCESS.value)
        self.assertIsNotNone(job.search_vector)

        raw.raw_payload_json["description"] = "Django dev updated"
        raw.save(update_fields=["raw_payload_json"])
        same_job = JobNormalizationService.normalize(raw)
        self.assertIsNotNone(same_job)
        assert same_job is not None
        self.assertEqual(same_job.id, job.id)
        self.assertEqual(NormalizedJob.objects.filter(source=self.source, source_job_id="123").count(), 1)

    def test_renormalization_updates_existing_skill_json_fields(self):
        now = timezone.now()
        raw = RawJobRecord.objects.create(
            source=self.source,
            source_job_id="skill-json-refresh",
            raw_payload_json={
                "intitule": "Développeur backend",
                "description": "Stack backend.",
                "competences": [
                    {"libelle": "Python", "exigence": "E"},
                    {"libelle": "Docker", "exigence": "S"},
                    "invalid",
                    {"libelle": 123, "exigence": "E"},
                ],
            },
            payload_hash="hash",
            first_seen_at=now,
            last_seen_at=now,
            last_fetched_at=now,
        )

        job = JobNormalizationService.normalize(raw)
        self.assertIsNotNone(job)
        assert job is not None
        self.assertEqual(NormalizedJob.objects.filter(source=self.source, source_job_id="skill-json-refresh").count(), 1)
        self.assertEqual(job.required_skills_json, ["Python"])
        self.assertEqual(job.optional_skills_json, ["Docker"])

        raw.raw_payload_json = {
            "intitule": "Développeur backend",
            "description": "Stack backend mise à jour.",
            "competences": [
                {"libelle": "Django", "exigence": "E"},
                {"libelle": "PostgreSQL", "exigence": "S"},
            ],
        }
        raw.save(update_fields=["raw_payload_json"])

        same_job = JobNormalizationService.normalize(raw)
        self.assertIsNotNone(same_job)
        assert same_job is not None
        self.assertEqual(same_job.id, job.id)
        self.assertEqual(same_job.required_skills_json, ["Django"])
        self.assertNotIn("Python", same_job.required_skills_json)
        self.assertEqual(same_job.optional_skills_json, ["PostgreSQL"])
        self.assertNotIn("Docker", same_job.optional_skills_json)
        self.assertEqual(NormalizedJob.objects.filter(source=self.source, source_job_id="skill-json-refresh").count(), 1)

    def test_normalization_failure_stores_error(self):
        now = timezone.now()
        raw = RawJobRecord.objects.create(
            source=self.source,
            source_job_id="missing-title",
            raw_payload_json={"description": "No title"},
            payload_hash="hash",
            first_seen_at=now,
            last_seen_at=now,
            last_fetched_at=now,
        )

        job = JobNormalizationService.normalize(raw)

        self.assertIsNone(job)
        raw.refresh_from_db()
        self.assertEqual(raw.normalization_status, NormalizationStatus.FAILED.value)
        self.assertIn("Missing title", raw.normalization_error)

    def test_skill_extraction_service(self):
        now = timezone.now()
        raw = RawJobRecord.objects.create(
            source=self.source,
            source_job_id="test_skill",
            raw_payload_json={"intitule": "Dev Python"},
            payload_hash="hash",
            first_seen_at=now,
            last_seen_at=now,
            last_fetched_at=now,
        )
        job = JobNormalizationService.normalize(raw)
        self.assertIsNotNone(job)
        assert job is not None
        job.required_skills_json = ["Python"]
        job.optional_skills_json = ["TunitechScript"]
        job.save(update_fields=["required_skills_json", "optional_skills_json"])

        result = JobSkillExtractionService.extract_for_job(job)
        job.refresh_from_db()
        
        self.assertIn(self.skill_python, result.canonical_skills)
        self.assertEqual(job.required_skills_json, ["Python"])
        self.assertEqual(job.optional_skills_json, [])
        self.assertEqual(job.skill_extraction_status, "success")
        job_skills = NormalizedJobSkill.objects.filter(job=job)
        self.assertTrue(job_skills.exists())

        JobSkillExtractionService.extract_for_job(job)
        self.assertEqual(NormalizedJobSkill.objects.filter(job=job, skill=self.skill_python).count(), 1)

    def test_skill_extraction_records_unknown_candidates(self):
        now = timezone.now()
        raw = RawJobRecord.objects.create(
            source=self.source,
            source_job_id="unknown_skill",
            raw_payload_json={
                "intitule": "Dev Python",
                "competences": [{"libelle": "TunitechScript", "exigence": "E"}],
            },
            payload_hash="hash",
            first_seen_at=now,
            last_seen_at=now,
            last_fetched_at=now,
        )
        job = JobNormalizationService.normalize(raw)
        self.assertIsNotNone(job)
        assert job is not None
        JobSkillExtractionService.extract_for_job(job)

        self.assertTrue(
            UnmatchedSkillCandidate.objects.filter(
                normalized_text="tunitechscript",
                source_type="job",
            ).exists()
        )

    def test_freshness_service(self):
        now = timezone.now()
        raw = RawJobRecord.objects.create(
            source=self.source,
            source_job_id="fresh1",
            raw_payload_json={"intitule": "Dev Python"},
            payload_hash="hash",
            first_seen_at=now,
            last_seen_at=now,
            last_fetched_at=now,
        )
        job = JobNormalizationService.normalize(raw)
        self.assertIsNotNone(job)
        assert job is not None

        # Active
        JobFreshnessService.mark_stale_and_expired(now=now)
        job.refresh_from_db()
        self.assertEqual(job.status, JobStatus.ACTIVE.value)

        # Stale
        job.last_seen_at = now - timedelta(hours=25)
        job.save()
        JobFreshnessService.mark_stale_and_expired(now=now)
        job.refresh_from_db()
        self.assertEqual(job.status, JobStatus.STALE.value)

        # Removed
        job.last_seen_at = now - timedelta(hours=73)
        job.save()
        JobFreshnessService.mark_stale_and_expired(now=now)
        job.refresh_from_db()
        self.assertEqual(job.status, JobStatus.REMOVED.value)

        # Expired
        job.expires_at = now - timedelta(hours=1)
        job.save()
        JobFreshnessService.mark_stale_and_expired(now=now)
        job.refresh_from_db()
        self.assertEqual(job.status, JobStatus.EXPIRED.value)
