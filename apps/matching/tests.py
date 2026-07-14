from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.core.exceptions import PermissionDenied, ValidationError
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
from apps.matching.services.feedback import MatchFeedbackService
from apps.matching.services.match_result import MatchResultService
from apps.matching.services.policy_version import MATCH_SCORING_VERSION
from apps.matching.services.quick_match import QuickMatchRateLimitExceeded, QuickMatchService
from apps.matching.services.scoring import MatchScoringService
from apps.profiles.models import CandidateProfile, ProfileSkill
from apps.skills.models import Skill, SkillAlias, SkillCategory, UnmatchedSkillCandidate

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

        ProfileSkill.objects.create(profile=self.profile, raw_name="Python", normalized_name="python", skill=self.python)
        ProfileSkill.objects.create(profile=self.profile, raw_name="Django", normalized_name="django", skill=self.django)

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

    def _job_skill(self, job, skill, requirement_type, *, confidence=1):
        return NormalizedJobSkill.objects.create(
            job=job,
            skill=skill,
            requirement_type=requirement_type,
            source=SkillSource.RULE,
            confidence=confidence,
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

    def test_get_user_match_recomputes_when_profile_skills_change(self):
        match = MatchResultService.create_match_result(self.user, self.job)
        old_score = match.fit_score

        ProfileSkill.objects.create(
            profile=self.profile,
            raw_name="PostgreSQL",
            normalized_name="postgresql",
            skill=self.postgres,
            is_confirmed=True,
        )

        refreshed = MatchResultService.get_user_match(self.user, match.public_id)

        self.assertGreaterEqual(refreshed.fit_score, old_score)
        self.assertIn("postgresql", refreshed.profile_snapshot_json["skills"])

    def test_scoring_uses_formula_and_clamps_scores(self):
        result = MatchScoringService.calculate(self.profile, self.job)
        expected = round(
            result.technical_skills_score * 0.45
            + result.experience_score * 0.20
            + result.role_title_score * 0.15
            + result.language_score * 0.10
            + result.location_score * 0.10
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
        postgres_skill = Skill.objects.get(canonical_name="PostgreSQL")
        python_skill = Skill.objects.get(canonical_name="Python")
        ProfileSkill.objects.create(profile=optional_only_profile, raw_name="PostgreSQL", normalized_name="postgresql", skill=postgres_skill)
        ProfileSkill.objects.create(profile=required_only_profile, raw_name="Python", normalized_name="python", skill=python_skill)

        optional_score = MatchScoringService.calculate(optional_only_profile, self.job).technical_skills_score
        required_score = MatchScoringService.calculate(required_only_profile, self.job).technical_skills_score

        self.assertGreater(required_score, optional_score)

    def test_scoring_uses_canonical_skill_id_not_raw_profile_text(self):
        dotnet = self._skill(".NET", SkillCategory.BACKEND)
        job = self._job("dotnet-job", ".NET Backend Developer")
        self._job_skill(job, dotnet, RequirementType.REQUIRED)
        ProfileSkill.objects.create(
            profile=self.profile,
            raw_name=".NET Core",
            normalized_name=".net core",
            skill=dotnet,
        )

        result = MatchScoringService.calculate(self.profile, job)

        self.assertIn({"name": ".NET", "type": "required"}, result.strong_skills)
        self.assertNotIn({"name": ".NET", "requirement_type": "required"}, result.missing_required_skills)

    def test_low_confidence_required_skill_does_not_inflate_technical_score(self):
        go = self._skill("Go", SkillCategory.PROGRAMMING_LANGUAGE)
        ProfileSkill.objects.create(
            profile=self.profile,
            raw_name="Go",
            normalized_name="go",
            skill=go,
        )
        high_confidence_job = self._job("go-high-confidence", "Go Developer")
        low_confidence_job = self._job("go-low-confidence", "Go Developer")
        self._job_skill(high_confidence_job, go, RequirementType.REQUIRED, confidence=0.9)
        self._job_skill(low_confidence_job, go, RequirementType.REQUIRED, confidence=0.49)

        high_result = MatchScoringService.calculate(self.profile, high_confidence_job)
        low_result = MatchScoringService.calculate(self.profile, low_confidence_job)

        self.assertIn({"name": "Go", "type": "required"}, high_result.strong_skills)
        self.assertEqual(high_result.technical_skills_score, 90)
        self.assertEqual(high_result.match_confidence, MatchScoringService.CONFIDENCE_RELIABLE)

        self.assertNotIn({"name": "Go", "type": "required"}, low_result.strong_skills)
        self.assertLess(low_result.technical_skills_score, high_result.technical_skills_score)
        self.assertIn("low_confidence_job_skills", low_result.risk_flags)
        self.assertIn("low_confidence_job_skills", low_result.profile_signals)
        self.assertNotEqual(low_result.match_confidence, MatchScoringService.CONFIDENCE_RELIABLE)

    def test_missing_required_french_and_expired_job_risk_flags(self):
        self.profile.french_level = ""
        self.profile.save(update_fields=["french_level"])
        expired_job = self._job(
            "expired",
            "Senior Backend Developer",
            expires_at=timezone.now() - timedelta(days=1),
            experience_level=ExperienceLevel.SENIOR,
            language_requirements={"french": "required"},
        )
        self._job_skill(expired_job, self.react, RequirementType.REQUIRED)

        result = MatchScoringService.calculate(self.profile, expired_job)

        self.assertIn("missing_required_skills", result.risk_flags)
        self.assertIn("french_level_missing", result.risk_flags)
        self.assertIn("experience_too_low", result.risk_flags)
        self.assertIn("job_may_be_expired", result.risk_flags)

    def test_full_scoring_does_not_invent_french_requirement_for_france_job(self):
        self.profile.french_level = "none"
        self.profile.save(update_fields=["french_level"])

        result = MatchScoringService.calculate(self.profile, self.job)

        self.assertNotIn("french_level_missing", result.risk_flags)
        self.assertEqual(result.language_score, 100)

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

    def test_quick_match_does_not_invent_french_requirement_for_france_job(self):
        session = QuickMatchService.run_quick_match(
            session_key="none-french-session",
            job=self.job,
            entered_skills=["Python", "Django"],
            experience_level="mid",
            french_level="none",
            ip_address="198.51.100.10",
        )

        self.assertNotIn("french_level_missing", session.risk_flags_json)

    def test_quick_match_uses_explicit_required_only_language_policy_and_neutral_metadata(self):
        optional_job = self._job(
            "quick-optional-language",
            "Optional languages",
            experience_level=ExperienceLevel.UNKNOWN,
            language_requirements={"french": "optional", "english": "preferred"},
        )
        self._job_skill(optional_job, self.python, RequirementType.REQUIRED)
        optional = QuickMatchService.run_quick_match(
            session_key="quick-optional-language",
            job=optional_job,
            entered_skills=["Python"],
            experience_level="junior",
            french_level="none",
            ip_address="198.51.100.20",
        )
        self.assertNotIn("french_level_missing", optional.risk_flags_json)
        self.assertNotIn("english_level_missing", optional.risk_flags_json)
        self.assertEqual(optional.estimated_fit_score, 92)

        french_required_job = self._job(
            "quick-french-required",
            "French required",
            experience_level=ExperienceLevel.UNKNOWN,
            language_requirements={"french": "B2"},
        )
        self._job_skill(french_required_job, self.python, RequirementType.REQUIRED)
        french_required = QuickMatchService.run_quick_match(
            session_key="quick-french-required",
            job=french_required_job,
            entered_skills=["Python"],
            experience_level="junior",
            french_level="basic",
            ip_address="198.51.100.21",
        )
        self.assertIn("french_level_missing", french_required.risk_flags_json)
        self.assertLess(french_required.estimated_fit_score, optional.estimated_fit_score)

        english_required_job = self._job(
            "quick-english-required",
            "English required",
            experience_level=ExperienceLevel.UNKNOWN,
            language_requirements={"english": {"required": True}},
        )
        self._job_skill(english_required_job, self.python, RequirementType.REQUIRED)
        # English required job: omitted English level means "not assessed"
        # and must NOT penalize the candidate.
        english_required_omitted = QuickMatchService.run_quick_match(
            session_key="quick-english-required-omitted",
            job=english_required_job,
            entered_skills=["Python"],
            experience_level="junior",
            french_level="fluent",
            english_level="",
            ip_address="198.51.100.220",
        )
        self.assertNotIn("english_level_missing", english_required_omitted.risk_flags_json)
        # Explicit insufficient English ("none") on a required-English job must warn and penalize.
        english_required = QuickMatchService.run_quick_match(
            session_key="quick-english-required",
            job=english_required_job,
            entered_skills=["Python"],
            experience_level="junior",
            french_level="fluent",
            english_level="none",
            ip_address="198.51.100.22",
        )
        self.assertIn("english_level_missing", english_required.risk_flags_json)
        # Fluent English on a required-English job must NOT warn, even if a level
        # threshold is required.
        english_fluent = QuickMatchService.run_quick_match(
            session_key="quick-english-fluent",
            job=english_required_job,
            entered_skills=["Python"],
            experience_level="junior",
            french_level="fluent",
            english_level="fluent",
            ip_address="198.51.100.23",
        )
        self.assertNotIn("english_level_missing", english_fluent.risk_flags_json)

    def test_quick_match_uses_aliases_and_records_unknown_skills(self):
        dotnet = self._skill(".NET", SkillCategory.BACKEND)
        SkillAlias.objects.create(skill=dotnet, alias=".NET Core", normalized_alias=".net core")
        job = self._job("quick-dotnet", ".NET Developer")
        self._job_skill(job, dotnet, RequirementType.REQUIRED)

        session = QuickMatchService.run_quick_match(
            session_key="alias-session",
            job=job,
            entered_skills=[".NET Core", "Mystery Stack"],
            experience_level="mid_level",
            french_level="intermediate",
            ip_address="127.0.0.9",
        )

        self.assertIn({"name": ".NET", "type": "required"}, session.matched_skills_json)
        self.assertTrue(
            UnmatchedSkillCandidate.objects.filter(
                normalized_text="mystery stack",
                source_type="quick_match",
                status="pending",
            ).exists()
        )

    def test_quick_match_required_c2_satisfied_by_fluent_candidate(self):
        # Defect 1 — Quick Match end-to-end C2 coverage. The UI labels fluent
        # as "Fluent / Native (C2)", so a required C2 + fluent candidate must
        # NOT raise english_level_missing; advanced must raise it.
        c2_job = self._job(
            "quick-c2-english",
            "C2 English",
            experience_level=ExperienceLevel.UNKNOWN,
            language_requirements={"english": "C2"},
        )
        self._job_skill(c2_job, self.python, RequirementType.REQUIRED)

        fluent_session = QuickMatchService.run_quick_match(
            session_key="quick-c2-fluent",
            job=c2_job,
            entered_skills=["Python"],
            experience_level="junior",
            french_level="intermediate",
            english_level="fluent",
            ip_address="198.51.100.40",
        )
        self.assertNotIn("english_level_missing", fluent_session.risk_flags_json)

        advanced_session = QuickMatchService.run_quick_match(
            session_key="quick-c2-advanced",
            job=c2_job,
            entered_skills=["Python"],
            experience_level="junior",
            french_level="intermediate",
            english_level="advanced",
            ip_address="198.51.100.41",
        )
        self.assertIn("english_level_missing", advanced_session.risk_flags_json)
        self.assertLess(
            advanced_session.estimated_fit_score,
            fluent_session.estimated_fit_score,
        )

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

    def test_quick_match_view_passes_english_level_to_service(self):
        english_required_job = self._job(
            "quick-english-view",
            "English required",
            experience_level=ExperienceLevel.UNKNOWN,
            language_requirements={"english": {"required": True}},
        )
        self._job_skill(english_required_job, self.python, RequirementType.REQUIRED)

        url = reverse("matching:quick_match", kwargs={"public_id": english_required_job.public_id})
        # Explicit insufficient English — should be flagged and penalized.
        insufficient_response = self.client.post(
            url,
            {
                "skills": "Python",
                "experience_level": "junior",
                "french_level": "intermediate",
                "english_level": "none",
            },
        )
        self.assertEqual(insufficient_response.status_code, 200)
        session = QuickMatchSession.objects.order_by("-id").first()
        self.assertIn("english_level_missing", session.risk_flags_json)
        self.assertContains(
            insufficient_response,
            "anglais requis non atteint",
        )

        # Fluent English — no warning and no penalty.
        fluent_response = self.client.post(
            url,
            {
                "skills": "Python",
                "experience_level": "junior",
                "french_level": "intermediate",
                "english_level": "fluent",
            },
        )
        self.assertEqual(fluent_response.status_code, 200)
        fluent_session = QuickMatchSession.objects.order_by("-id").first()
        self.assertNotIn("english_level_missing", fluent_session.risk_flags_json)
        self.assertGreater(
            fluent_session.estimated_fit_score,
            session.estimated_fit_score,
        )

        # Omitted English — not assessed, no penalty.
        omitted_response = self.client.post(
            url,
            {
                "skills": "Python",
                "experience_level": "junior",
                "french_level": "intermediate",
            },
        )
        self.assertEqual(omitted_response.status_code, 200)
        omitted_session = QuickMatchSession.objects.order_by("-id").first()
        self.assertNotIn("english_level_missing", omitted_session.risk_flags_json)

    def test_quick_match_form_has_optional_english_level_field(self):
        from apps.matching.forms import QuickMatchForm

        form = QuickMatchForm()
        self.assertIn("english_level", form.fields)
        self.assertFalse(form.fields["english_level"].required)

        # Empty english_level means "not assessed", not "insufficient".
        valid = QuickMatchForm({
            "skills": "Python",
            "experience_level": "junior",
            "french_level": "intermediate",
            "english_level": "",
        })
        self.assertTrue(valid.is_valid(), valid.errors)
        self.assertEqual(valid.cleaned_data["english_level"], "")

        explicit = QuickMatchForm({
            "skills": "Python",
            "experience_level": "junior",
            "french_level": "intermediate",
            "english_level": "fluent",
        })
        self.assertTrue(explicit.is_valid(), explicit.errors)
        self.assertEqual(explicit.cleaned_data["english_level"], "fluent")

    def test_quick_match_optional_skills_renderYellow_classes(self):
        # Blocker 3: optional missing skills must not use red badge classes.
        kafka = self._skill("Kafka", SkillCategory.BACKEND)
        job = self._job(
            "quick-optional-styling",
            "Backend Developer",
            language_requirements={},
        )
        self._job_skill(job, self.python, RequirementType.REQUIRED)
        self._job_skill(job, kafka, RequirementType.OPTIONAL)
        session = QuickMatchService.run_quick_match(
            session_key="quick-optional-styling-session",
            job=job,
            entered_skills=["Python"],
            experience_level="mid",
            french_level="intermediate",
            english_level="",
            ip_address="127.0.0.10",
        )
        missing_optional = next(
            (s for s in session.missing_skills_json if s.get("requirement_type") == "optional"),
            None,
        )
        self.assertIsNotNone(missing_optional)
        self.assertEqual(missing_optional["name"], "Kafka")

        from django.template.loader import render_to_string
        html = render_to_string(
            "matching/partials/quick_match_result.html", {"session": session}
        )
        self.assertIn("Kafka", html)
        self.assertIn("(Optionnel)", html)
        self.assertIn("badge badge-yellow", html)
        self.assertIn("data-optional-skill", html)
        # Optional missing skills must NOT render red badge classes.
        optional_fragment = html.split("data-optional-skill", 1)[1].split("</span>", 1)[0]
        self.assertNotIn("badge badge-red", optional_fragment)
        self.assertNotIn("border border-red-200", optional_fragment)
        self.assertNotIn("text-red-500", optional_fragment)

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

        self.assertContains(response, "Données insuffisantes")
        self.assertNotContains(response, "Fit Global")
        self.assertNotContains(response, "Technique")
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

        self.assertContains(response, "À vérifier")
        self.assertContains(response, "Signal technique insuffisant")
        self.assertNotContains(response, "no_required_skills_extracted")

    def test_match_detail_action_buttons_use_external_apply_once(self):
        self.job.source_url = "https://example.test/external-apply"
        self.job.save(update_fields=["source_url"])
        match = MatchResultService.create_match_result(self.user, self.job)

        self.client.login(email="candidate@example.test", password="password")
        response = self.client.get(reverse("matching:detail", kwargs={"public_id": match.public_id}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="https://example.test/external-apply"', html=False)
        self.assertContains(response, 'target="_blank" rel="noopener noreferrer"', html=False)
        self.assertEqual(response.content.decode().count('data-i18n="Apply">Postuler</a>'), 1)
        self.assertContains(response, 'class="grid match-actions"', html=False)
        self.assertContains(response, 'class="btn save full"', html=False)
        self.assertContains(response, 'data-i18n="Save"', html=False)
        self.assertContains(response, 'data-i18n="Back to job">Retour à l\'offre</a>', html=False)
        self.assertContains(response, 'data-i18n="Fit summary">Résumé du fit</h2>', html=False)
        self.assertContains(response, 'data-i18n="Strong">Fort</b>', html=False)
        self.assertContains(response, 'data-i18n="Gap">Écart</b>', html=False)
        summary_html = response.content.decode().split('data-i18n="Fit summary"', 1)[1]
        self.assertNotIn('data-i18n="Apply">Postuler</a>', summary_html)
        self.assertNotContains(response, "Voir l'offre")

    def test_match_detail_hides_apply_without_source_url(self):
        self.job.source_url = ""
        self.job.save(update_fields=["source_url"])
        match = MatchResultService.create_match_result(self.user, self.job)

        self.client.login(email="candidate@example.test", password="password")
        response = self.client.get(reverse("matching:detail", kwargs={"public_id": match.public_id}))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'data-i18n="Apply">Postuler</a>', html=False)
        self.assertNotContains(response, "Voir l'offre")


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

    def test_location_affects_final_score(self):
        self.job.skill_signal_quality = "strong"
        self.job.classification_json = {"confidence": "high", "family": "software_development"}
        self.job.save(update_fields=["skill_signal_quality", "classification_json"])

        with (
            patch.object(MatchScoringService, "_calc_technical_score", return_value=(50, [], [], [])),
            patch.object(MatchScoringService, "_calc_experience_score", return_value=50),
            patch.object(MatchScoringService, "_calc_role_title_score", return_value=50),
            patch.object(MatchScoringService, "_calc_language_score", return_value=50),
            patch.object(MatchScoringService, "_calc_location_score", side_effect=[0, 100]),
        ):
            res1 = MatchScoringService.calculate(self.profile, self.job)
            res2 = MatchScoringService.calculate(self.profile, self.job)

        self.assertNotEqual(res1.location_score, res2.location_score)
        self.assertNotEqual(res1.fit_score, res2.fit_score)
        self.assertEqual(res1.fit_score, 45)
        self.assertEqual(res2.fit_score, 55)



    def test_actions_recommended_copy_is_french(self):
        res = MatchScoringService.calculate(self.profile, self.job)
        actions = res.recommended_actions
        self.assertTrue(any("Priorité : ajoutez" in action for action in actions))

        # Test when no required skills missing
        ProfileSkill.objects.create(profile=self.profile, raw_name="Angular", normalized_name="angular", skill=self.skill_angular)
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

        self.assertNotContains(response, "Localisation")
        self.assertContains(response, "Fit summary")
        self.assertContains(response, "Strong")
        self.assertContains(response, "Gap")
        self.assertContains(response, "Good language fit")
        self.assertContains(response, "Backend gap")
        self.assertNotContains(response, "Score détaillé")
        self.assertNotContains(response, "Rôle/titre")
        self.assertContains(response, "Angular")
        self.assertNotContains(response, "Compétences obligatoires non détectées")
        self.assertNotContains(response, "À renforcer")
        self.assertContains(response, "Actions recommandées")
        self.assertContains(response, "Mobilité / contrat")
        self.assertContains(response, "Vérifiez la localisation")

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

    def test_human_risk_flags_renders_points_de_vigilance_and_human_readable_labels(self):
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
            risk_flags_json=["job_may_be_expired"],
            profile_signals_json=[],
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse("matching:detail", kwargs={"public_id": match.public_id}))

        self.assertContains(response, "Points de vigilance")
        self.assertContains(response, "Offre possiblement expirée")
        self.assertNotContains(response, "job_may_be_expired")

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


class Phase16FFeedbackTests(TestCase):
    def setUp(self):
        from apps.matching.models import MatchQualityFeedback, MatchQualityIssue
        self.user = UserModel.objects.create_user(username="reviewer", email="reviewer@example.com", password="password")
        self.profile = CandidateProfile.objects.create(
            user=self.user,
            years_experience=3.0,
            current_level="mid",
            french_level="c1",
            profile_completion_score=100
        )
        now = timezone.now()
        source = JobSource.objects.create(name="test", slug="test", source_type="fixture")
        raw = RawJobRecord.objects.create(source=source, source_job_id="test2", payload_hash="test2", first_seen_at=now, last_seen_at=now, last_fetched_at=now, raw_payload_json={})
        self.job = NormalizedJob.objects.create(
            source=source,
            raw_record=raw,
            source_job_id="test2",
            first_seen_at=now,
            last_seen_at=now,
            last_fetched_at=now,
            public_id="11111111-1111-1111-1111-111111111111",
            title="Dev",
            status="active",
        )
        self.match = MatchResult.objects.create(
            user=self.user,
            profile=self.profile,
            job=self.job,
            fit_score=50,
            technical_skills_score=50,
            experience_score=50,
            role_title_score=50,
            language_score=50,
            location_score=50,
        )

    def test_match_quality_feedback_creation(self):
        from apps.matching.models import MatchQualityFeedback, MatchQualityIssue
        feedback = MatchQualityFeedback.objects.create(
            match_result=self.match,
            reason=MatchQualityIssue.MISSING_KEY_SKILL,
            notes="Missing React",
            reviewed_by=self.user
        )
        self.assertEqual(feedback.reason, MatchQualityIssue.MISSING_KEY_SKILL)
        self.assertEqual(self.match.quality_feedback.count(), 1)

    def test_match_feedback_service_rejects_invalid_reason(self):
        with self.assertRaises(ValidationError):
            MatchFeedbackService.record_feedback(
                self.user,
                self.match.public_id,
                "not_a_valid_reason",
                "bad value",
            )

        self.assertEqual(self.match.quality_feedback.count(), 0)

    def test_match_feedback_view_uses_public_id_and_owner_filter(self):
        from apps.matching.models import MatchQualityFeedback, MatchQualityIssue

        other_user = UserModel.objects.create_user(
            username="other_reviewer",
            email="other_reviewer@example.com",
            password="password",
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("matching:feedback", kwargs={"public_id": self.match.public_id}),
            {"reason": MatchQualityIssue.GOOD_MATCH, "notes": "useful"},
        )

        self.assertRedirects(response, reverse("matching:detail", kwargs={"public_id": self.match.public_id}))
        self.assertTrue(
            MatchQualityFeedback.objects.filter(
                match_result=self.match,
                reason=MatchQualityIssue.GOOD_MATCH,
                reviewed_by=self.user,
            ).exists()
        )

        self.client.force_login(other_user)
        response = self.client.post(
            reverse("matching:feedback", kwargs={"public_id": self.match.public_id}),
            {"reason": MatchQualityIssue.GOOD_MATCH},
        )
        self.assertEqual(response.status_code, 404)


class MatchRowIdentityTests(TestCase):
    """Blocker 4 — preserve object identity and deterministic history behavior."""

    def setUp(self):
        self.user = create_test_user(
            username="identity-user", email="identity@example.test", password="password"
        )
        self.other_user = create_test_user(
            username="identity-other", email="identity-other@example.test", password="password"
        )
        self.profile = CandidateProfile.objects.create(
            user=self.user,
            years_experience=3.0,
            current_level="mid",
            target_country="France",
            target_roles=["Backend Developer"],
            french_level="intermediate",
            english_level="fluent",
            profile_completion_score=100,
        )
        CandidateProfile.objects.create(
            user=self.other_user,
            years_experience=1.0,
            current_level="junior",
            french_level="basic",
            profile_completion_score=80,
        )
        self.source = JobSource.objects.create(
            name="Identity", slug="identity", source_type=SourceType.FIXTURE
        )
        self.job_one = self._job("identity-job-one", "Backend Developer Python")
        self.job_two = self._job("identity-job-two", "Backend Developer Go")

    def _job(self, source_job_id, title):
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
            country="France",
            remote_type=RemoteType.HYBRID,
            job_type=JobType.FULL_TIME_JOB,
            experience_level=ExperienceLevel.MID_LEVEL,
            status=JobStatus.ACTIVE,
            description="Build backend systems.",
            required_skills_json=["Python"],
            optional_skills_json=[],
            language_requirements_json={},
            classification_json={"family": "software_development", "is_it": True, "confidence": "high"},
            skill_signal_quality="strong",
            first_seen_at=now,
            last_seen_at=now,
            last_fetched_at=now,
        )

    def _make_match(self, *, user, profile, job, scoring_version, snapshot=None):
        snapshot = snapshot if snapshot is not None else MatchResultService._profile_snapshot(profile)
        return MatchResult.objects.create(
            user=user,
            profile=profile,
            job=job,
            profile_snapshot_json=snapshot,
            job_snapshot_json={"title": job.title, "company_name": "Test"},
            fit_score=50,
            technical_skills_score=50,
            experience_score=50,
            role_title_score=50,
            language_score=50,
            location_score=50,
            scoring_version=scoring_version,
        )

    @staticmethod
    def _public_ids(matches):
        return [str(m.public_id) for m in matches]

    def test_history_has_no_duplicate_public_ids_with_mixed_versions(self):
        latest = self._make_match(
            user=self.user, profile=self.profile, job=self.job_one,
            scoring_version=MATCH_SCORING_VERSION,
        )
        older = self._make_match(
            user=self.user, profile=self.profile, job=self.job_one,
            scoring_version="score_v1",
        )

        history = MatchResultService.list_user_matches(self.user)

        ids = self._public_ids(history)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertIn(str(latest.public_id), ids)
        self.assertIn(str(older.public_id), ids)
        # History must return rows in reverse-created order.
        ordered_db = [
            str(m.public_id)
            for m in MatchResult.objects.filter(user=self.user).order_by("-created_at")
        ]
        self.assertEqual(ids, ordered_db)

    def test_history_does_not_call_refresh_if_stale(self):
        # Defect 2 — list_user_matches must be read-only and never trigger
        # refresh_if_stale / _recompute_in_place / update_current_match_for_job.
        stale = self._make_match(
            user=self.user, profile=self.profile, job=self.job_one,
            scoring_version="score_v1",
        )
        with (
            patch.object(MatchResultService, "refresh_if_stale") as refresh,
            patch.object(MatchResultService, "_recompute_in_place") as recompute,
            patch.object(MatchResultService, "update_current_match_for_job") as update,
        ):
            history = MatchResultService.list_user_matches(self.user)
        refresh.assert_not_called()
        recompute.assert_not_called()
        update.assert_not_called()
        self.assertEqual([str(m.public_id) for m in history], [str(stale.public_id)])

    def test_history_does_not_mutate_scoring_version_score_snapshot_or_timestamp(self):
        stale = self._make_match(
            user=self.user, profile=self.profile, job=self.job_one,
            scoring_version="score_v1",
        )
        original_snapshot = dict(stale.profile_snapshot_json)
        original_fit = stale.fit_score
        original_version = stale.scoring_version
        original_updated = stale.updated_at

        MatchResultService.list_user_matches(self.user)
        stale.refresh_from_db()

        self.assertEqual(stale.scoring_version, original_version)
        self.assertEqual(stale.fit_score, original_fit)
        self.assertEqual(stale.profile_snapshot_json, original_snapshot)
        self.assertEqual(stale.updated_at, original_updated)

    def test_repeated_history_loads_remain_read_only(self):
        stale = self._make_match(
            user=self.user, profile=self.profile, job=self.job_one,
            scoring_version="score_v1",
        )
        original_version = stale.scoring_version
        original_updated = stale.updated_at

        for _ in range(3):
            MatchResultService.list_user_matches(self.user)
        stale.refresh_from_db()

        self.assertEqual(stale.scoring_version, original_version)
        self.assertEqual(stale.updated_at, original_updated)

    def test_get_user_match_returns_requested_public_id_when_stale(self):
        older = self._make_match(
            user=self.user, profile=self.profile, job=self.job_one,
            scoring_version="score_v1",
        )
        requested_public_id = str(older.public_id)

        refreshed = MatchResultService.get_user_match(self.user, requested_public_id)

        # The refreshed object must respect the requested public_id; refreshing
        # it in place may not surface any other row.
        self.assertEqual(str(refreshed.public_id), requested_public_id)
        self.assertEqual(refreshed.scoring_version, MATCH_SCORING_VERSION)
        self.assertTrue(MatchResult.objects.filter(public_id=requested_public_id).exists())

    def test_two_jobs_both_present_and_ordered(self):
        match_one = self._make_match(
            user=self.user, profile=self.profile, job=self.job_one,
            scoring_version="score_v1",
        )
        match_two = self._make_match(
            user=self.user, profile=self.profile, job=self.job_two,
            scoring_version="score_v1",
        )

        history = MatchResultService.list_user_matches(self.user)

        ids = self._public_ids(history)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(set(ids), {str(match_one.public_id), str(match_two.public_id)})
        # list_user_matches preserves reverse-chronological order returned by the DB.
        ordered_db = [
            str(m.public_id)
            for m in MatchResult.objects.filter(user=self.user).order_by("-created_at")
        ]
        self.assertEqual(ids, ordered_db)

    def test_selected_stale_detail_refreshes_only_that_row_in_place(self):
        # Defect 2 — opening one selected stale detail may refresh that row
        # in place, but other stale rows for the same job must remain untouched.
        stale_kept = self._make_match(
            user=self.user, profile=self.profile, job=self.job_one,
            scoring_version="score_v1",
        )
        # Slightly different snapshot for the second stale row so we can
        # verify it is NOT refreshed when the first is opened.
        other_snapshot = dict(stale_kept.profile_snapshot_json)
        other_snapshot["note"] = "other-stale-row"
        stale_other = MatchResult.objects.create(
            user=self.user,
            profile=self.profile,
            job=self.job_one,
            profile_snapshot_json=other_snapshot,
            job_snapshot_json={"title": self.job_one.title, "company_name": "Test"},
            fit_score=30,
            technical_skills_score=30,
            experience_score=30,
            role_title_score=30,
            language_score=30,
            location_score=30,
            scoring_version="score_v1",
        )

        requested_public_id = str(stale_kept.public_id)
        refreshed = MatchResultService.get_user_match(self.user, requested_public_id)

        self.assertEqual(str(refreshed.public_id), requested_public_id)
        self.assertEqual(refreshed.scoring_version, MATCH_SCORING_VERSION)

        stale_other.refresh_from_db()
        # The other stale row was not selected and must remain untouched.
        self.assertEqual(stale_other.scoring_version, "score_v1")
        self.assertEqual(stale_other.fit_score, 30)
        self.assertEqual(stale_other.profile_snapshot_json, other_snapshot)

    def test_other_user_match_remains_inaccessible(self):
        mine = self._make_match(
            user=self.user, profile=self.profile, job=self.job_one,
            scoring_version=MATCH_SCORING_VERSION,
        )

        with self.assertRaises(Http404):
            MatchResultService.get_user_match(self.other_user, str(mine.public_id))

        # And the history endpoint never leaks another user's rows.
        other_history = MatchResultService.list_user_matches(self.other_user)
        self.assertNotIn(str(mine.public_id), self._public_ids(other_history))


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class RecomputeCurrentMatchesTests(TestCase):
    def setUp(self):
        self.user = create_test_user(
            username="recomputeuser",
            email="recompute@example.test",
        )
        self.other_user = create_test_user(
            username="recomputeother",
            email="recomputeother@example.test",
        )
        self.other_profile = CandidateProfile.objects.create(
            user=self.other_user,
            years_experience=1.0,
            current_level="junior",
            target_country="France",
            target_roles=["Frontend Developer"],
            french_level="basic",
            profile_completion_score=60,
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
        self.python = Skill.objects.create(
            canonical_name="Python",
            slug="python",
            category=SkillCategory.PROGRAMMING_LANGUAGE,
            is_active=True,
        )
        SkillAlias.objects.create(
            skill=self.python, alias="Python", normalized_alias="python"
        )
        ProfileSkill.objects.create(
            profile=self.profile,
            raw_name="Python",
            normalized_name="python",
            skill=self.python,
        )

        self.source = JobSource.objects.create(
            name="France Travail",
            slug="france-travail-recompute",
            source_type=SourceType.FIXTURE,
        )
        self.job_one = self._job("recompute-1", "Backend Developer")
        self.job_two = self._job("recompute-2", "Python Engineer")

    def _job(self, source_job_id, title):
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
            country="France",
            city="Paris",
            contract_type="CDI",
            remote_type=RemoteType.HYBRID,
            job_type=JobType.FULL_TIME_JOB,
            experience_level=ExperienceLevel.MID_LEVEL,
            description="Build backend systems.",
            status=JobStatus.ACTIVE,
            required_skills_json=["Python"],
            optional_skills_json=[],
            language_requirements_json={},
            classification_json={
                "family": "software_development",
                "is_it": True,
                "confidence": "high",
            },
            first_seen_at=now,
            last_seen_at=now,
            last_fetched_at=now,
        )

    def test_recompute_only_latest_row_per_user_job(self):
        first = MatchResultService.create_match_result(self.user, self.job_one)
        second = MatchResultService.create_match_result(self.user, self.job_one)
        other_job_match = MatchResultService.create_match_result(self.user, self.job_two)
        other_user_match = MatchResultService.create_match_result(self.other_user, self.job_one)

        first_updated = first.updated_at
        second_updated = second.updated_at
        other_job_updated = other_job_match.updated_at
        other_user_updated = other_user_match.updated_at

        refreshed_count = MatchResultService.recompute_current_matches_for_user(self.user)
        self.assertEqual(refreshed_count, 2)

        first.refresh_from_db()
        second.refresh_from_db()
        other_job_match.refresh_from_db()
        other_user_match.refresh_from_db()

        # Historical row (first) must stay unchanged.
        self.assertEqual(first.updated_at, first_updated)
        # Latest row per user/job must be recomputed.
        self.assertGreater(second.updated_at, second_updated)
        self.assertGreater(other_job_match.updated_at, other_job_updated)
        # Other user's row must not be touched.
        self.assertEqual(other_user_match.updated_at, other_user_updated)
