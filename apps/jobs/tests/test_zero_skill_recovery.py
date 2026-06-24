from django.test import TestCase
from django.utils import timezone
from django.core.management import call_command
from django.contrib.admin.sites import AdminSite
from io import StringIO
from unittest.mock import patch

from apps.jobs.admin import NormalizedJobAdmin, recover_zero_skill_jobs_action
from apps.jobs.models import NormalizedJob, JobSource, SourceType, RawJobRecord, JobType, RemoteType, ExperienceLevel, NormalizedJobSkill, RequirementType, SkillSource
from apps.jobs.services.zero_skill_recovery import ZeroSkillJobRecoveryService
from apps.skills.models import Skill
from apps.skills.services.seed import SkillSeedService

class ZeroSkillRecoveryTests(TestCase):
    def setUp(self):
        SkillSeedService.seed_initial_taxonomy()
        
        self.source = JobSource.objects.create(
            name="Test Source", slug="test-source", source_type=SourceType.MANUAL
        )

    def create_job(self, title, description, job_id="123"):
        raw_record = RawJobRecord.objects.create(
            source=self.source,
            source_job_id=job_id,
            raw_payload_json={},
            payload_hash=f"hash_{job_id}",
            first_seen_at=timezone.now(),
            last_seen_at=timezone.now(),
            last_fetched_at=timezone.now()
        )
        job = NormalizedJob.objects.create(
            source=self.source,
            raw_record=raw_record,
            source_job_id=job_id,
            title=title,
            description=description,
            job_type=JobType.FULL_TIME_JOB,
            remote_type=RemoteType.ON_SITE,
            experience_level=ExperienceLevel.JUNIOR,
            first_seen_at=timezone.now(),
            last_seen_at=timezone.now(),
            last_fetched_at=timezone.now()
        )
        return job

    def test_apprenti_technicien_informatique(self):
        job = self.create_job(
            title="Apprenti(e) Technicien Informatique", 
            description="Missions: support aux utilisateurs et maintenance matériel informatique."
        )
        result = ZeroSkillJobRecoveryService.recover_job(job)
        self.assertEqual(result['skipped_excluded'], 0)
        self.assertGreater(result['skills_created'], 0)
        self.assertEqual(result['recovered_jobs'], 1)
        self.assertTrue(NormalizedJobSkill.objects.filter(job=job).exists())

    def test_apprenti_infrastructure(self):
        job = self.create_job(
            title="Apprenti / Apprentie infrastructure et sécurité informatique", 
            description="Administration systèmes et réseaux et sécurité informatique."
        )
        result = ZeroSkillJobRecoveryService.recover_job(job)
        self.assertGreater(result['skills_created'], 0)

    def test_alternant_en_informatique(self):
        job = self.create_job(
            title="ALTERNANT EN INFORMATIQUE", 
            description="installation/configuration des équipements et dépannage."
        )
        result = ZeroSkillJobRecoveryService.recover_job(job)
        self.assertGreater(result['skills_created'], 0)

    def test_excluded_roles(self):
        job1 = self.create_job(
            title="SDR/BDR - Business Developer - Cybersécurité", 
            description="Vente de solutions de sécurité informatique.",
            job_id="ex1"
        )
        job2 = self.create_job(
            title="Médiateur scientifique cybersécurité", 
            description="Sensibilisation sécurité informatique.",
            job_id="ex2"
        )
        job3 = self.create_job(
            title="Consultant transformation digitale", 
            description="Accompagnement développement web.",
            job_id="ex3"
        )
        for job in [job1, job2, job3]:
            result = ZeroSkillJobRecoveryService.recover_job(job)
            self.assertEqual(result['skipped_excluded'], 1, f"Failed exclusion for {job.title}")
            self.assertEqual(result['skills_created'], 0)

    def test_classified_non_it_job_is_excluded_even_with_technical_words(self):
        job = self.create_job(
            title="Consultant transformation digitale",
            description="Accompagnement des équipes sur le développement web et la cybersécurité.",
            job_id="classified-non-it",
        )
        job.classification_json = {"is_it": False, "family": "non_it"}
        job.skill_signal_quality = "excluded_non_it"
        job.save(update_fields=["classification_json", "skill_signal_quality"])

        result = ZeroSkillJobRecoveryService.recover_job(job)

        self.assertEqual(result["skipped_excluded"], 1)
        self.assertFalse(NormalizedJobSkill.objects.filter(job=job).exists())

    def test_recovery_skips_jobs_that_already_have_skills(self):
        job = self.create_job(
            title="Apprenti(e) Technicien Informatique",
            description="support aux utilisateurs et dépannage.",
            job_id="already-skilled",
        )
        skill = Skill.objects.get(canonical_name="IT Support")
        NormalizedJobSkill.objects.create(
            job=job,
            skill=skill,
            requirement_type=RequirementType.DETECTED.value,
            source=SkillSource.RULE.value,
        )

        result = ZeroSkillJobRecoveryService.recover_job(job)

        self.assertEqual(result["skipped_existing_skills"], 1)
        self.assertEqual(NormalizedJobSkill.objects.filter(job=job).count(), 1)

    def test_recovery_command_dry_run_does_not_write_and_apply_is_idempotent(self):
        job = self.create_job(
            title="ALTERNANT EN INFORMATIQUE",
            description="installation/configuration des équipements et dépannage.",
            job_id="cmd-recovery",
        )

        out = StringIO()
        call_command("recover_zero_skill_jobs", "--active-only", "--dry-run", "--limit", "10", stdout=out)
        self.assertIn("Dry run", out.getvalue())
        self.assertFalse(NormalizedJobSkill.objects.filter(job=job).exists())

        out = StringIO()
        call_command("recover_zero_skill_jobs", "--active-only", "--apply", "--limit", "10", stdout=out)
        self.assertIn("Apply", out.getvalue())
        first_count = NormalizedJobSkill.objects.filter(job=job).count()
        self.assertGreater(first_count, 0)

        out = StringIO()
        call_command("recover_zero_skill_jobs", "--active-only", "--apply", "--limit", "10", stdout=out)
        self.assertEqual(NormalizedJobSkill.objects.filter(job=job).count(), first_count)

    @patch("apps.jobs.services.zero_skill_recovery.ZeroSkillJobRecoveryService.recover_queryset")
    def test_admin_action_calls_recovery_service_only(self, mock_recover):
        job = self.create_job(
            title="Apprenti(e) Technicien Informatique",
            description="support aux utilisateurs.",
            job_id="admin-action",
        )
        mock_recover.return_value = {
            "jobs_inspected": 1,
            "skipped_excluded": 0,
            "recovered_jobs": 1,
            "skills_created": 1,
            "still_zero_skill": 0,
            "skipped_existing_skills": 0,
            "examples": [],
        }

        class DummyRequest:
            pass

        model_admin = NormalizedJobAdmin(NormalizedJob, AdminSite())
        with patch.object(model_admin, "message_user") as mock_message:
            recover_zero_skill_jobs_action(model_admin, DummyRequest(), NormalizedJob.objects.filter(id=job.id))

        mock_recover.assert_called_once()
        mock_message.assert_called_once()
