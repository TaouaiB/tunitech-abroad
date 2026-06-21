from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.core.exceptions import PermissionDenied
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import Http404
from django.test import Client, TestCase, override_settings
from django.urls import NoReverseMatch, reverse
from django.utils import timezone

from apps.cvs.models import CVUpload
from apps.jobs.models import (
    ExperienceLevel,
    JobSource,
    JobStatus,
    JobType,
    NormalizedJob,
    NormalizedJobSkill,
    RawJobRecord,
    RemoteType,
    RequirementType,
    SkillSource,
    SourceType,
)
from apps.matching.models import MatchResult, QuickMatchSession
from apps.matching.services.match_result import MatchResultService
from apps.matching.services.quick_match import QuickMatchRateLimitExceeded, QuickMatchService
from apps.matching.services.scoring import MatchScoringService
from apps.profiles.models import CandidateProfile, ProfileSkill
from apps.skills.models import Skill, SkillAlias, SkillCategory

UserModel = get_user_model()


def create_test_user(
    *,
    username: str,
    email: str,
    password: str = "password",
    is_staff: bool = False,
) -> AbstractBaseUser:
    user = UserModel.objects.create(
        username=username,
        email=email,
        is_staff=is_staff,
    )
    user.set_password(password)
    user.save(update_fields=["password"])
    return user


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class MatchingTests(TestCase):
    def setUp(self):
        self.user = create_test_user(
            username="candidate",
            email="candidate@example.test",
            password="password",
        )
        self.other_user = create_test_user(
            username="other",
            email="other@example.test",
            password="password",
        )
        self.profile = CandidateProfile.objects.create(
            user=self.user,
            years_experience=3.0,
            current_level="mid_level",
            target_country="France",
            target_roles=["Backend Developer"],
            french_level="intermediate",
            english_level="fluent",
            relocation_preference="yes",
            remote_preference="hybrid",
            profile_completion_score=80,
        )
        CandidateProfile.objects.create(
            user=self.other_user,
            years_experience=1.0,
            current_level="junior",
            target_country="France",
            target_roles=["Frontend Developer"],
            french_level="basic",
            profile_completion_score=60,
        )

        self.python = self._skill("Python", SkillCategory.PROGRAMMING_LANGUAGE)
        self.django = self._skill("Django", SkillCategory.BACKEND)
        self.postgres = self._skill("PostgreSQL", SkillCategory.DATABASE)
        self.react = self._skill("React", SkillCategory.FRONTEND)

        ProfileSkill.objects.create(profile=self.profile, raw_name="Python", normalized_name="python")
        ProfileSkill.objects.create(profile=self.profile, raw_name="Django", normalized_name="django")

        self.source = JobSource.objects.create(
            name="France Travail",
            slug="france-travail-test",
            source_type=SourceType.FIXTURE,
        )
        self.job = self._job("job-1", "Backend Developer Python")
        self._job_skill(self.job, self.python, RequirementType.REQUIRED)
        self._job_skill(self.job, self.django, RequirementType.REQUIRED)
        self._job_skill(self.job, self.postgres, RequirementType.OPTIONAL)

        self.client = Client()

    def _skill(self, name, category):
        skill = Skill.objects.create(
            canonical_name=name,
            slug=name.lower().replace(" ", "-"),
            category=category,
            is_active=True,
        )
        SkillAlias.objects.create(skill=skill, alias=name, normalized_alias=name.lower())
        return skill

    def _job(
        self,
        source_job_id,
        title,
        *,
        status=JobStatus.ACTIVE,
        expires_at=None,
        experience_level=ExperienceLevel.MID_LEVEL,
        country="France",
        remote_type=RemoteType.HYBRID,
        language_requirements=None,
        classification_json=None,
        skill_signal_quality="strong",
    ):
        now = timezone.now()
        raw = RawJobRecord.objects.create(
            source=self.source,
            source_job_id=source_job_id,
            raw_payload_json={},
            payload_hash=source_job_id,
            first_seen_at=now,
            last_seen_at=now,
            last_fetched_at=now,
        )
        return NormalizedJob.objects.create(
            source=self.source,
            raw_record=raw,
            source_job_id=source_job_id,
            title=title,
            company_name="Tech Corp",
            location="Paris",
            country=country,
            city="Paris",
            contract_type="CDI",
            remote_type=remote_type,
            job_type=JobType.FULL_TIME_JOB,
            experience_level=experience_level,
            description="Build backend systems.",
            status=status,
            expires_at=expires_at,
            required_skills_json=["Python", "Django"],
            optional_skills_json=["PostgreSQL"],
            language_requirements_json=language_requirements or {},
            classification_json=classification_json or {"family": "software_development", "is_it": True, "confidence": "high"},
            skill_signal_quality=skill_signal_quality,
            first_seen_at=now,
            last_seen_at=now,
            last_fetched_at=now,
        )

    def _job_skill(self, job, skill, requirement_type):
        return NormalizedJobSkill.objects.create(
            job=job,
            skill=skill,
            requirement_type=requirement_type,
            source=SkillSource.RULE,
            confidence=1,
        )

    def _job_without_extracted_skills(self, source_job_id, title, description="Build software.", classification_json=None):
        job = self._job(source_job_id, title, classification_json=classification_json, skill_signal_quality="missing")
        job.description = description
        job.required_skills_json = []
        job.optional_skills_json = []
        job.save(update_fields=["description", "required_skills_json", "optional_skills_json"])
        return job

    def test_match_result_public_id_exists_and_recompute_is_allowed(self):
        first = MatchResultService.create_match_result(self.user, self.job)
        second = MatchResultService.create_match_result(self.user, self.job)

        self.assertNotEqual(first.public_id, second.public_id)
        self.assertEqual(MatchResult.objects.filter(user=self.user, job=self.job).count(), 2)

    def test_scoring_uses_formula_and_clamps_scores(self):
        result = MatchScoringService.calculate(self.profile, self.job)
        expected = round(
            result.technical_skills_score * 0.50
            + result.experience_score * 0.20
            + result.role_title_score * 0.15
            + result.language_score * 0.15
        )

        self.assertEqual(result.fit_score, expected)
        for score in (
            result.fit_score,
            result.technical_skills_score,
            result.experience_score,
            result.role_title_score,
            result.language_score,
            result.location_score,
        ):
            self.assertGreaterEqual(score, 0)
            self.assertLessEqual(score, 100)

    def test_required_skills_weight_more_than_optional_skills(self):
        optional_only_profile = CandidateProfile.objects.create(
            user=create_test_user(username="optional", email="optional@example.test", password="password"),
            years_experience=3.0,
            current_level="mid_level",
            target_country="France",
            french_level="intermediate",
            profile_completion_score=80,
        )
        required_only_profile = CandidateProfile.objects.create(
            user=create_test_user(username="required", email="required@example.test", password="password"),
            years_experience=3.0,
            current_level="mid_level",
            target_country="France",
            french_level="intermediate",
            profile_completion_score=80,
        )
        ProfileSkill.objects.create(profile=optional_only_profile, raw_name="PostgreSQL", normalized_name="postgresql")
        ProfileSkill.objects.create(profile=required_only_profile, raw_name="Python", normalized_name="python")

        optional_score = MatchScoringService.calculate(optional_only_profile, self.job).technical_skills_score
        required_score = MatchScoringService.calculate(required_only_profile, self.job).technical_skills_score

        self.assertGreater(required_score, optional_score)

    def test_missing_required_french_and_expired_job_risk_flags(self):
        self.profile.french_level = ""
        self.profile.save(update_fields=["french_level"])
        expired_job = self._job(
            "expired",
            "Senior Backend Developer",
            expires_at=timezone.now() - timedelta(days=1),
            experience_level=ExperienceLevel.SENIOR,
        )
        self._job_skill(expired_job, self.react, RequirementType.REQUIRED)

        result = MatchScoringService.calculate(self.profile, expired_job)

        self.assertIn("missing_required_skills", result.risk_flags)
        self.assertIn("french_level_missing", result.risk_flags)
        self.assertIn("experience_too_low", result.risk_flags)
        self.assertIn("job_may_be_expired", result.risk_flags)

    def test_full_scoring_treats_none_french_level_as_missing_for_france_job(self):
        self.profile.french_level = "none"
        self.profile.save(update_fields=["french_level"])

        result = MatchScoringService.calculate(self.profile, self.job)

        self.assertIn("french_level_missing", result.risk_flags)
        self.assertLess(result.language_score, 80)

    def test_profile_signals_do_not_reduce_score(self):
        with_signals = MatchScoringService.calculate(self.profile, self.job)
        self.profile.github_url = "https://github.com/candidate"
        self.profile.linkedin_url = "https://www.linkedin.com/in/candidate"
        self.profile.portfolio_url = "https://candidate.example.test"
        self.profile.save(update_fields=["github_url", "linkedin_url", "portfolio_url"])
        without_signals = MatchScoringService.calculate(self.profile, self.job)

        self.assertEqual(with_signals.fit_score, without_signals.fit_score)
        self.assertIn("profile_signal_missing_github", with_signals.profile_signals)

    def test_data_scientist_without_technical_skills_is_not_reliable_match(self):
        job = self._job_without_extracted_skills(
            "data-no-skills",
            "Data Scientist",
            description="Analyse data and build business reports.",
        )

        result = MatchScoringService.calculate(self.profile, job)

        self.assertIn(result.match_confidence, ["low_confidence", "unavailable"])
        self.assertIn("no_required_skills_extracted", result.risk_flags)

    def test_web_developer_without_extracted_skills_is_unavailable(self):
        job = self._job_without_extracted_skills(
            "web-no-skills",
            "Web Developer",
            description="Build web applications for internal users.",
        )

        result = MatchScoringService.calculate(self.profile, job)

        self.assertEqual(result.match_confidence, "unavailable")
        self.assertIn("insufficient_job_technical_signal", result.risk_flags)

    def test_photography_seller_job_is_unavailable(self):
        job = self._job_without_extracted_skills(
            "photo-seller",
            "Vendeur photographie",
            description="Vente de matériel photo et conseil clients en magasin.",
            classification_json={"family": "non_it", "is_it": False, "confidence": "excluded"}
        )

        result = MatchScoringService.calculate(self.profile, job)

        self.assertEqual(result.match_confidence, "unavailable")
        self.assertLessEqual(result.fit_score, 25)
        self.assertIn("non_it_low_relevance_job", result.risk_flags)

    def test_python_django_required_skills_are_reliable_normal_score(self):
        result = MatchScoringService.calculate(self.profile, self.job)

        self.assertEqual(result.match_confidence, "reliable")
        self.assertGreater(result.fit_score, 0)
        self.assertNotIn("no_required_skills_extracted", result.risk_flags)

    def test_java_spring_angular_required_stack_is_reliable(self):
        java = self._skill("Java", SkillCategory.PROGRAMMING_LANGUAGE)
        spring = self._skill("Spring", SkillCategory.BACKEND)
        angular = self._skill("Angular", SkillCategory.FRONTEND)
        job = self._job(
            "java-spring-angular",
            "Développeur Java Spring Angular",
            classification_json={"family": "software_development", "is_it": True, "confidence": "high"},
            skill_signal_quality="strong",
        )
        self._job_skill(job, java, RequirementType.REQUIRED)
        self._job_skill(job, spring, RequirementType.REQUIRED)
        self._job_skill(job, angular, RequirementType.REQUIRED)

        result = MatchScoringService.calculate(self.profile, job)

        self.assertEqual(result.match_confidence, "reliable")

    def test_generic_ft_competence_labels_only_are_not_reliable(self):
        job = self._job(
            "generic-ft-web",
            "Développeur web",
            classification_json={"family": "web_mobile", "is_it": True, "confidence": "medium"},
            skill_signal_quality="generic_only",
        )
        job.required_skills_json = []
        job.optional_skills_json = ["Concevoir une application web"]
        job.save(update_fields=["required_skills_json", "optional_skills_json"])

        result = MatchScoringService.calculate(self.profile, job)

        self.assertEqual(result.match_confidence, "low_confidence")
        self.assertNotEqual(result.match_confidence, "reliable")

    def test_match_result_snapshots_exclude_private_cv_data(self):
        cv_upload = CVUpload.objects.create(
            user=self.user,
            file=SimpleUploadedFile("cv.pdf", b"%PDF-test", content_type="application/pdf"),
            original_filename="cv.pdf",
            file_hash="abc123",
            file_size=9,
        )

        match = MatchResultService.create_match_result(self.user, self.job, cv_upload=cv_upload)
        snapshot_text = f"{match.profile_snapshot_json} {match.job_snapshot_json}"

        self.assertIn("public_id", match.profile_snapshot_json)
        self.assertIn("public_id", match.job_snapshot_json)
        self.assertNotIn("raw_text", snapshot_text)
        self.assertNotIn("file", snapshot_text)
        self.assertNotIn("url", snapshot_text.lower())
        self.assertNotIn(str(cv_upload.file), snapshot_text)

    def test_match_detail_is_owner_protected(self):
        match = MatchResultService.create_match_result(self.user, self.job)

        retrieved = MatchResultService.get_user_match(self.user, match.public_id)
        self.assertEqual(retrieved, match)
        with self.assertRaises(Exception):
            MatchResultService.get_user_match(self.other_user, match.public_id)

    def test_analytics_failure_does_not_break_match_creation(self):
        with patch("apps.matching.services.match_result.UserEventService.record_event", side_effect=RuntimeError("boom")):
            match = MatchResultService.create_match_result(self.user, self.job)

        self.assertIsInstance(match, MatchResult)

    def test_unauthenticated_user_cannot_create_full_match_service_result(self):
        with self.assertRaises(PermissionDenied):
            MatchResultService.create_match_result(type("Anonymous", (), {"is_authenticated": False})(), self.job)

    def test_match_result_service_rejects_invisible_job(self):
        invisible_job = self._job(
            "invisible",
            "Removed Backend Developer",
            status=JobStatus.REMOVED,
        )

        with self.assertRaises(Http404):
            MatchResultService.create_match_result(self.user, invisible_job)

        self.assertFalse(MatchResult.objects.filter(user=self.user, job=invisible_job).exists())

    def test_quick_match_service_hashes_values_expires_and_rate_limits(self):
        session = QuickMatchService.run_quick_match(
            session_key="test-session",
            job=self.job,
            entered_skills=["Python", "Django"],
            experience_level="mid",
            french_level="advanced",
            ip_address="127.0.0.1",
        )

        self.assertIsInstance(session, QuickMatchSession)
        self.assertNotEqual(session.session_key_hash, "test-session")
        self.assertNotEqual(session.ip_hash, "127.0.0.1")
        self.assertEqual(len(session.session_key_hash), 64)
        self.assertEqual(len(session.ip_hash), 64)
        self.assertGreaterEqual(session.expires_at, timezone.now() + timedelta(hours=23, minutes=59))
        self.assertLessEqual(session.expires_at, timezone.now() + timedelta(hours=24, minutes=1))

        for _ in range(10):
            QuickMatchService.run_quick_match(
                session_key="limited-session",
                job=self.job,
                entered_skills=["Python"],
                experience_level="junior",
                french_level="basic",
                ip_address="192.0.2.10",
            )

        with self.assertRaises(QuickMatchRateLimitExceeded):
            QuickMatchService.run_quick_match(
                session_key="limited-session",
                job=self.job,
                entered_skills=["Python"],
                experience_level="junior",
                french_level="basic",
                ip_address="192.0.2.10",
            )

    def test_quick_match_treats_none_french_level_as_missing_for_france_job(self):
        session = QuickMatchService.run_quick_match(
            session_key="none-french-session",
            job=self.job,
            entered_skills=["Python", "Django"],
            experience_level="mid",
            french_level="none",
            ip_address="198.51.100.10",
        )

        self.assertIn("french_level_missing", session.risk_flags_json)
        self.assertLess(session.estimated_fit_score, 90)

    def test_full_match_post_requires_login_and_uses_uuid_route(self):
        url = reverse("matching:create", kwargs={"public_id": self.job.public_id})
        anonymous_response = self.client.post(url)
        self.assertEqual(anonymous_response.status_code, 302)

        self.client.login(email="candidate@example.test", password="password")
        response = self.client.post(url)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(MatchResult.objects.filter(user=self.user, job=self.job).exists())
        with self.assertRaises(NoReverseMatch):
            reverse("matching:create", kwargs={"public_id": self.job.id})

    def test_quick_match_view_allows_anonymous_user(self):
        url = reverse("matching:quick_match", kwargs={"public_id": self.job.public_id})
        response = self.client.post(
            url,
            {
                "skills": "Python, React",
                "experience_level": "junior",
                "french_level": "intermediate",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(QuickMatchSession.objects.exists())

    def test_quick_match_form_includes_reset_scripts(self):
        url = reverse("jobs:detail", kwargs={"public_id": self.job.public_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'window.addEventListener(\'pageshow\'')
        self.assertContains(response, 'htmx:beforeRequest')
        self.assertContains(response, 'hx-target="#quick-match-result"')

    def test_match_history_and_detail_are_owner_filtered(self):
        match = MatchResultService.create_match_result(self.user, self.job)
        other_match = MatchResultService.create_match_result(self.other_user, self.job)

        self.client.login(email="candidate@example.test", password="password")
        history_response = self.client.get(reverse("matching:history"))
        detail_response = self.client.get(reverse("matching:detail", kwargs={"public_id": match.public_id}))
        other_detail_response = self.client.get(reverse("matching:detail", kwargs={"public_id": other_match.public_id}))

        self.assertContains(history_response, "Backend Developer Python")
        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(other_detail_response.status_code, 404)

    def test_no_internal_integer_match_routes_exist(self):
        self.assertEqual(self.client.post(f"/jobs/{self.job.id}/match/").status_code, 404)
        self.assertEqual(self.client.get("/dashboard/matches/1/").status_code, 404)

    def test_match_detail_unavailable_hides_normal_score_ui_and_raw_flags(self):
        job = self._job_without_extracted_skills(
            "photo-ui",
            "Vendeur photographie",
            description="Vente de matériel photo et conseil clients en magasin.",
            classification_json={"family": "non_it", "is_it": False, "confidence": "excluded"}
        )
        match = MatchResultService.create_match_result(self.user, job)

        self.client.login(email="candidate@example.test", password="password")
        response = self.client.get(reverse("matching:detail", kwargs={"public_id": match.public_id}))

        self.assertContains(response, "Données insuffisantes pour calculer un match fiable")
        self.assertNotContains(response, "Fit Global")
        self.assertNotContains(response, "Technique")
        self.assertContains(response, "Offre probablement non IT")
        self.assertNotContains(response, "non_it_low_relevance_job")

    def test_match_detail_low_confidence_labels_estimate_and_technical_unavailable(self):
        job = self._job(
            "web-ui",
            "Data Analyst",
            classification_json={"family": "data_ai_bi", "is_it": True, "confidence": "high"},
            skill_signal_quality="partial",
        )
        job.required_skills_json = []
        job.optional_skills_json = ["Python"]
        job.description = "Analyse data and build business reports with Python."
        job.save(update_fields=["required_skills_json", "optional_skills_json", "description"])
        self._job_skill(job, self.python, RequirementType.OPTIONAL)
        match = MatchResultService.create_match_result(self.user, job)

        self.client.login(email="candidate@example.test", password="password")
        response = self.client.get(reverse("matching:detail", kwargs={"public_id": match.public_id}))

        self.assertContains(response, "estimation prudente")
        self.assertContains(response, "L'analyse de cette offre est limitée.")
        self.assertNotContains(response, "Excellente nouvelle ! Vous possédez toutes les compétences techniques requises")
        self.assertContains(response, "Signal technique insuffisant")
        self.assertNotContains(response, "no_required_skills_extracted")


class Phase15GHardeningTests(TestCase):
    def _skill(self, name, category):
        skill = Skill.objects.create(
            canonical_name=name,
            slug=name.lower().replace(" ", "-"),
            category=category,
            is_active=True,
        )
        SkillAlias.objects.create(skill=skill, alias=name, normalized_alias=name.lower())
        return skill

    def setUp(self):
        self.user = UserModel.objects.create_user(username="test15g", email="test15g@example.com", password="password")
        self.profile = CandidateProfile.objects.create(
            user=self.user,
            years_experience=3.0,
            current_level="mid",
            french_level="c1",
            profile_completion_score=100
        )

        now = timezone.now()
        source = JobSource.objects.create(name="test", slug="test", source_type="fixture")
        raw = RawJobRecord.objects.create(source=source, source_job_id="test", payload_hash="test", first_seen_at=now, last_seen_at=now, last_fetched_at=now, raw_payload_json={})

        self.job = NormalizedJob.objects.create(
            source=source,
            raw_record=raw,
            source_job_id="test",
            first_seen_at=now,
            last_seen_at=now,
            last_fetched_at=now,
            public_id="00000000-0000-0000-0000-000000000000",
            title="Fullstack JS Developer",
            country="France",
            remote_type="hybrid",
            experience_level="mid",
            status="active",
            classification_json={"confidence": "high", "family": "frontend_backend"}
        )

        self.skill_js = self._skill("JavaScript", SkillCategory.PROGRAMMING_LANGUAGE)
        self.skill_json = self._skill("JSON", SkillCategory.BACKEND)
        self.skill_json_schema = self._skill("JSON Schema", SkillCategory.BACKEND)
        self.skill_openapi = self._skill("OpenAPI", SkillCategory.BACKEND)
        self.skill_jira = self._skill("Jira", SkillCategory.TOOLS)
        self.skill_confluence = self._skill("Confluence", SkillCategory.TOOLS)
        self.skill_wordpress = self._skill("WordPress", SkillCategory.BACKEND)
        self.skill_angular = self._skill("Angular", SkillCategory.FRONTEND)

        NormalizedJobSkill.objects.create(job=self.job, skill=self.skill_js, requirement_type=RequirementType.OPTIONAL)
        NormalizedJobSkill.objects.create(job=self.job, skill=self.skill_json, requirement_type=RequirementType.OPTIONAL)
        NormalizedJobSkill.objects.create(job=self.job, skill=self.skill_json_schema, requirement_type=RequirementType.OPTIONAL)
        NormalizedJobSkill.objects.create(job=self.job, skill=self.skill_openapi, requirement_type=RequirementType.OPTIONAL)
        NormalizedJobSkill.objects.create(job=self.job, skill=self.skill_jira, requirement_type=RequirementType.OPTIONAL)
        NormalizedJobSkill.objects.create(job=self.job, skill=self.skill_confluence, requirement_type=RequirementType.OPTIONAL)
        NormalizedJobSkill.objects.create(job=self.job, skill=self.skill_wordpress, requirement_type=RequirementType.OPTIONAL)
        NormalizedJobSkill.objects.create(job=self.job, skill=self.skill_angular, requirement_type=RequirementType.REQUIRED)

    def test_location_removed_from_final_score(self):
        # Even if profile relocation matches vs not matches, fit score stays same because location is not in calculation.
        # However, location_score might differ.

        self.profile.relocation_preference = True
        self.profile.save()
        res1 = MatchScoringService.calculate(self.profile, self.job)

        self.profile.relocation_preference = False
        self.profile.save()
        res2 = MatchScoringService.calculate(self.profile, self.job)

        self.assertNotEqual(res1.location_score, res2.location_score)
        self.assertEqual(res1.fit_score, res2.fit_score)

    def test_json_is_suppressed_when_implied(self):
        # Profile has JavaScript, lacks Angular
        ProfileSkill.objects.create(profile=self.profile, raw_name="JavaScript", normalized_name="javascript")

        res = MatchScoringService.calculate(self.profile, self.job)

        missing_opt = [s["name"] for s in res.missing_optional_skills]
        self.assertNotIn("JSON", missing_opt)
        self.assertNotIn("Jira", missing_opt)
        self.assertNotIn("Confluence", missing_opt)
        self.assertIn("JSON Schema", missing_opt)
        self.assertIn("OpenAPI", missing_opt)
        self.assertIn("WordPress", missing_opt)

        missing_req = [s["name"] for s in res.missing_required_skills]
        self.assertIn("Angular", missing_req)

        self.assertEqual(Skill.objects.filter(canonical_name__in=["JSON", "Jira", "Confluence"]).count(), 3)
        self.assertEqual(NormalizedJobSkill.objects.filter(job=self.job, skill__canonical_name__in=["JSON", "Jira", "Confluence"]).count(), 3)

    def test_wordpress_is_not_suppressed_when_required(self):
        NormalizedJobSkill.objects.filter(job=self.job, skill=self.skill_wordpress).update(
            requirement_type=RequirementType.REQUIRED
        )

        res = MatchScoringService.calculate(self.profile, self.job)

        missing_req = [s["name"] for s in res.missing_required_skills]
        self.assertIn("Angular", missing_req)
        self.assertIn("WordPress", missing_req)

    def test_noisy_optional_skills_suppressed_but_preserved_terms_display(self):
        noisy_skills = [
            self._skill("XML", SkillCategory.BACKEND),
            self._skill("YAML", SkillCategory.BACKEND),
            self._skill("CSV", SkillCategory.DATA_AI),
            self._skill("Markdown", SkillCategory.TOOLS),
            self._skill("SOAP", SkillCategory.BACKEND),
            self._skill("Agile", SkillCategory.METHODOLOGY),
            self._skill("Scrum", SkillCategory.METHODOLOGY),
            self._skill("Kanban", SkillCategory.METHODOLOGY),
            self._skill("Excel", SkillCategory.TOOLS),
            self._skill("Office 365", SkillCategory.TOOLS),
        ]
        for skill in noisy_skills:
            NormalizedJobSkill.objects.create(job=self.job, skill=skill, requirement_type=RequirementType.OPTIONAL)

        res = MatchScoringService.calculate(self.profile, self.job)

        missing_opt = [s["name"] for s in res.missing_optional_skills]
        for skill_name in ["JSON", "XML", "YAML", "CSV", "Markdown", "SOAP", "Jira", "Confluence", "Agile", "Scrum", "Kanban", "Excel", "Office 365"]:
            self.assertNotIn(skill_name, missing_opt)
        for skill_name in ["JSON Schema", "OpenAPI", "WordPress"]:
            self.assertIn(skill_name, missing_opt)

    def test_actions_recommended_copy_is_french(self):
        res = MatchScoringService.calculate(self.profile, self.job)
        actions = res.recommended_actions
        self.assertTrue(any("Priorité : ajoutez" in action for action in actions))

        # Test when no required skills missing
        ProfileSkill.objects.create(profile=self.profile, raw_name="Angular", normalized_name="angular")
        res2 = MatchScoringService.calculate(self.profile, self.job)
        actions2 = res2.recommended_actions
        self.assertTrue(any("Votre profil couvre les compétences principales" in action for action in actions2))

    def test_match_detail_removes_scored_location_and_redundant_required_gap_card(self):
        match = MatchResult.objects.create(
            user=self.user,
            profile=self.profile,
            job=self.job,
            profile_snapshot_json={},
            job_snapshot_json={"title": self.job.title, "company_name": "Test"},
            fit_score=52,
            technical_skills_score=40,
            experience_score=100,
            role_title_score=50,
            language_score=70,
            location_score=0,
            missing_required_skills_json=[{"name": "Angular"}],
            missing_optional_skills_json=[{"name": "Kubernetes"}],
            risk_flags_json=["missing_required_skills"],
            recommended_actions_json=[
                "Priorité : ajoutez Angular à votre plan d'apprentissage. Mettez à jour votre CV si vous avez déjà utilisé Angular."
            ],
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse("matching:detail", kwargs={"public_id": match.public_id}))

        self.assertContains(response, "Mobilité / contrat")
        self.assertContains(response, "Poste basé en France")
        self.assertNotContains(response, "Localisation")
        self.assertContains(response, "Compétences requises manquantes")
        self.assertContains(response, "Angular")
        self.assertNotContains(response, "Compétences obligatoires non détectées")
        self.assertNotContains(response, "À renforcer")
        self.assertNotContains(response, "Points de vigilance")
        self.assertContains(response, "Actions recommandées")
        self.assertContains(response, "border-rose-200")

    def test_empty_human_risk_flags_does_not_render_points_de_vigilance(self):
        match = MatchResult.objects.create(
            user=self.user,
            profile=self.profile,
            job=self.job,
            profile_snapshot_json={},
            job_snapshot_json={"title": self.job.title, "company_name": "Test"},
            fit_score=72,
            technical_skills_score=70,
            experience_score=100,
            role_title_score=70,
            language_score=70,
            location_score=0,
            risk_flags_json=["missing_required_skills"],
            profile_signals_json=[],
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse("matching:detail", kwargs={"public_id": match.public_id}))

        self.assertEqual(match.human_risk_flags, [])
        self.assertNotContains(response, "Points de vigilance")

class Phase15GRecommendationsViewTests(TestCase):
    def setUp(self):
        self.user = UserModel.objects.create_user(username="test15g-refresh", email="test15g-refresh@example.com", password="password")

    def test_refresh_recommendations_endpoint_post_only(self):
        self.client.force_login(self.user)
        url = reverse("recommendations:refresh")

        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)

    def test_refresh_recommendations_requires_login(self):
        url = reverse("recommendations:refresh")

        response = self.client.post(url)

        self.assertRedirects(response, f"{reverse('account_login')}?next={url}")

    def test_refresh_recommendations_post_calls_service(self):
        self.client.force_login(self.user)
        url = reverse("recommendations:refresh")
        result = type(
            "RefreshResult",
            (),
            {"skipped_reason": None, "stored_recommendations_count": 3},
        )()

        with patch("apps.recommendations.views.RecommendationService.refresh_for_user", return_value=result) as refresh:
            response = self.client.post(url)

        self.assertRedirects(response, reverse("dashboard:recommendations"))
        refresh.assert_called_once_with(self.user, trigger_type="manual_refresh")

    def test_refresh_button_appears_with_csrf_form(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("dashboard:recommendations"))

        self.assertContains(response, "Actualiser mes recommandations")
        self.assertContains(response, f'action="{reverse("recommendations:refresh")}"')
        self.assertContains(response, "csrfmiddlewaretoken")
