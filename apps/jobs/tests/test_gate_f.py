import re

from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.jobs.models import (
    JobSource,
    JobStatus,
    NormalizedJob,
    NormalizedJobSkill,
    RawJobRecord,
    RequirementType,
    SkillSource,
    SourceType,
)
from apps.jobs.services.presentation import JobPresentationService
from apps.jobs.services.language_requirements import (
    LanguageRequirement,
    LanguageRequirementClassifier,
    LanguageRequirementKind,
)
from apps.jobs.services.search import JobSearchService
from apps.jobs.services.search_vector import JobSearchVectorService
from apps.matching.models import MatchResult, QuickMatchSession, human_risk_labels
from apps.matching.services.match_result import MatchResultService
from apps.matching.services.policy_version import MATCH_SCORING_VERSION
from apps.matching.services.presentation import MatchPresentationService
from apps.matching.services.scoring import MatchScoringService
from apps.profiles.models import CandidateProfile
from apps.recommendations.models import JobRecommendation, SavedJob
from apps.recommendations.services.staleness import RecommendationStalenessService
from apps.skills.models import Skill, SkillCategory
from apps.skills.services.extraction_policy import SkillCandidateKind, classify_skill_candidate


User = get_user_model()


class GateFSkillPolicyTests(TestCase):
    @staticmethod
    def make_job(source, key, **kwargs):
        now = timezone.now()
        raw = RawJobRecord.objects.create(
            source=source, source_job_id=key, raw_payload_json={}, payload_hash=f"hash-{key}",
            first_seen_at=now, last_seen_at=now, last_fetched_at=now,
        )
        return NormalizedJob.objects.create(
            source=source, raw_record=raw, source_job_id=key,
            first_seen_at=now, last_seen_at=now, last_fetched_at=now, **kwargs,
        )

    def test_role_broad_and_concrete_skill_policy(self):
        broad_or_roles = {
            "Artificial Intelligence": SkillCandidateKind.BROAD_TECHNICAL,
            "DevOps": SkillCandidateKind.BROAD_TECHNICAL,
            "Windows": SkillCandidateKind.BROAD_TECHNICAL,
            "Data Engineer": SkillCandidateKind.REJECTED_NOISE,
            "Network Engineer": SkillCandidateKind.REJECTED_NOISE,
            "API": SkillCandidateKind.BROAD_TECHNICAL,
            "Monitoring": SkillCandidateKind.BROAD_TECHNICAL,
            "Software Development": SkillCandidateKind.BROAD_TECHNICAL,
        }
        for name, kind in broad_or_roles.items():
            with self.subTest(name=name):
                decision = classify_skill_candidate(raw_text=name, canonical_name=name, category=SkillCategory.OTHER)
                self.assertEqual(decision.kind, kind)
                self.assertFalse(decision.can_be_required)

        for name in ("Data Modeling", "dbt", "Active Directory", "TCP/IP", "Machine Learning", "PostgreSQL"):
            with self.subTest(name=name):
                decision = classify_skill_candidate(raw_text=name, canonical_name=name, category=SkillCategory.OTHER)
                self.assertEqual(decision.kind, SkillCandidateKind.HARD_TECHNICAL)
                self.assertTrue(decision.can_be_required)

    def test_presenter_and_scoring_exclude_roles_broad_signals_and_unknown_language(self):
        source = JobSource.objects.create(name="Gate F", slug="gate-f-policy", source_type=SourceType.FIXTURE)
        job = self.make_job(
            source, "policy",
            title="Data role",
            status=JobStatus.ACTIVE,
            skill_signal_quality="strong",
            classification_json={"is_it": True, "confidence": "high"},
        )
        names = [
            "Artificial Intelligence", "DevOps", "Data Engineer", "Network Engineer", "Windows",
            "API", "Monitoring", "Software Development", "Langues non précisées",
            "Data Modeling", "dbt", "Active Directory", "TCP/IP",
        ]
        for index, name in enumerate(names):
            skill = Skill.objects.create(canonical_name=name, slug=f"gate-f-{index}", category=SkillCategory.TOOLS)
            NormalizedJobSkill.objects.create(
                job=job, skill=skill, requirement_type=RequirementType.REQUIRED,
                source=SkillSource.ADMIN, confidence=1,
            )

        visible = [entry["name"] for entry in JobPresentationService.get_user_facing_skill_entries(job)]
        self.assertEqual(visible, ["Active Directory", "Data Modeling", "dbt", "TCP/IP"])

        user = User.objects.create_user(username="gate-f-score", email="gate-f-score@example.test")
        profile = CandidateProfile.objects.create(user=user, profile_completion_score=100)
        result = MatchScoringService.calculate(profile, job)
        self.assertEqual(
            [row["name"] for row in result.missing_required_skills],
            ["Active Directory", "Data Modeling", "dbt", "TCP/IP"],
        )

    def test_insufficient_experience_remains_warning_not_missing_skill(self):
        self.assertEqual(human_risk_labels(["experience_too_low"]), ["Expérience insuffisante"])
        source = JobSource.objects.create(name="Gate F warning", slug="gate-f-warning", source_type=SourceType.FIXTURE)
        job = self.make_job(source, "warning", title="Warning job", status=JobStatus.ACTIVE)
        template = render_to_string(
            "recommendations/partials/recommendation_card.html",
            {"rec": type("Rec", (), {
                "job": job,
                "strong_skills_json": [], "missing_skills_json": [], "risk_flags_json": ["experience_too_low"],
                "fit_score": 50, "reason_summary": "", "is_match_low_confidence": False, "is_saved": False,
            })()},
        )
        self.assertIn('<span class="pill warn">Expérience insuffisante</span>', template)
        self.assertNotIn('<span class="skill missing">Expérience insuffisante</span>', template)

    def test_user_risks_suppress_unknown_language_but_keep_explicit_requirement(self):
        source = JobSource.objects.create(name="Gate F risks", slug="gate-f-risks", source_type=SourceType.FIXTURE)
        unspecified = self.make_job(source, "risk-unspecified", title="Unspecified", status=JobStatus.ACTIVE)
        subject = type("Subject", (), {
            "job": unspecified,
            "risk_flags_json": [
                "job_language_unknown", "french_level_missing", "english_level_missing", "experience_too_low"
            ],
        })()
        self.assertEqual(
            MatchPresentationService.get_user_facing_risk_labels(subject),
            ["Expérience insuffisante"],
        )

        explicit = self.make_job(
            source,
            "risk-explicit",
            title="Explicit",
            status=JobStatus.ACTIVE,
            language_requirements_json={"french": "B2"},
        )
        subject.job = explicit
        self.assertEqual(
            MatchPresentationService.get_user_facing_risk_labels(subject),
            ["Niveau de français requis non atteint", "Expérience insuffisante"],
        )

        explicit.language_requirements_json = {"french": "optional", "english": "preferred"}
        self.assertEqual(
            MatchPresentationService.get_user_facing_risk_labels(subject),
            ["Expérience insuffisante"],
        )

    def test_language_classifier_covers_ingestion_and_enrichment_representations(self):
        cases = (
            ({"english": "required"}, "english", LanguageRequirementKind.REQUIRED),
            ({"english": "optional"}, "english", LanguageRequirementKind.OPTIONAL),
            ({"english": False}, "english", LanguageRequirementKind.OPTIONAL),
            ({"english": "required=false"}, "english", LanguageRequirementKind.OPTIONAL),
            ({"english": {"required": False, "level": "B2"}}, "english", LanguageRequirementKind.OPTIONAL),
            ({"english": {"required": "false", "level": "B2"}}, "english", LanguageRequirementKind.OPTIONAL),
            ({"english": {"requirement_type": "optional", "level": "C1"}}, "english", LanguageRequirementKind.OPTIONAL),
            ({"french": "B2"}, "french", LanguageRequirementKind.REQUIRED),
            ([{"language": "French", "level": "required"}], "french", LanguageRequirementKind.REQUIRED),
            ([{"language": "English", "level": "nice to have"}], "english", LanguageRequirementKind.OPTIONAL),
            ({"french": "unknown"}, "french", LanguageRequirementKind.UNSPECIFIED),
        )
        for requirements, language, expected in cases:
            with self.subTest(requirements=requirements, language=language):
                self.assertEqual(LanguageRequirementClassifier.classify(requirements, language), expected)

    def test_language_classifier_handles_negative_and_level_expressions_correctly(self):
        cases = (
            # Blocker 1 verified failures — direct regression coverage.
            ({"english": "not required"}, "english", LanguageRequirementKind.OPTIONAL),
            ({"english": "no requirement"}, "english", LanguageRequirementKind.OPTIONAL),
            ({"english": "not mandatory"}, "english", LanguageRequirementKind.OPTIONAL),
            ({"french": "non requis"}, "french", LanguageRequirementKind.OPTIONAL),
            ({"french": "pas requis"}, "french", LanguageRequirementKind.OPTIONAL),
            ({"french": "non obligatoire"}, "french", LanguageRequirementKind.OPTIONAL),
            ({"french": "pas obligatoire"}, "french", LanguageRequirementKind.OPTIONAL),
            ({"french": "B2 ou plus"}, "french", LanguageRequirementKind.REQUIRED),
            ({"french": "B2+"}, "french", LanguageRequirementKind.REQUIRED),
            ({"french": "B2 minimum"}, "french", LanguageRequirementKind.REQUIRED),
            ({"french": "niveau B2"}, "french", LanguageRequirementKind.REQUIRED),
            ({"english": "a plus"}, "english", LanguageRequirementKind.OPTIONAL),
            ({"english": "un plus"}, "english", LanguageRequirementKind.OPTIONAL),
            ({"english": "serait un plus"}, "english", LanguageRequirementKind.OPTIONAL),
        )
        for requirements, language, expected in cases:
            with self.subTest(requirements=requirements, language=language):
                self.assertEqual(LanguageRequirementClassifier.classify(requirements, language), expected)

        # Bare CEFR level carries the minimum level value when REQUIRED.
        self.assertEqual(
            LanguageRequirementClassifier.get_requirement({"french": "B2 ou plus"}, "french"),
            LanguageRequirement(LanguageRequirementKind.REQUIRED, "b2"),
        )
        self.assertEqual(
            LanguageRequirementClassifier.get_requirement({"french": "B2+"}, "french"),
            LanguageRequirement(LanguageRequirementKind.REQUIRED, "b2"),
        )

    def test_language_classifier_required_false_overrides_level_within_record(self):
        # Structured required=False overrides a supplied CEFR level.
        self.assertEqual(
            LanguageRequirementClassifier.get_requirement(
                {"english": {"required": False, "level": "B2"}}, "english"
            ),
            LanguageRequirement(LanguageRequirementKind.OPTIONAL, "b2"),
        )

    def test_language_classifier_explicit_required_wins_over_earlier_optional_rep(self):
        # Duplicate representations: explicit REQUIRED must not be discarded
        # because an earlier optional/ambiguous item appeared for the same language.
        requirements = [
            {"language": "English", "level": "preferred"},
            {"language": "English", "level": "required", "minimum": "B2"},
        ]
        self.assertEqual(
            LanguageRequirementClassifier.classify(requirements, "english"),
            LanguageRequirementKind.REQUIRED,
        )

    def test_candidate_level_rank_consistent_with_ui_choices(self):
        # Defect 1 — fluent must satisfy required C2 (UI: "Fluent / Native (C2)").
        # advanced satisfies C1 but NOT C2. intermediate satisfies B2 but NOT C1.
        # basic satisfies A2 but NOT B1. Unknown values remain insufficient.
        c2_required = LanguageRequirement(LanguageRequirementKind.REQUIRED, "c2")
        c1_required = LanguageRequirement(LanguageRequirementKind.REQUIRED, "c1")
        b2_required = LanguageRequirement(LanguageRequirementKind.REQUIRED, "b2")
        b1_required = LanguageRequirement(LanguageRequirementKind.REQUIRED, "b1")

        self.assertTrue(LanguageRequirementClassifier.candidate_meets(c2_required, "fluent"))
        self.assertTrue(LanguageRequirementClassifier.candidate_meets(c2_required, "native"))
        self.assertFalse(LanguageRequirementClassifier.candidate_meets(c2_required, "advanced"))
        self.assertTrue(LanguageRequirementClassifier.candidate_meets(c1_required, "advanced"))
        self.assertFalse(LanguageRequirementClassifier.candidate_meets(c1_required, "intermediate"))
        self.assertTrue(LanguageRequirementClassifier.candidate_meets(b2_required, "intermediate"))
        self.assertFalse(LanguageRequirementClassifier.candidate_meets(b1_required, "basic"))
        # Unknown/unrecognized candidate values must remain insufficient.
        self.assertFalse(LanguageRequirementClassifier.candidate_meets(c2_required, "telepathic"))
        self.assertFalse(LanguageRequirementClassifier.candidate_meets(c2_required, ""))
        self.assertFalse(LanguageRequirementClassifier.candidate_meets(c2_required, "none"))

    def test_negative_language_phrases_classify_correctly(self):
        # Defect 1 — negative phrase hardening. Use targeted patterns instead
        # of broad substring rules so negated phrases don't reverse meanings.
        cases = (
            ({"english": "no English required"}, "english", LanguageRequirementKind.OPTIONAL),
            ({"french": "no French required"}, "french", LanguageRequirementKind.OPTIONAL),
            ({"english": "not optional"}, "english", LanguageRequirementKind.REQUIRED),
            ({"english": "non facultatif"}, "english", LanguageRequirementKind.REQUIRED),
            ({"french": "pas facultatif"}, "french", LanguageRequirementKind.REQUIRED),
            # Keep all previously passing cases.
            ({"english": "not required"}, "english", LanguageRequirementKind.OPTIONAL),
            ({"english": "no requirement"}, "english", LanguageRequirementKind.OPTIONAL),
            ({"french": "B2 ou plus"}, "french", LanguageRequirementKind.REQUIRED),
            ({"french": "B2+"}, "french", LanguageRequirementKind.REQUIRED),
            ({"english": "a plus"}, "english", LanguageRequirementKind.OPTIONAL),
        )
        for requirements, language, expected in cases:
            with self.subTest(requirements=requirements, language=language):
                self.assertEqual(
                    LanguageRequirementClassifier.classify(requirements, language),
                    expected,
                )

    def test_full_matching_required_c2_satisfied_by_fluent_candidate(self):
        # End-to-end full-matching coverage: required C2 + fluent candidate
        # must NOT raise english_level_missing; advanced must raise it.
        source = JobSource.objects.create(
            name="Gate F C2", slug="gate-f-c2", source_type=SourceType.FIXTURE
        )
        fluent_profile = CandidateProfile.objects.create(
            user=User.objects.create_user(
                username="gate-f-c2-fluent", email="gate-f-c2-fluent@example.test"
            ),
            years_experience=1,
            current_level="junior",
            french_level="",
            english_level="fluent",
            profile_completion_score=100,
        )
        advanced_profile = CandidateProfile.objects.create(
            user=User.objects.create_user(
                username="gate-f-c2-advanced", email="gate-f-c2-advanced@example.test"
            ),
            years_experience=1,
            current_level="junior",
            french_level="",
            english_level="advanced",
            profile_completion_score=100,
        )
        job = self.make_job(
            source,
            "c2-english",
            title="C2 English",
            status=JobStatus.ACTIVE,
            language_requirements_json={"english": "C2"},
        )

        fluent_result = MatchScoringService.calculate(fluent_profile, job)
        self.assertNotIn("english_level_missing", fluent_result.risk_flags)
        self.assertEqual(fluent_result.language_score, 100)

        advanced_result = MatchScoringService.calculate(advanced_profile, job)
        self.assertIn("english_level_missing", advanced_result.risk_flags)
        self.assertLess(advanced_result.language_score, 100)

    def test_unknown_experience_and_non_required_languages_are_neutral(self):
        source = JobSource.objects.create(name="Gate F neutral", slug="gate-f-neutral", source_type=SourceType.FIXTURE)
        user = User.objects.create_user(username="gate-f-neutral", email="gate-f-neutral@example.test")
        profile = CandidateProfile.objects.create(
            user=user,
            years_experience=1,
            current_level="junior",
            french_level="",
            english_level="",
            profile_completion_score=100,
        )
        job = self.make_job(
            source,
            "neutral",
            title="Neutral metadata",
            country="France",
            status=JobStatus.ACTIVE,
            experience_level="unknown",
            language_requirements_json={"french": "optional", "english": "preferred"},
            skill_signal_quality="strong",
            classification_json={"is_it": True, "confidence": "high"},
        )
        result = MatchScoringService.calculate(profile, job)
        self.assertEqual(result.experience_score, 100)
        self.assertEqual(result.language_score, 100)
        self.assertIn("experience_unknown", result.risk_flags)
        self.assertNotIn("french_level_missing", result.risk_flags)
        self.assertNotIn("english_level_missing", result.risk_flags)
        subject = type("Subject", (), {"job": job, "risk_flags_json": result.risk_flags})()
        self.assertNotIn("Expérience non précisée", MatchPresentationService.get_user_facing_risk_labels(subject))

    def test_only_explicit_required_languages_warn_and_penalize(self):
        source = JobSource.objects.create(name="Gate F required language", slug="gate-f-required-language", source_type=SourceType.FIXTURE)
        user = User.objects.create_user(username="gate-f-required-language", email="gate-f-required-language@example.test")
        profile = CandidateProfile.objects.create(
            user=user,
            years_experience=1,
            current_level="junior",
            french_level="basic",
            english_level="",
            profile_completion_score=100,
        )
        english_job = self.make_job(
            source, "english-required", title="English required", status=JobStatus.ACTIVE,
            language_requirements_json={"english": "required"},
        )
        english = MatchScoringService.calculate(profile, english_job)
        self.assertEqual(english.language_score, 60)
        self.assertIn("english_level_missing", english.risk_flags)

        french_job = self.make_job(
            source, "french-required", title="French required", status=JobStatus.ACTIVE,
            language_requirements_json={"french": "B2"},
        )
        french = MatchScoringService.calculate(profile, french_job)
        self.assertEqual(french.language_score, 60)
        self.assertIn("french_level_missing", french.risk_flags)

        no_language_job = self.make_job(
            source, "no-language", title="No language", country="France", status=JobStatus.ACTIVE,
            language_requirements_json={},
        )
        no_language = MatchScoringService.calculate(profile, no_language_job)
        self.assertEqual(no_language.language_score, 100)
        self.assertNotIn("french_level_missing", no_language.risk_flags)

    def test_quick_match_uses_canonical_skills_and_contextual_risks(self):
        source = JobSource.objects.create(name="Gate F quick", slug="gate-f-quick", source_type=SourceType.FIXTURE)
        job = self.make_job(source, "quick", title="Quick", status=JobStatus.ACTIVE)
        for index, name in enumerate(("PostgreSQL", "DevOps", "Langues non précisées")):
            skill = Skill.objects.create(canonical_name=name, slug=f"quick-{index}", category=SkillCategory.TOOLS)
            NormalizedJobSkill.objects.create(
                job=job, skill=skill, requirement_type=RequirementType.REQUIRED,
                source=SkillSource.ADMIN, confidence=1,
            )
        session = QuickMatchSession(
            job=job,
            estimated_fit_score=50,
            matched_skills_json=[],
            missing_skills_json=[
                {"name": "PostgreSQL", "requirement_type": "required"},
                {"name": "DevOps", "requirement_type": "required"},
                {"name": "Langues non précisées", "requirement_type": "required"},
            ],
            risk_flags_json=["job_language_unknown", "french_level_missing", "experience_unknown"],
        )
        html = render_to_string("matching/partials/quick_match_result.html", {"session": session})
        self.assertIn("PostgreSQL", html)
        self.assertNotIn("DevOps", html)
        self.assertNotIn("Langues non précisées", html)
        self.assertNotIn("Expérience non précisée", html)

        job.language_requirements_json = {"french": "B2"}
        html = render_to_string("matching/partials/quick_match_result.html", {"session": session})
        self.assertIn("Niveau de français requis non atteint", html)


