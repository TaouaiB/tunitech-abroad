import uuid
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from apps.jobs.models import (
    ExperienceLevel,
    JobSource,
    JobStatus,
    JobType,
    NormalizationStatus,
    NormalizedJob,
    RawJobRecord,
    RemoteType,
    SourceType,
)


class RecomputeJobSkillSignalsCommandTest(TestCase):
    def setUp(self):
        self.source = JobSource.objects.create(
            name="France Travail",
            slug="france_travail",
            source_type=SourceType.API,
            is_active=True,
        )

    def _job(self, title, description, *, competences=None, country="FR"):
        now = timezone.now()
        raw = RawJobRecord.objects.create(
            source=self.source,
            source_job_id=f"SIG-{uuid.uuid4().hex[:8]}",
            raw_payload_json={
                "intitule": title,
                "description": description,
                "competences": competences or [],
            },
            payload_hash=f"hash-{uuid.uuid4().hex[:8]}",
            first_seen_at=now,
            last_seen_at=now,
            last_fetched_at=now,
            normalization_status=NormalizationStatus.SUCCESS,
        )
        return NormalizedJob.objects.create(
            source=self.source,
            raw_record=raw,
            source_job_id=raw.source_job_id,
            title=title,
            description=description,
            remote_type=RemoteType.UNKNOWN,
            job_type=JobType.FULL_TIME_JOB,
            experience_level=ExperienceLevel.JUNIOR,
            country=country,
            status=JobStatus.ACTIVE,
            classification_json={"family": "unknown", "is_it": True, "confidence": "unknown"},
            skill_signal_quality="unknown",
            first_seen_at=now,
            last_seen_at=now,
            last_fetched_at=now,
        )

    def test_dry_run_reports_obvious_it_jobs_without_writing(self):
        job = self._job(
            "Développeur Python Django",
            "Développement backend API avec PostgreSQL et Linux.",
        )

        out = StringIO()
        call_command("recompute_job_skill_signals", "--limit", "100", "--dry-run", stdout=out)

        job.refresh_from_db()
        self.assertEqual(job.skill_signal_quality, "unknown")
        self.assertIn("changed_to_partial: 1", out.getvalue())
        self.assertIn("[DRY-RUN] no changes written", out.getvalue())

    def test_recompute_changes_obvious_required_skill_to_strong(self):
        job = self._job(
            "Ingénieur logiciel Java",
            "Conception et maintenance applicative.",
            competences=[{"libelle": "Java", "exigence": "E"}],
        )

        out = StringIO()
        call_command("recompute_job_skill_signals", "--limit", "100", stdout=out)

        job.refresh_from_db()
        self.assertEqual(job.skill_signal_quality, "strong")
        self.assertEqual(job.classification_json["confidence"], "high")
        self.assertIn("changed_to_strong: 1", out.getvalue())

    def test_recompute_keeps_non_it_excluded(self):
        job = self._job(
            "Vendeur en magasin",
            "Accueil client et encaissement.",
        )

        call_command("recompute_job_skill_signals", "--limit", "100", stdout=StringIO())

        job.refresh_from_db()
        self.assertEqual(job.skill_signal_quality, "excluded_non_it")
        self.assertEqual(job.classification_json["family"], "non_it")
