from django.test import TestCase
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.utils import timezone
from django.contrib.postgres.indexes import GinIndex
from apps.jobs.models import (
    JobSource,
    SourceType,
    RawJobRecord,
    NormalizedJob,
    NormalizedJobSkill,
    RemoteType,
    JobType,
    ExperienceLevel,
    RequirementType,
    SkillSource,
)
from apps.jobs.services.helpers import compute_payload_hash
from apps.skills.models import Skill, SkillCategory


class JobModelsTest(TestCase):
    def setUp(self):
        self.source = JobSource.objects.create(
            name="Test Source", slug="test_source", source_type=SourceType.FIXTURE
        )

    def test_job_source_unique_slug(self):
        with self.assertRaises(IntegrityError):
            JobSource.objects.create(name="Another Source", slug="test_source", source_type=SourceType.API)

    def test_raw_job_record_unique_constraint(self):
        now = timezone.now()
        RawJobRecord.objects.create(
            source=self.source,
            source_job_id="123",
            raw_payload_json={"id": "123"},
            payload_hash="hash1",
            first_seen_at=now,
            last_seen_at=now,
            last_fetched_at=now,
        )

        with self.assertRaises(IntegrityError):
            RawJobRecord.objects.create(
                source=self.source,
                source_job_id="123",
                raw_payload_json={"id": "123"},
                payload_hash="hash2",
                first_seen_at=now,
                last_seen_at=now,
                last_fetched_at=now,
            )

    def test_normalized_job_public_id(self):
        now = timezone.now()
        raw = RawJobRecord.objects.create(
            source=self.source,
            source_job_id="123",
            raw_payload_json={},
            payload_hash="hash",
            first_seen_at=now,
            last_seen_at=now,
            last_fetched_at=now,
        )

        job1 = NormalizedJob.objects.create(
            source=self.source,
            raw_record=raw,
            source_job_id="123",
            title="Dev",
            remote_type=RemoteType.REMOTE,
            job_type=JobType.FULL_TIME_JOB,
            experience_level=ExperienceLevel.JUNIOR,
            first_seen_at=now,
            last_seen_at=now,
            last_fetched_at=now,
        )

        self.assertIsNotNone(job1.public_id)

    def test_normalized_job_has_search_vector_gin_index(self):
        gin_indexes = [
            index for index in NormalizedJob._meta.indexes
            if isinstance(index, GinIndex) and index.name == "jobs_normal_search_vector_gin"
        ]
        self.assertEqual(len(gin_indexes), 1)

    def test_normalized_job_skill_unique_and_protects_skill(self):
        now = timezone.now()
        raw = RawJobRecord.objects.create(
            source=self.source,
            source_job_id="skill-protect",
            raw_payload_json={},
            payload_hash="hash",
            first_seen_at=now,
            last_seen_at=now,
            last_fetched_at=now,
        )
        job = NormalizedJob.objects.create(
            source=self.source,
            raw_record=raw,
            source_job_id="skill-protect",
            title="Dev",
            remote_type=RemoteType.REMOTE,
            job_type=JobType.FULL_TIME_JOB,
            experience_level=ExperienceLevel.JUNIOR,
            first_seen_at=now,
            last_seen_at=now,
            last_fetched_at=now,
        )
        skill = Skill.objects.create(
            canonical_name="Python",
            slug="python-job-model",
            category=SkillCategory.PROGRAMMING_LANGUAGE,
            is_active=True,
        )

        NormalizedJobSkill.objects.create(
            job=job,
            skill=skill,
            requirement_type=RequirementType.REQUIRED,
            source=SkillSource.RULE,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                NormalizedJobSkill.objects.create(
                    job=job,
                    skill=skill,
                    requirement_type=RequirementType.REQUIRED,
                    source=SkillSource.RULE,
                )

        with self.assertRaises(ProtectedError):
            skill.delete()

    def test_deterministic_hashing(self):
        payload1 = {"b": 2, "a": 1}
        payload2 = {"a": 1, "b": 2}
        payload3 = {"a": 1, "b": 3}

        hash1 = compute_payload_hash(payload1)
        hash2 = compute_payload_hash(payload2)
        hash3 = compute_payload_hash(payload3)

        self.assertEqual(hash1, hash2)
        self.assertNotEqual(hash1, hash3)
        self.assertEqual(len(hash1), 64)