class GateFSearchTests(TestCase):
    def setUp(self):
        self.source = JobSource.objects.create(name="Gate F Search", slug="gate-f-search", source_type=SourceType.FIXTURE)

    def make_job(self, key, title, description="", **kwargs):
        now = timezone.now()
        raw = RawJobRecord.objects.create(
            source=self.source, source_job_id=key, raw_payload_json={}, payload_hash=f"hash-{key}",
            first_seen_at=now, last_seen_at=now, last_fetched_at=now,
        )
        job = NormalizedJob.objects.create(
            source=self.source,
            raw_record=raw,
            source_job_id=key,
            title=title,
            description=description,
            status=kwargs.pop("status", JobStatus.ACTIVE),
            first_seen_at=now, last_seen_at=now, last_fetched_at=now,
            **kwargs,
        )
        JobSearchVectorService.update_search_vector(job)
        return job

    def test_bilingual_engineer_queries_return_same_french_titles(self):
        expected = {
            self.make_job("eng-1", "Ingénieur logiciel").id,
            self.make_job("eng-2", "Ingénieure systèmes").id,
        }
        english = {job.id for job in JobSearchService.search({"q": "engineer"}).page_obj}
        french = {job.id for job in JobSearchService.search({"q": "ingénieur"}).page_obj}
        self.assertEqual(english, expected)
        self.assertEqual(french, expected)

    def test_data_search_ranking_canonical_skill_visibility_and_filters(self):
        title_match = self.make_job("data-title", "Data Engineer", location="Paris", remote_type="remote")
        description_match = self.make_job("data-description", "Backend Developer", "Build reliable data pipelines", location="Paris")
        second_title = self.make_job("data-title-2", "Data Analyst", location="Lyon")
        hidden = self.make_job("data-expired", "Data Architect", status=JobStatus.EXPIRED)
        skill_only = self.make_job("skill-only", "Database specialist")
        postgres = Skill.objects.create(canonical_name="PostgreSQL", slug="gate-f-postgresql", category=SkillCategory.DATABASE)
        NormalizedJobSkill.objects.create(job=skill_only, skill=postgres, requirement_type=RequirementType.REQUIRED, source=SkillSource.ADMIN)

        result = JobSearchService.search({"q": "data"})
        ids = [job.id for job in result.page_obj]
        self.assertGreaterEqual(len(ids), 3)
        self.assertLess(ids.index(title_match.id), ids.index(description_match.id))
        self.assertIn(second_title.id, ids)
        self.assertNotIn(hidden.id, ids)

        skill_result = JobSearchService.search({"q": "PostgreSQL"})
        self.assertEqual([job.id for job in skill_result.page_obj], [skill_only.id])

        filtered = JobSearchService.search({"q": "data", "location": "Paris", "remote_type": "remote"})
        self.assertEqual([job.id for job in filtered.page_obj], [title_match.id])


