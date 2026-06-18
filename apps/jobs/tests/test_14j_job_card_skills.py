from django.test import TestCase
from django.template.loader import render_to_string
from apps.jobs.models import NormalizedJob, JobSource, SourceType, RemoteType, JobType, ExperienceLevel, NormalizedJobSkill, RequirementType, SkillSource, SkillExtractionStatus
from apps.skills.models import Skill
from django.utils import timezone

class JobCardSkillsTests(TestCase):
    def setUp(self):
        source = JobSource.objects.create(name="FT", slug="ft", source_type=SourceType.API)
        from apps.jobs.models import RawJobRecord
        raw_record = RawJobRecord.objects.create(
            source=source,
            source_job_id="123",
            raw_payload_json={},
            payload_hash="hash",
            first_seen_at=timezone.now(),
            last_seen_at=timezone.now(),
            last_fetched_at=timezone.now()
        )
        self.dummy_job = NormalizedJob.objects.create(
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

    def test_job_card_skills_with_canonical(self):
        skill1 = Skill.objects.create(canonical_name="Python", category="programming_language", slug="python")
        skill2 = Skill.objects.create(canonical_name="Django", category="framework", slug="django")
        
        NormalizedJobSkill.objects.create(job=self.dummy_job, skill=skill1, requirement_type=RequirementType.REQUIRED, source=SkillSource.RULE)
        NormalizedJobSkill.objects.create(job=self.dummy_job, skill=skill2, requirement_type=RequirementType.REQUIRED, source=SkillSource.RULE)
        
        html = render_to_string('jobs/partials/job_card.html', {'job': self.dummy_job})
        
        self.assertIn("Python", html)
        self.assertIn("Django", html)
        self.assertNotIn("Aucune compétence", html)

    def test_job_card_skills_with_raw_json(self):
        # Setup job with only raw required skills
        self.dummy_job.required_skills_json = ["React", "A very long raw string that should be excluded from the chips because it is over 35 characters long", "Node"]
        self.dummy_job.save()
        
        html = render_to_string('jobs/partials/job_card.html', {'job': self.dummy_job})
        
        self.assertIn("React", html)
        self.assertIn("Node", html)
        # Long string should not be there
        self.assertNotIn("A very long raw string", html)
        self.assertNotIn("Aucune compétence", html)

    def test_job_card_skills_empty(self):
        self.dummy_job.required_skills_json = []
        self.dummy_job.skill_extraction_status = SkillExtractionStatus.SUCCESS
        self.dummy_job.save()
        
        html = render_to_string('jobs/partials/job_card.html', {'job': self.dummy_job})
        
        self.assertIn("Aucune compétence spécifique extraite", html)

    def test_job_card_skills_all_raw_sentences_shows_empty_state(self):
        self.dummy_job.required_skills_json = [
            "A very long raw string that should be excluded from the chips because it is over 35 characters long",
        ]
        self.dummy_job.skill_extraction_status = SkillExtractionStatus.SUCCESS
        self.dummy_job.save()

        html = render_to_string('jobs/partials/job_card.html', {'job': self.dummy_job})

        self.assertNotIn("A very long raw string", html)
        self.assertIn("Aucune compétence spécifique extraite", html)

    def test_job_card_skills_processing_state(self):
        self.dummy_job.required_skills_json = []
        self.dummy_job.skill_extraction_status = "processing"
        self.dummy_job.save(update_fields=["required_skills_json", "skill_extraction_status"])

        html = render_to_string('jobs/partials/job_card.html', {'job': self.dummy_job})

        self.assertIn("Compétences en cours d'analyse", html)
