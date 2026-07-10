from __future__ import annotations

import os
from decimal import Decimal
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.cvs.models import CVUpload
from apps.jobs.models import (
    JobSource,
    NormalizedJob,
    NormalizedJobSkill,
    RawJobRecord,
    RequirementType,
    SkillSource,
    SourceType,
)
from apps.jobs.services.gate_e_rematerialization import GateEOptions, GateERematerializationService, GateEResult
from apps.jobs.services.skill_materialization import JobSkillMaterializationService
from apps.matching.models import MatchResult
from apps.matching.services.scoring import MatchScoringService
from apps.profiles.models import CandidateProfile, ProfileSkill
from apps.recommendations.models import JobRecommendation
from apps.skills.models import Skill, SkillAlias, SkillCategory
from apps.skills.services.normalizer import normalize_skill_text


User = get_user_model()


class GateERematerializationCommandTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.source = JobSource.objects.create(
            name="Gate E",
            slug="gate-e",
            source_type=SourceType.MANUAL,
        )
        cls.python = Skill.objects.create(canonical_name="Python", slug="python-gate-e")
        SkillAlias.objects.create(
            skill=cls.python,
            alias="Python",
            normalized_alias=normalize_skill_text("Python"),
        )
        cls.software_development = Skill.objects.create(
            canonical_name="Software Development",
            slug="software-development-gate-e",
            category=SkillCategory.BACKEND,
        )
        SkillAlias.objects.create(
            skill=cls.software_development,
            alias="développement logiciel",
            normalized_alias=normalize_skill_text("développement logiciel"),
        )

    def _job(self, source_job_id: str, *, title: str = "Python Developer", description: str = "Stack technique: Python.") -> NormalizedJob:
        now = timezone.now()
        raw = RawJobRecord.objects.create(
            source=self.source,
            source_job_id=source_job_id,
            raw_payload_json={"competences": [{"libelle": "Python", "exigence": "E"}]},
            payload_hash=f"hash-{source_job_id}",
            first_seen_at=now,
            last_seen_at=now,
            last_fetched_at=now,
        )
        return NormalizedJob.objects.create(
            source=self.source,
            raw_record=raw,
            source_job_id=source_job_id,
            title=title,
            description=description,
            first_seen_at=now,
            last_seen_at=now,
            last_fetched_at=now,
            classification_json={"family": "software_development", "is_it": True, "confidence": "high"},
        )

    def _report_path(self, tmpdir: str) -> str:
        return str(Path(tmpdir) / "gate-e-report.md")

    def _skill(self, name: str, slug: str, category: str = SkillCategory.BACKEND, aliases: list[str] | None = None) -> Skill:
        skill = Skill.objects.create(canonical_name=name, slug=slug, category=category, is_active=True)
        for alias in aliases or [name]:
            SkillAlias.objects.create(
                skill=skill,
                alias=alias,
                normalized_alias=normalize_skill_text(alias),
            )
        return skill

    def test_command_defaults_to_dry_run_and_does_not_require_backup(self):
        self._job("dry-run")
        with TemporaryDirectory() as tmpdir:
            out = StringIO()
            with patch("apps.jobs.management.commands.run_gate_e_rematerialization.Command._create_backup") as backup:
                call_command("run_gate_e_rematerialization", report_path=self._report_path(tmpdir), stdout=out)

        backup.assert_not_called()
        self.assertIn("[DRY-RUN]", out.getvalue())

    @override_settings(DEBUG=True)
    def test_apply_requires_explicit_flag_and_writes_after_backup(self):
        job = self._job("apply")
        with TemporaryDirectory() as tmpdir:
            backup = Path(tmpdir) / "backup.dump"
            backup.write_bytes(b"backup")
            with patch(
                "apps.jobs.management.commands.run_gate_e_rematerialization.Command._create_backup",
                return_value=str(backup),
            ):
                call_command(
                    "run_gate_e_rematerialization",
                    apply=True,
                    job_public_id=str(job.public_id),
                    report_path=self._report_path(tmpdir),
                    stdout=StringIO(),
                )

        self.assertTrue(NormalizedJobSkill.objects.filter(job=job, skill=self.python).exists())

    @override_settings(DEBUG=False)
    def test_production_local_safety_guard_blocks_apply_before_backup(self):
        self._job("prod-guard")
        with patch("apps.jobs.management.commands.run_gate_e_rematerialization.Command._create_backup") as backup:
            with self.assertRaises(CommandError):
                call_command("run_gate_e_rematerialization", apply=True, stdout=StringIO())
        backup.assert_not_called()

    @override_settings(DEBUG=True)
    def test_apply_guard_rejects_remote_numeric_ip(self):
        from apps.jobs.management.commands.run_gate_e_rematerialization import Command

        with patch.dict(os.environ, {"DJANGO_SETTINGS_MODULE": "config.settings.local"}):
            with self.assertRaises(CommandError):
                Command._assert_local_apply_allowed(
                    {"engine": "django.db.backends.postgresql", "host": "10.1.2.3", "name": "tunitech_abroad"}
                )

    @override_settings(DEBUG=True)
    def test_apply_guard_rejects_remote_hostname(self):
        from apps.jobs.management.commands.run_gate_e_rematerialization import Command

        with patch.dict(os.environ, {"DJANGO_SETTINGS_MODULE": "config.settings.local"}):
            with self.assertRaises(CommandError):
                Command._assert_local_apply_allowed(
                    {"engine": "django.db.backends.postgresql", "host": "db.internal.example", "name": "tunitech_abroad"}
                )

    @override_settings(DEBUG=True)
    def test_apply_guard_accepts_localhost(self):
        from apps.jobs.management.commands.run_gate_e_rematerialization import Command

        with patch.dict(os.environ, {"DJANGO_SETTINGS_MODULE": "config.settings.local"}):
            Command._assert_local_apply_allowed(
                {"engine": "django.db.backends.postgresql", "host": "localhost", "name": "tunitech_abroad"}
            )

    @override_settings(DEBUG=True)
    def test_apply_guard_rejects_production_settings_before_backup(self):
        self._job("prod-settings-guard")
        with patch.dict(os.environ, {"DJANGO_SETTINGS_MODULE": "config.settings.production"}), patch(
            "apps.jobs.management.commands.run_gate_e_rematerialization.Command._create_backup"
        ) as backup:
            with self.assertRaises(CommandError):
                call_command("run_gate_e_rematerialization", apply=True, stdout=StringIO())
        backup.assert_not_called()

    @override_settings(DEBUG=True)
    def test_targeted_public_id_and_deterministic_ordering(self):
        first = self._job("a-first")
        second = self._job("b-second")
        with TemporaryDirectory() as tmpdir:
            backup = Path(tmpdir) / "backup.dump"
            backup.write_bytes(b"backup")
            with patch(
                "apps.jobs.management.commands.run_gate_e_rematerialization.Command._create_backup",
                return_value=str(backup),
            ):
                call_command(
                    "run_gate_e_rematerialization",
                    apply=True,
                    job_public_id=str(second.public_id),
                    report_path=self._report_path(tmpdir),
                    stdout=StringIO(),
                )

        self.assertFalse(NormalizedJobSkill.objects.filter(job=first).exists())
        self.assertTrue(NormalizedJobSkill.objects.filter(job=second).exists())

    @override_settings(DEBUG=True)
    def test_idempotent_second_apply_and_no_skill_auto_creation(self):
        job = self._job("idempotent")
        initial_skill_count = Skill.objects.count()
        with TemporaryDirectory() as tmpdir:
            backup = Path(tmpdir) / "backup.dump"
            backup.write_bytes(b"backup")
            with patch(
                "apps.jobs.management.commands.run_gate_e_rematerialization.Command._create_backup",
                return_value=str(backup),
            ):
                for _ in range(2):
                    call_command(
                        "run_gate_e_rematerialization",
                        apply=True,
                        job_public_id=str(job.public_id),
                        report_path=self._report_path(tmpdir),
                        stdout=StringIO(),
                    )

        self.assertEqual(Skill.objects.count(), initial_skill_count)
        self.assertEqual(NormalizedJobSkill.objects.filter(job=job, skill=self.python).count(), 1)

    def test_no_external_api_or_llm_calls(self):
        self._job("no-external")
        with TemporaryDirectory() as tmpdir:
            with patch("apps.jobs.services.france_travail.client.FranceTravailClient.search_offers") as ft, patch(
                "apps.llm.services.client.OpenRouterClient._make_request"
            ) as llm:
                call_command("run_gate_e_rematerialization", report_path=self._report_path(tmpdir), stdout=StringIO())

        ft.assert_not_called()
        llm.assert_not_called()

    def test_metrics_and_search_vector_service_are_used(self):
        self._job("metrics")
        with TemporaryDirectory() as tmpdir:
            report_path = self._report_path(tmpdir)
            with patch("apps.jobs.services.gate_e_rematerialization.JobSearchVectorService.update_search_vector") as update_vector:
                call_command("run_gate_e_rematerialization", report_path=report_path, stdout=StringIO())

            report = Path(report_path).read_text(encoding="utf-8")

        update_vector.assert_called()
        self.assertIn("active_jobs", report)
        self.assertIn("total_materialized_job_skills", report)

    @override_settings(DEBUG=True)
    def test_include_matches_marks_or_refreshes_recommendations(self):
        job = self._job("matches")
        user = User.objects.create_user(username="gate-e-user", email="gate-e@example.test", password="pass")
        profile = CandidateProfile.objects.create(
            user=user,
            current_level="mid",
            years_experience=3,
            french_level="c1",
            profile_completion_score=100,
        )
        JobRecommendation.objects.create(
            user=user,
            profile=profile,
            job=job,
            fit_score=80,
            ranking_score=Decimal("80.00"),
            rank=1,
            computed_at=timezone.now(),
            status="active",
        )

        with TemporaryDirectory() as tmpdir:
            backup = Path(tmpdir) / "backup.dump"
            backup.write_bytes(b"backup")
            with patch(
                "apps.jobs.management.commands.run_gate_e_rematerialization.Command._create_backup",
                return_value=str(backup),
            ):
                call_command(
                    "run_gate_e_rematerialization",
                    apply=True,
                    include_matches=True,
                    report_path=self._report_path(tmpdir),
                    stdout=StringIO(),
                )

        self.assertTrue(JobRecommendation.objects.filter(user=user, status__in=["active", "stale"]).exists())

    @override_settings(DEBUG=True)
    def test_targeted_include_matches_does_not_refresh_unrelated_jobs(self):
        targeted_job = self._job("targeted-match")
        unrelated_job = self._job("unrelated-match")
        targeted_user = User.objects.create_user(username="targeted-user", email="targeted@example.test", password="pass")
        unrelated_user = User.objects.create_user(username="unrelated-user", email="unrelated@example.test", password="pass")
        targeted_profile = CandidateProfile.objects.create(
            user=targeted_user,
            current_level="mid",
            years_experience=3,
            french_level="c1",
            profile_completion_score=100,
        )
        unrelated_profile = CandidateProfile.objects.create(
            user=unrelated_user,
            current_level="mid",
            years_experience=3,
            french_level="c1",
            profile_completion_score=100,
        )
        JobRecommendation.objects.create(
            user=targeted_user,
            profile=targeted_profile,
            job=targeted_job,
            fit_score=80,
            ranking_score=Decimal("80.00"),
            rank=1,
            computed_at=timezone.now(),
            status="active",
        )
        unrelated_rec = JobRecommendation.objects.create(
            user=unrelated_user,
            profile=unrelated_profile,
            job=unrelated_job,
            fit_score=70,
            ranking_score=Decimal("70.00"),
            rank=1,
            computed_at=timezone.now(),
            status="active",
        )
        same_user_unrelated_rec = JobRecommendation.objects.create(
            user=targeted_user,
            profile=targeted_profile,
            job=unrelated_job,
            fit_score=65,
            ranking_score=Decimal("65.00"),
            rank=2,
            computed_at=timezone.now(),
            status="active",
        )

        with TemporaryDirectory() as tmpdir:
            backup = Path(tmpdir) / "backup.dump"
            backup.write_bytes(b"backup")
            with patch(
                "apps.jobs.management.commands.run_gate_e_rematerialization.Command._create_backup",
                return_value=str(backup),
            ):
                call_command(
                    "run_gate_e_rematerialization",
                    apply=True,
                    job_public_id=str(targeted_job.public_id),
                    include_matches=True,
                    report_path=self._report_path(tmpdir),
                    stdout=StringIO(),
                )

        unrelated_rec.refresh_from_db()
        same_user_unrelated_rec.refresh_from_db()
        self.assertEqual(unrelated_rec.status, "active")
        self.assertEqual(same_user_unrelated_rec.status, "active")
        self.assertEqual(same_user_unrelated_rec.fit_score, 65)

    def test_match_consistency_passes_when_active_recommendation_matches_latest_match(self):
        job = self._job("match-consistency-pass")
        user = User.objects.create_user(username="match-pass", email="match-pass@example.test", password="pass")
        profile = CandidateProfile.objects.create(user=user, profile_completion_score=100)
        JobRecommendation.objects.create(
            user=user,
            profile=profile,
            job=job,
            fit_score=72,
            ranking_score=Decimal("72.00"),
            rank=1,
            computed_at=timezone.now(),
            status="active",
        )
        MatchResult.objects.create(
            user=user,
            profile=profile,
            job=job,
            fit_score=72,
            technical_skills_score=70,
            experience_score=70,
            role_title_score=70,
            language_score=70,
            location_score=70,
        )
        result = GateEResult(before={}, after={}, affected_job_ids={job.id})

        consistency = GateERematerializationService._calculate_match_consistency(
            GateEOptions(include_matches=True),
            result,
        )

        self.assertEqual(consistency["status"], "pass")
        self.assertEqual(consistency["comparable_pairs"], 1)
        self.assertEqual(consistency["mismatches"], 0)

    def test_match_consistency_fails_when_active_recommendation_differs_from_latest_match(self):
        job = self._job("match-consistency-fail")
        user = User.objects.create_user(username="match-fail", email="match-fail@example.test", password="pass")
        profile = CandidateProfile.objects.create(user=user, profile_completion_score=100)
        JobRecommendation.objects.create(
            user=user,
            profile=profile,
            job=job,
            fit_score=64,
            ranking_score=Decimal("64.00"),
            rank=1,
            computed_at=timezone.now(),
            status="active",
        )
        MatchResult.objects.create(
            user=user,
            profile=profile,
            job=job,
            fit_score=70,
            technical_skills_score=70,
            experience_score=70,
            role_title_score=70,
            language_score=70,
            location_score=70,
        )
        result = GateEResult(before={}, after={}, affected_job_ids={job.id})

        consistency = GateERematerializationService._calculate_match_consistency(
            GateEOptions(include_matches=True),
            result,
        )

        self.assertEqual(consistency["status"], "fail")
        self.assertEqual(consistency["comparable_pairs"], 1)
        self.assertEqual(consistency["mismatches"], 1)

    def test_match_consistency_is_not_run_when_no_comparable_pair_exists(self):
        job = self._job("match-consistency-empty")
        result = GateEResult(before={}, after={}, affected_job_ids={job.id})

        consistency = GateERematerializationService._calculate_match_consistency(
            GateEOptions(include_matches=True),
            result,
        )

        self.assertEqual(consistency["status"], "not_run")
        self.assertEqual(consistency["comparable_pairs"], 0)
        self.assertEqual(consistency["mismatches"], 0)

    def test_database_family_aliases_map_to_distinct_canonical_skills(self):
        self._skill("PostgreSQL", "postgresql-gate-e-family", SkillCategory.DATABASE, ["PostgreSQL"])
        self._skill("MySQL", "mysql-gate-e-family", SkillCategory.DATABASE, ["MySQL"])
        self._skill("SQLite", "sqlite-gate-e-family", SkillCategory.DATABASE, ["SQLite"])
        self._skill("SQL", "sql-gate-e-family", SkillCategory.DATABASE, ["SQL"])
        self._skill("SQL Server", "sql-server-gate-e-family", SkillCategory.DATABASE, ["SQL Server"])

        aliases = {
            alias.alias: alias.skill.canonical_name
            for alias in SkillAlias.objects.filter(
                normalized_alias__in=[
                    normalize_skill_text("PostgreSQL"),
                    normalize_skill_text("MySQL"),
                    normalize_skill_text("SQLite"),
                    normalize_skill_text("SQL Server"),
                ]
            ).select_related("skill")
        }

        self.assertEqual(aliases["PostgreSQL"], "PostgreSQL")
        self.assertEqual(aliases["MySQL"], "MySQL")
        self.assertEqual(aliases["SQLite"], "SQLite")
        self.assertEqual(aliases["SQL Server"], "SQL Server")
        self.assertEqual({aliases["PostgreSQL"], aliases["MySQL"], aliases["SQLite"]}, {"PostgreSQL", "MySQL", "SQLite"})

        job = self._job("sql-server-distinct")
        JobSkillMaterializationService.materialize_for_job(
            job,
            source="rule",
            raw_skills_dict={
                "SQL Server": RequirementType.REQUIRED.value,
                "PostgreSQL": RequirementType.REQUIRED.value,
                "MySQL": RequirementType.REQUIRED.value,
                "SQLite": RequirementType.REQUIRED.value,
            },
        )
        materialized = {
            row.skill.canonical_name
            for row in NormalizedJobSkill.objects.filter(job=job).select_related("skill")
        }

        self.assertIn("SQL Server", materialized)
        self.assertIn("PostgreSQL", materialized)
        self.assertIn("MySQL", materialized)
        self.assertIn("SQLite", materialized)
        self.assertNotIn("SQL", materialized)

    def test_chef_ambiguity_uses_actual_materialization_context(self):
        chef = self._skill("Chef", "chef-gate-e", SkillCategory.DEVOPS, ["Chef"])
        project_job = self._job("chef-project", title="Chef de projet informatique", description="Pilotage projet informatique.")
        JobSkillMaterializationService.materialize_for_job(
            project_job,
            source="rule",
            raw_skills_dict={"chef de projet informatique": RequirementType.REQUIRED.value},
        )

        devops_job = self._job("chef-devops", title="Ingénieur DevOps", description="Chef Infra automation.")
        JobSkillMaterializationService.materialize_for_job(
            devops_job,
            source="rule",
            raw_skills_dict={"Chef Infra": RequirementType.REQUIRED.value},
        )

        self.assertFalse(NormalizedJobSkill.objects.filter(job=project_job, skill=chef).exists())
        self.assertTrue(NormalizedJobSkill.objects.filter(job=devops_job, skill=chef).exists())

    def test_cv_noise_check_ignores_manual_confirmed_noisy_skills(self):
        user = User.objects.create_user(username="manual-noise", email="manual-noise@example.test", password="pass")
        profile = CandidateProfile.objects.create(user=user)
        ProfileSkill.objects.create(
            profile=profile,
            raw_name="web development",
            normalized_name=normalize_skill_text("web development"),
            source="manual",
            is_confirmed=True,
        )

        report = GateERematerializationService._regression_cases(GateEOptions(), GateEResult(before={}, after={}))

        self.assertIn("CV-origin noisy phrases are not ProfileSkill rows: pass", report)

    def test_cv_noise_check_fails_for_confirmed_cv_origin_noisy_skill(self):
        user = User.objects.create_user(username="cv-noise", email="cv-noise@example.test", password="pass")
        profile = CandidateProfile.objects.create(user=user)
        ProfileSkill.objects.create(
            profile=profile,
            raw_name="stock alerts",
            normalized_name=normalize_skill_text("stock alerts"),
            source="cv_upload",
            is_confirmed=True,
        )

        report = GateERematerializationService._regression_cases(GateEOptions(), GateEResult(before={}, after={}))

        self.assertIn("CV-origin noisy phrases are not ProfileSkill rows: fail", report)
        self.assertNotIn("PRIVATE RAW CV TEXT", report)

    def test_broad_detected_software_development_does_not_improve_technical_score_or_create_required_penalty(self):
        user = User.objects.create_user(username="broad-score", email="broad-score@example.test", password="pass")
        profile = CandidateProfile.objects.create(
            user=user,
            current_level="mid",
            years_experience=3,
            french_level="c1",
            profile_completion_score=100,
        )
        django = self._skill("Django", "django-broad-score", SkillCategory.BACKEND, ["Django"])
        ProfileSkill.objects.create(profile=profile, skill=django, raw_name="Django", normalized_name="django")
        job = self._job("broad-score", title="Backend Developer", description="Build Django services.")
        NormalizedJobSkill.objects.create(
            job=job,
            skill=django,
            requirement_type=RequirementType.REQUIRED.value,
            source=SkillSource.RULE.value,
            confidence=1,
        )
        before = MatchScoringService.calculate(profile, job)

        NormalizedJobSkill.objects.create(
            job=job,
            skill=self.software_development,
            requirement_type=RequirementType.DETECTED.value,
            source=SkillSource.RULE.value,
            confidence=0.4,
        )
        after = MatchScoringService.calculate(profile, job)

        self.assertEqual(after.technical_skills_score, before.technical_skills_score)
        self.assertEqual(after.fit_score, before.fit_score)
        self.assertEqual(after.missing_required_skills, [])
        self.assertNotIn("missing_required_skills", after.risk_flags)

    def test_api_and_monitoring_broad_rows_do_not_change_deterministic_fit_score(self):
        user = User.objects.create_user(username="api-monitoring", email="api-monitoring@example.test", password="pass")
        profile = CandidateProfile.objects.create(
            user=user,
            current_level="mid",
            years_experience=3,
            french_level="c1",
            profile_completion_score=100,
        )
        django = self._skill("Django", "django-api-monitoring", SkillCategory.BACKEND, ["Django"])
        api = self._skill("API", "api-gate-e-broad", SkillCategory.BACKEND, ["API"])
        monitoring = self._skill("Monitoring", "monitoring-gate-e-broad", SkillCategory.TOOLS, ["Monitoring"])
        ProfileSkill.objects.create(profile=profile, skill=django, raw_name="Django", normalized_name="django")
        job = self._job("api-monitoring", title="Backend Developer", description="Build Django services.")
        NormalizedJobSkill.objects.create(
            job=job,
            skill=django,
            requirement_type=RequirementType.REQUIRED.value,
            source=SkillSource.RULE.value,
            confidence=1,
        )
        before = MatchScoringService.calculate(profile, job)
        for skill in (api, monitoring):
            NormalizedJobSkill.objects.create(
                job=job,
                skill=skill,
                requirement_type=RequirementType.DETECTED.value,
                source=SkillSource.RULE.value,
                confidence=0.4,
            )

        after = MatchScoringService.calculate(profile, job)

        self.assertEqual(after.technical_skills_score, before.technical_skills_score)
        self.assertEqual(after.fit_score, before.fit_score)

    def test_specific_supported_technical_skill_still_affects_scoring(self):
        user = User.objects.create_user(username="rest-score", email="rest-score@example.test", password="pass")
        profile = CandidateProfile.objects.create(
            user=user,
            current_level="mid",
            years_experience=3,
            french_level="c1",
            profile_completion_score=100,
        )
        rest_api = self._skill("REST API", "rest-api-gate-e-score", SkillCategory.BACKEND, ["REST API"])
        job = self._job("rest-score", title="API Developer", description="Build REST API services.")
        NormalizedJobSkill.objects.create(
            job=job,
            skill=rest_api,
            requirement_type=RequirementType.REQUIRED.value,
            source=SkillSource.RULE.value,
            confidence=1,
        )
        missing = MatchScoringService.calculate(profile, job)

        ProfileSkill.objects.create(profile=profile, skill=rest_api, raw_name="REST API", normalized_name=normalize_skill_text("REST API"))
        matched = MatchScoringService.calculate(profile, job)

        self.assertLess(missing.technical_skills_score, matched.technical_skills_score)
        self.assertIn({"name": "REST API", "requirement_type": "required"}, missing.missing_required_skills)
        self.assertIn({"name": "REST API", "type": "required"}, matched.strong_skills)

    def test_required_and_optional_exact_technical_skill_behavior_remains_unchanged(self):
        user = User.objects.create_user(username="exact-score", email="exact-score@example.test", password="pass")
        profile = CandidateProfile.objects.create(
            user=user,
            current_level="mid",
            years_experience=3,
            french_level="c1",
            profile_completion_score=100,
        )
        django = self._skill("Django", "django-exact-score", SkillCategory.BACKEND, ["Django"])
        postgres = self._skill("PostgreSQL", "postgres-exact-score", SkillCategory.DATABASE, ["PostgreSQL"])
        ProfileSkill.objects.create(profile=profile, skill=django, raw_name="Django", normalized_name="django")
        job = self._job("exact-score", title="Backend Developer", description="Build Django and PostgreSQL services.")
        NormalizedJobSkill.objects.create(
            job=job,
            skill=django,
            requirement_type=RequirementType.REQUIRED.value,
            source=SkillSource.RULE.value,
            confidence=1,
        )
        NormalizedJobSkill.objects.create(
            job=job,
            skill=postgres,
            requirement_type=RequirementType.OPTIONAL.value,
            source=SkillSource.RULE.value,
            confidence=1,
        )
        optional_missing = MatchScoringService.calculate(profile, job)

        ProfileSkill.objects.create(profile=profile, skill=postgres, raw_name="PostgreSQL", normalized_name="postgresql")
        optional_matched = MatchScoringService.calculate(profile, job)

        self.assertEqual(optional_missing.missing_required_skills, [])
        self.assertIn({"name": "PostgreSQL", "requirement_type": "optional"}, optional_missing.missing_optional_skills)
        self.assertLess(optional_missing.technical_skills_score, optional_matched.technical_skills_score)

    def test_report_splits_broad_signals_from_hard_technical_skills(self):
        self._job(
            "broad-report",
            title="Développeur logiciel",
            description="Compétences techniques: développement logiciel.",
        )
        with TemporaryDirectory() as tmpdir:
            report_path = self._report_path(tmpdir)
            call_command("run_gate_e_rematerialization", report_path=report_path, stdout=StringIO())
            report = Path(report_path).read_text(encoding="utf-8")

        self.assertIn("### added_hard_technical_skills", report)
        self.assertIn("### added_broad_non_scoring_signals", report)
        self.assertIn("Software Development", report)
        self.assertNotIn("top_added_or_retained_hard_technical_skills", report)

    def test_report_lists_actual_unmatched_candidate_phrases(self):
        from apps.skills.models import UnmatchedSkillCandidate

        UnmatchedSkillCandidate.objects.create(
            raw_skill_text="Private raw text should not be reported",
            normalized_text="unknown-framework",
            source_type="job",
            occurrence_count=7,
            status="pending",
        )
        self._job("unmatched-report")
        with TemporaryDirectory() as tmpdir:
            report_path = self._report_path(tmpdir)
            call_command("run_gate_e_rematerialization", report_path=report_path, stdout=StringIO())
            report = Path(report_path).read_text(encoding="utf-8")

        self.assertIn("normalized_text=unknown-framework", report)
        self.assertIn("source_type=job", report)
        self.assertIn("status=pending", report)
        self.assertIn("occurrence_count=7", report)
        self.assertNotIn("Private raw text should not be reported", report)

    def test_include_cvs_is_rejected_in_dry_run(self):
        with patch("apps.jobs.services.gate_e_rematerialization.CVParsingService.parse") as parse:
            with self.assertRaises(CommandError):
                call_command("run_gate_e_rematerialization", include_cvs=True, stdout=StringIO())
        parse.assert_not_called()

    @override_settings(DEBUG=True, LLM_ENABLED=False)
    def test_optional_cv_reparse_uses_active_non_deleted_cvs_only(self):
        active_user = User.objects.create_user(username="active-cv", email="active-cv@example.test", password="pass")
        deleted_user = User.objects.create_user(username="deleted-cv", email="deleted-cv@example.test", password="pass")
        active = CVUpload.objects.create(
            user=active_user,
            file="cvs/active.pdf",
            original_filename="active.pdf",
            file_hash="active",
            file_size=10,
            is_active=True,
        )
        deleted = CVUpload.objects.create(
            user=deleted_user,
            file="cvs/deleted.pdf",
            original_filename="deleted.pdf",
            file_hash="deleted",
            file_size=10,
            is_active=False,
            deleted_at=timezone.now(),
        )

        with TemporaryDirectory() as tmpdir:
            backup = Path(tmpdir) / "backup.dump"
            backup.write_bytes(b"backup")
            with patch(
                "apps.jobs.management.commands.run_gate_e_rematerialization.Command._create_backup",
                return_value=str(backup),
            ), patch("apps.jobs.services.gate_e_rematerialization.CVParsingService.parse", return_value=None) as parse:
                call_command(
                    "run_gate_e_rematerialization",
                    apply=True,
                    include_cvs=True,
                    report_path=self._report_path(tmpdir),
                    stdout=StringIO(),
                )

        parse.assert_called_once()
        self.assertEqual(parse.call_args.args[0].public_id, active.public_id)
        self.assertNotEqual(parse.call_args.args[0].public_id, deleted.public_id)

    def test_report_does_not_contain_raw_cv_text_or_secret_values(self):
        self._job("report-safety")
        raw_cv_text = "PRIVATE RAW CV TEXT"
        with TemporaryDirectory() as tmpdir:
            report_path = self._report_path(tmpdir)
            call_command("run_gate_e_rematerialization", report_path=report_path, stdout=StringIO())
            report = Path(report_path).read_text(encoding="utf-8")

        self.assertNotIn(raw_cv_text, report)
        self.assertNotIn("PASSWORD", report.upper())

    def test_backup_failure_prevents_mutation(self):
        job = self._job("backup-fail")
        with patch(
            "apps.jobs.management.commands.run_gate_e_rematerialization.Command._create_backup",
            side_effect=CommandError("backup failed"),
        ):
            with self.assertRaises(CommandError):
                call_command("run_gate_e_rematerialization", apply=True, stdout=StringIO())

        self.assertFalse(NormalizedJobSkill.objects.filter(job=job).exists())

    def test_partial_row_failure_is_reported_without_aborting_unrelated_rows(self):
        bad = self._job("bad")
        good = self._job("good")
        with TemporaryDirectory() as tmpdir:
            report_path = self._report_path(tmpdir)

            def fail_one(job):
                if job.public_id == bad.public_id:
                    raise RuntimeError("row failure")
                return None

            with patch("apps.jobs.services.gate_e_rematerialization.JobSearchVectorService.update_search_vector", side_effect=fail_one):
                with self.assertRaises(CommandError):
                    call_command("run_gate_e_rematerialization", report_path=report_path, stdout=StringIO())
            report = Path(report_path).read_text(encoding="utf-8")

        self.assertIn(str(bad.public_id), report)
        self.assertIn(str(good.public_id), report)

    @override_settings(DEBUG=True)
    def test_apply_partial_row_failure_rolls_back_failed_row_only(self):
        bad = self._job("apply-bad")
        good = self._job("apply-good")
        with TemporaryDirectory() as tmpdir:
            backup = Path(tmpdir) / "backup.dump"
            backup.write_bytes(b"backup")
            report_path = self._report_path(tmpdir)

            def fail_one(job):
                if job.public_id == bad.public_id:
                    raise RuntimeError("row failure")
                return None

            with patch(
                "apps.jobs.management.commands.run_gate_e_rematerialization.Command._create_backup",
                return_value=str(backup),
            ), patch(
                "apps.jobs.services.gate_e_rematerialization.JobSearchVectorService.update_search_vector",
                side_effect=fail_one,
            ):
                with self.assertRaises(CommandError):
                    call_command(
                        "run_gate_e_rematerialization",
                        apply=True,
                        report_path=report_path,
                        stdout=StringIO(),
                    )

        self.assertFalse(NormalizedJobSkill.objects.filter(job=bad).exists())
        self.assertTrue(NormalizedJobSkill.objects.filter(job=good, skill=self.python).exists())