class GateFCanonicalPageConsistencyTests(TestCase):
    @staticmethod
    def canonical_names(html):
        return re.findall(r'data-canonical-skill[^>]*>([^<]+)</span>', html)

    def test_same_job_uses_same_canonical_skills_on_all_four_surfaces(self):
        source = JobSource.objects.create(name="Gate F Pages", slug="gate-f-pages", source_type=SourceType.FIXTURE)
        now = timezone.now()
        raw = RawJobRecord.objects.create(
            source=source, source_job_id="pages", raw_payload_json={}, payload_hash="hash-pages",
            first_seen_at=now, last_seen_at=now, last_fetched_at=now,
        )
        job = NormalizedJob.objects.create(
            source=source, raw_record=raw, source_job_id="pages", title="Canonical pages", status=JobStatus.ACTIVE,
            language_requirements_json={"english": "optional"},
            skill_signal_quality="strong", classification_json={"is_it": True, "confidence": "high"},
            first_seen_at=now, last_seen_at=now, last_fetched_at=now,
        )
        for index, name in enumerate(("dbt", "Data Modeling", "DevOps", "Langues non précisées")):
            skill = Skill.objects.create(canonical_name=name, slug=f"page-skill-{index}", category=SkillCategory.OTHER)
            NormalizedJobSkill.objects.create(job=job, skill=skill, requirement_type=RequirementType.REQUIRED, source=SkillSource.ADMIN)

        user = User.objects.create_user(username="gate-f-pages", email="gate-f-pages@example.test", password="pass")
        profile = CandidateProfile.objects.create(user=user, profile_completion_score=100)
        recommendation = JobRecommendation.objects.create(
            user=user, profile=profile, job=job, fit_score=50, ranking_score=50, rank=1,
            strong_skills_json=[{"name": "dbt"}], missing_skills_json=[{"name": "Data Modeling"}, {"name": "DevOps"}],
            reason_summary=(
                "Priorité : ajoutez DevOps à votre plan d'apprentissage. "
                "Mettez à jour votre CV si vous avez déjà utilisé DevOps. Complétez votre profil candidat."
            ),
            risk_flags_json=[
                "job_language_unknown", "french_level_missing", "english_level_missing",
                "experience_unknown", "experience_too_low",
            ],
            computed_at=timezone.now(), status="active",
        )
        match = MatchResult.objects.create(
            user=user, profile=profile, job=job, fit_score=50, technical_skills_score=50,
            experience_score=50, role_title_score=50, language_score=50, location_score=50,
            job_snapshot_json={"title": job.title, "company_name": "Test", "country": "France"},
            strong_skills_json=[{"name": "dbt"}, {"name": "Artificial Intelligence"}],
            missing_required_skills_json=[{"name": "Data Modeling"}, {"name": "Data Engineer"}],
            missing_optional_skills_json=[{"name": "DevOps"}],
            risk_flags_json=[
                "job_language_unknown", "french_level_missing", "english_level_missing",
                "experience_unknown", "experience_too_low",
            ],
            recommended_actions_json=[
                "Priorité : ajoutez DevOps à votre plan d'apprentissage. Mettez à jour votre CV si vous avez déjà utilisé DevOps.",
                "Complétez votre profil candidat.",
            ],
        )
        SavedJob.objects.create(user=user, job=job)
        self.client.force_login(user)

        request = RequestFactory().get("/")
        request.user = user
        recommendation_html = render_to_string(
            "recommendations/partials/recommendation_card.html", {"rec": recommendation, "request": request}
        )
        pages = [
            recommendation_html,
            self.client.get(reverse("matching:detail", args=[match.public_id])).content.decode(),
            self.client.get(reverse("matching:history")).content.decode(),
            self.client.get(reverse("jobs:detail", args=[job.public_id])).content.decode(),
            self.client.get(reverse("dashboard:saved_jobs")).content.decode(),
        ]
        visible_sets = [self.canonical_names(html) for html in (pages[0], pages[1], pages[3], pages[4])]
        self.assertEqual(visible_sets, [["Data Modeling", "dbt"]] * 4)
        for html in pages:
            self.assertNotIn("Langues non précisées", html)
            self.assertNotIn(">DevOps</span>", html)
            self.assertNotIn("Artificial Intelligence", html)
            self.assertNotIn("Data Engineer", html)
            self.assertNotIn("Expérience non précisée", html)
            self.assertNotIn("Niveau d'anglais requis non atteint", html)
        self.assertIn("Expérience insuffisante", pages[0])
        self.assertIn("Expérience insuffisante", pages[1])
        self.assertIn("Data Modeling", pages[2])
        self.assertIn("Priorité : ajoutez Data Modeling", pages[0])
        self.assertIn("Priorité : ajoutez Data Modeling", pages[1])

    def test_previous_policy_results_are_not_current_when_affected(self):
        source = JobSource.objects.create(name="Gate F stale", slug="gate-f-stale", source_type=SourceType.FIXTURE)
        now = timezone.now()
        raw = RawJobRecord.objects.create(
            source=source, source_job_id="stale", raw_payload_json={}, payload_hash="hash-stale",
            first_seen_at=now, last_seen_at=now, last_fetched_at=now,
        )
        job = NormalizedJob.objects.create(
            source=source, raw_record=raw, source_job_id="stale",
            title="Stale policy", status=JobStatus.ACTIVE,
            skill_signal_quality="strong", classification_json={"is_it": True, "confidence": "high"},
            first_seen_at=now, last_seen_at=now, last_fetched_at=now,
        )
        broad = Skill.objects.create(canonical_name="DevOps", slug="stale-devops", category=SkillCategory.TOOLS)
        NormalizedJobSkill.objects.create(
            job=job, skill=broad, requirement_type=RequirementType.REQUIRED,
            source=SkillSource.ADMIN, confidence=1,
        )
        user = User.objects.create_user(username="gate-f-stale", email="gate-f-stale@example.test")
        profile = CandidateProfile.objects.create(user=user, profile_completion_score=100)
        match = MatchResult.objects.create(
            user=user, profile=profile, job=job,
            profile_snapshot_json=MatchResultService._profile_snapshot(profile),
            fit_score=60, technical_skills_score=60, experience_score=60,
            role_title_score=60, language_score=60, location_score=60,
            scoring_version="score_v1",
        )
        self.assertTrue(MatchResultService._is_stale(match))
        self.assertNotEqual(match.scoring_version, MATCH_SCORING_VERSION)

        recommendation = JobRecommendation.objects.create(
            user=user, profile=profile, job=job, fit_score=60, ranking_score=60, rank=1,
            missing_skills_json=[],
            recommendation_version="reco_v1", computed_at=timezone.now(), status="active",
        )
        self.assertEqual(RecommendationStalenessService.mark_outdated_policy_recommendations_stale(user), 1)
        recommendation.refresh_from_db()
        self.assertEqual(recommendation.status, "stale")
