from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from io import StringIO
from django.core.management import call_command
from django.contrib.auth import get_user_model

from apps.jobs.models import (
    JobSource,
    RawJobRecord,
    NormalizedJob,
    NormalizedJobSkill,
    JobStatus,
    RequirementType,
    SkillSource,
)
from apps.jobs.services.eligibility import JobEligibilityService, PublicJobState
from apps.jobs.services.presentation import JobPresentationService
from apps.matching.models import MatchResult
from apps.skills.models import Skill

class EligibilityTests(TestCase):
    def setUp(self):
        self.source = JobSource.objects.create(name="Test Source", slug="test", is_active=True)
        self.client = Client()

    def _create_job(
        self,
        source_job_id,
        title,
        description,
        is_it,
        family,
        confidence,
        skill_status,
        signal_quality,
        contract_type="CDD",
        job_type="CDD",
        with_job_skill=None,
    ):
        raw = RawJobRecord.objects.create(
            source=self.source,
            source_job_id=source_job_id,
            raw_payload_json={},
            payload_hash="hash",
            first_seen_at=timezone.now(),
            last_seen_at=timezone.now(),
            last_fetched_at=timezone.now(),
        )
        job = NormalizedJob.objects.create(
            source=self.source,
            raw_record=raw,
            source_job_id=source_job_id,
            title=title,
            description=description,
            status=JobStatus.ACTIVE,
            skill_extraction_status=skill_status,
            skill_signal_quality=signal_quality,
            classification_json={
                "is_it": is_it,
                "family": family,
                "confidence": confidence
            },
            first_seen_at=timezone.now(),
            last_seen_at=timezone.now(),
            last_fetched_at=timezone.now(),
            contract_type=contract_type,
            job_type=job_type,
            required_skills_json=["Python"] if signal_quality == "strong" else [],
        )
        if with_job_skill is None:
            with_job_skill = signal_quality == "strong"
        if with_job_skill:
            skill, _ = Skill.objects.get_or_create(
                slug=f"skill-{source_job_id}",
                defaults={"canonical_name": f"Skill {source_job_id}", "category": "programming_language"},
            )
            NormalizedJobSkill.objects.create(
                job=job,
                skill=skill,
                requirement_type=RequirementType.REQUIRED,
                source=SkillSource.RULE,
            )
        return job

    def test_eligibility_states(self):
        # 1. Matchable job
        j1 = self._create_job("j1", "Data Engineer", "GCP", True, "data_ai_bi", "high", "success", "strong")
        self.assertEqual(JobEligibilityService.classify_public_state(j1), PublicJobState.PUBLIC_MATCHABLE)
        self.assertTrue(JobEligibilityService.is_matchable(j1))
        self.assertTrue(JobEligibilityService.is_publicly_visible(j1))

        # 2. Excluded non IT job
        j2 = self._create_job("j2", "Business Developer", "Cyber", False, "non_it", "excluded", "pending", "excluded_non_it")
        self.assertEqual(JobEligibilityService.classify_public_state(j2), PublicJobState.EXCLUDED)
        self.assertFalse(JobEligibilityService.is_matchable(j2))
        self.assertFalse(JobEligibilityService.is_publicly_visible(j2))

        # 3. IT but pending analysis
        j3 = self._create_job("j3", "DevOps", "AWS", True, "devops_cloud_sre", "high", "pending", "unknown")
        self.assertEqual(JobEligibilityService.classify_public_state(j3), PublicJobState.PUBLIC_LIMITED_PENDING_ANALYSIS)
        self.assertFalse(JobEligibilityService.is_matchable(j3))
        self.assertTrue(JobEligibilityService.is_publicly_visible(j3))

        # 4. IT but zero skills (missing signal)
        j4 = self._create_job("j4", "DevOps", "AWS", True, "devops_cloud_sre", "high", "success", "missing")
        self.assertEqual(JobEligibilityService.classify_public_state(j4), PublicJobState.ADMIN_REVIEW_ONLY)
        self.assertFalse(JobEligibilityService.is_matchable(j4))
        self.assertFalse(JobEligibilityService.is_publicly_visible(j4))

    def test_public_views_respect_eligibility(self):
        j_matchable = self._create_job("j1", "Data Engineer", "GCP", True, "data_ai_bi", "high", "success", "strong")
        j_excluded = self._create_job("j2", "Business Developer", "Cyber", False, "non_it", "excluded", "pending", "excluded_non_it")
        j_admin = self._create_job("j3", "DevOps", "AWS", True, "devops_cloud_sre", "high", "success", "missing")

        # Public list
        response = self.client.get(reverse("jobs:list"))
        self.assertEqual(response.status_code, 200)
        jobs_in_context = list(response.context["page_obj"].object_list)
        self.assertIn(j_matchable, jobs_in_context)
        self.assertNotIn(j_excluded, jobs_in_context)
        self.assertNotIn(j_admin, jobs_in_context)

        # Job detail - matchable
        resp_m = self.client.get(reverse("jobs:detail", kwargs={"public_id": j_matchable.public_id}))
        self.assertEqual(resp_m.status_code, 200)

        # Job detail - excluded
        resp_e = self.client.get(reverse("jobs:detail", kwargs={"public_id": j_excluded.public_id}))
        self.assertEqual(resp_e.status_code, 404)

        # Quick match blocking on admin job
        resp_q = self.client.post(reverse("matching:quick_match", kwargs={"public_id": j_admin.public_id}), {"skills": "python"})
        self.assertEqual(resp_q.status_code, 200)
        self.assertIn("not currently eligible", resp_q.content.decode())
        
    def test_badge_deduplication(self):
        j1 = self._create_job("j1", "Data Engineer", "GCP", True, "data_ai_bi", "high", "success", "strong", contract_type="CDD", job_type="CDD")
        badges = JobPresentationService.get_deduplicated_badges(j1)
        texts = [b["text"] for b in badges]
        self.assertEqual(texts, ["CDD"])

    def test_public_list_includes_true_pending_analysis_only(self):
        pending = self._create_job("pending", "DevOps", "AWS", True, "devops_cloud_sre", "high", "pending", "unknown")
        missing_done = self._create_job("missing-done", "DevOps", "AWS", True, "devops_cloud_sre", "high", "success", "unknown")

        response = self.client.get(reverse("jobs:list"))

        content = response.content.decode()
        jobs_in_context = list(response.context["page_obj"].object_list)
        self.assertIn(pending, jobs_in_context)
        self.assertNotIn(missing_done, jobs_in_context)
        self.assertIn("Compétences en cours d'analyse", content)

    def test_generic_only_is_public_review_not_matchable(self):
        job = self._create_job("generic", "Consultant IT", "Informatique", True, "low_confidence_it", "low", "success", "generic_only")

        self.assertEqual(JobEligibilityService.classify_public_state(job), PublicJobState.ADMIN_REVIEW_ONLY)
        self.assertFalse(JobEligibilityService.is_publicly_visible(job))
        self.assertFalse(JobEligibilityService.is_matchable(job))

    def test_zero_skill_job_cannot_be_public_matchable(self):
        job = self._create_job(
            "zero-skill",
            "Data Engineer GCP",
            "Pipelines SQL et GCP.",
            True,
            "data_ai_bi",
            "high",
            "not_enough_text",
            "partial",
            with_job_skill=False,
        )

        self.assertEqual(JobEligibilityService.classify_public_state(job), PublicJobState.ADMIN_REVIEW_ONLY)
        self.assertFalse(JobEligibilityService.is_publicly_visible(job))
        self.assertFalse(JobEligibilityService.is_matchable(job))
        self.assertNotIn(job, list(JobEligibilityService.filter_matchable()))

    def test_bad_outreach_and_franchise_jobs_not_public_or_matchable(self):
        mediator = self._create_job(
            "mediator",
            "Médiateur/Médiatrice scientifique - spécialité cybersécurité",
            "Animation d'ateliers de découverte pour le grand public et orientation.",
            False,
            "non_it",
            "excluded",
            "not_enough_text",
            "excluded_non_it",
            with_job_skill=False,
        )
        franchise = self._create_job(
            "franchise",
            "Animateur/trice réseau / développeur/euse réseau de franchise",
            "Animer le réseau de franchise, accompagner les franchisés et points de vente.",
            False,
            "non_it",
            "excluded",
            "not_enough_text",
            "excluded_non_it",
            with_job_skill=False,
        )

        for job in (mediator, franchise):
            self.assertEqual(JobEligibilityService.classify_public_state(job), PublicJobState.EXCLUDED)
            self.assertFalse(JobEligibilityService.is_publicly_visible(job))
            self.assertFalse(JobEligibilityService.is_matchable(job))

        list_response = self.client.get(reverse("jobs:list"))
        jobs_in_context = list(list_response.context["page_obj"].object_list)
        self.assertNotIn(mediator, jobs_in_context)
        self.assertNotIn(franchise, jobs_in_context)

        for job in (mediator, franchise):
            detail_response = self.client.get(reverse("jobs:detail", kwargs={"public_id": job.public_id}))
            self.assertEqual(detail_response.status_code, 404)

            quick_response = self.client.post(
                reverse("matching:quick_match", kwargs={"public_id": job.public_id}),
                {"skills": "python"},
            )
            self.assertEqual(quick_response.status_code, 200)
            self.assertIn("not currently eligible", quick_response.content.decode())

            user = get_user_model().objects.create_user(
                username=f"user-{job.source_job_id}",
                email=f"{job.source_job_id}@example.test",
                password="testpass123",
            )
            self.client.force_login(user)
            detailed_response = self.client.post(reverse("matching:create", kwargs={"public_id": job.public_id}))
            self.assertEqual(detailed_response.status_code, 302)
            self.assertFalse(MatchResult.objects.filter(user=user, job=job).exists())
            self.client.logout()

    def test_protected_it_jobs_with_materialized_skills_are_matchable(self):
        protected_jobs = [
            ("data-gcp", "Data Engineer GCP", "Pipelines SQL et GCP.", "data_ai_bi"),
            ("devops", "Tech Lead / DevOps", "CI/CD, Docker, Kubernetes et Terraform.", "devops_cloud_sre"),
            ("java-angular", "Développeur fullstack Java/Angular", "Java, API REST et Angular.", "software_development"),
            ("dotnet", "Développeur .NET / C# Fullstack", "C#, .NET, API et frontend.", "software_development"),
            (
                "cyber-consultant",
                "Consultant Cybersécurité Sénior",
                "Audits sécurité, analyse de risques, ISO 27001 et durcissement.",
                "cybersecurity",
            ),
        ]

        for source_job_id, title, description, family in protected_jobs:
            job = self._create_job(
                source_job_id,
                title,
                description,
                True,
                family,
                "high",
                "success",
                "strong",
                with_job_skill=True,
            )
            self.assertEqual(JobEligibilityService.classify_public_state(job), PublicJobState.PUBLIC_MATCHABLE)
            self.assertTrue(JobEligibilityService.is_publicly_visible(job))
            self.assertTrue(JobEligibilityService.is_matchable(job))
            self.assertIn(job, list(JobEligibilityService.filter_matchable()))

    def test_reclassify_jobs_dry_run_apply_and_idempotency(self):
        corrected = self._create_job(
            "corrected",
            "Data Engineer GCP",
            "Pipelines SQL et GCP.",
            False,
            "non_it",
            "excluded",
            "success",
            "excluded_non_it",
        )
        hidden = self._create_job(
            "hidden",
            "Business Developer Cybersécurité",
            "Prospection commerciale cyber.",
            True,
            "cybersecurity",
            "high",
            "success",
            "strong",
        )

        dry_out = StringIO()
        call_command("reclassify_jobs", "--active-only", "--dry-run", "--limit", "20", stdout=dry_out)
        corrected.refresh_from_db()
        hidden.refresh_from_db()
        self.assertEqual(corrected.skill_signal_quality, "excluded_non_it")
        self.assertEqual(hidden.skill_signal_quality, "strong")
        self.assertIn("Jobs changed from excluded -> IT", dry_out.getvalue())

        apply_out = StringIO()
        call_command("reclassify_jobs", "--active-only", "--apply", "--limit", "20", stdout=apply_out)
        corrected.refresh_from_db()
        hidden.refresh_from_db()
        self.assertNotEqual(corrected.skill_signal_quality, "excluded_non_it")
        self.assertEqual(corrected.classification_json["family"], "data_ai_bi")
        self.assertEqual(hidden.skill_signal_quality, "excluded_non_it")
        self.assertEqual(hidden.classification_json["family"], "non_it")
        self.assertIn("Jobs changed from visible -> excluded/admin_review", apply_out.getvalue())

        second_out = StringIO()
        call_command("reclassify_jobs", "--active-only", "--apply", "--limit", "20", stdout=second_out)
        self.assertNotIn("Jobs changed from excluded -> IT", second_out.getvalue())
        self.assertNotIn("Jobs changed from visible -> excluded/admin_review", second_out.getvalue())
