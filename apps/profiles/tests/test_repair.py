from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.accounts.models import User
from apps.matching.models import MatchResult
from apps.profiles.models import CandidateProfile, ProfileSkill
from apps.profiles.services.backfill import ProfileSkillBackfillService
from apps.recommendations.models import JobRecommendation
from apps.skills.models import Skill, SkillAlias, UnmatchedSkillCandidate
from apps.skills.services.normalizer import normalize_skill_text

UserModel = get_user_model()


def make_user(username: str, email: str) -> User:
    user = UserModel(username=username, email=email)
    user.set_password("pw")
    user.save()
    return user


class ProfileSkillRepairServiceTests(TestCase):
    def setUp(self):
        self.user = make_user("repairuser", "repair@example.test")
        self.profile = CandidateProfile.objects.create(user=self.user, target_country="France")

        self.python = Skill.objects.create(
            canonical_name="Python", slug="python", category="programming_language"
        )
        self.java = Skill.objects.create(
            canonical_name="Java", slug="java", category="programming_language"
        )
        self.docker = Skill.objects.create(
            canonical_name="Docker", slug="docker", category="devops"
        )
        self.c = Skill.objects.create(
            canonical_name="C", slug="c-lang", category="programming_language"
        )
        self.cpp = Skill.objects.create(
            canonical_name="C++", slug="cpp", category="programming_language"
        )

        SkillAlias.objects.create(
            skill=self.python,
            alias="Python",
            normalized_alias=normalize_skill_text("Python"),
        )
        SkillAlias.objects.create(
            skill=self.java,
            alias="Java",
            normalized_alias=normalize_skill_text("Java"),
        )
        SkillAlias.objects.create(
            skill=self.docker,
            alias="Docker",
            normalized_alias=normalize_skill_text("Docker"),
        )
        SkillAlias.objects.create(
            skill=self.c,
            alias="C",
            normalized_alias=normalize_skill_text("C"),
        )
        SkillAlias.objects.create(
            skill=self.cpp,
            alias="C++",
            normalized_alias=normalize_skill_text("C++"),
        )

    def test_dry_run_writes_nothing(self):
        row = ProfileSkill.objects.create(
            profile=self.profile,
            raw_name="Python",
            normalized_name="python",
            source="cv_upload",
        )

        report = ProfileSkillBackfillService.repair(user=self.user, apply=False)

        row.refresh_from_db()
        self.assertIsNone(row.skill_id)
        self.assertEqual(report.rows_linked, 0)
        self.assertFalse(report.user_reports[0].changed)

    def test_deterministic_mapping_applies(self):
        row = ProfileSkill.objects.create(
            profile=self.profile,
            raw_name="Python",
            normalized_name="python",
            source="cv_upload",
        )

        report = ProfileSkillBackfillService.repair(user=self.user, apply=True)

        row.refresh_from_db()
        self.assertEqual(row.skill, self.python)
        self.assertEqual(report.rows_linked, 1)
        self.assertTrue(report.user_reports[0].changed)

    def test_ambiguous_mapping_is_preserved_and_reported(self):
        row = ProfileSkill.objects.create(
            profile=self.profile,
            raw_name="C C++",
            normalized_name="c c++",
            source="cv_upload",
        )

        report = ProfileSkillBackfillService.repair(user=self.user, apply=True)

        row.refresh_from_db()
        self.assertIsNone(row.skill_id)
        self.assertEqual(report.rows_ambiguous, 1)
        plan = report.user_reports[0].row_plans[0]
        self.assertEqual(plan.classification, "ambiguous")
        self.assertIn("C", plan.candidate_skill_names)
        self.assertIn("C++", plan.candidate_skill_names)

    def test_unmatched_mapping_is_preserved_not_recorded(self):
        row = ProfileSkill.objects.create(
            profile=self.profile,
            raw_name="MagicSkillXYZ",
            normalized_name="magicskillxyz",
            source="cv_upload",
        )

        report = ProfileSkillBackfillService.repair(user=self.user, apply=True)

        row.refresh_from_db()
        self.assertIsNone(row.skill_id)
        self.assertEqual(report.rows_unmatched, 1)
        self.assertFalse(
            UnmatchedSkillCandidate.objects.filter(
                normalized_text="magicskillxyz",
                source_type="cv",
            ).exists()
        )

    def test_one_user_scope_touches_only_that_user(self):
        other_user = make_user("otherrepair", "otherrepair@example.test")
        other_profile = CandidateProfile.objects.create(user=other_user, target_country="France")
        ProfileSkill.objects.create(
            profile=self.profile,
            raw_name="Python",
            normalized_name="python",
            source="cv_upload",
        )
        other_row = ProfileSkill.objects.create(
            profile=other_profile,
            raw_name="Java",
            normalized_name="java",
            source="cv_upload",
        )

        ProfileSkillBackfillService.repair(user=self.user, apply=True)

        other_row.refresh_from_db()
        self.assertIsNone(other_row.skill_id)

    def test_all_user_scope_handles_all_affected_users(self):
        other_user = make_user("otherrepair2", "otherrepair2@example.test")
        other_profile = CandidateProfile.objects.create(user=other_user, target_country="France")
        ProfileSkill.objects.create(
            profile=self.profile,
            raw_name="Python",
            normalized_name="python",
            source="cv_upload",
        )
        ProfileSkill.objects.create(
            profile=other_profile,
            raw_name="Java",
            normalized_name="java",
            source="cv_upload",
        )

        report = ProfileSkillBackfillService.repair(apply=True)

        self.assertEqual(report.users_scanned, 2)
        self.assertEqual(report.rows_linked, 2)

    def test_second_apply_makes_zero_changes(self):
        ProfileSkill.objects.create(
            profile=self.profile,
            raw_name="Python",
            normalized_name="python",
            source="cv_upload",
        )

        first = ProfileSkillBackfillService.repair(user=self.user, apply=True)
        second = ProfileSkillBackfillService.repair(user=self.user, apply=True)

        self.assertEqual(first.rows_linked, 1)
        self.assertEqual(second.rows_linked, 0)

    def test_non_null_links_are_never_overwritten(self):
        SkillAlias.objects.create(
            skill=self.python,
            alias="Py",
            normalized_alias=normalize_skill_text("Py"),
        )
        ProfileSkill.objects.create(
            profile=self.profile,
            skill=self.java,
            raw_name="Python",
            normalized_name="python",
            source="manual",
            confidence=100,
            is_confirmed=True,
        )
        ProfileSkill.objects.create(
            profile=self.profile,
            raw_name="Py",
            normalized_name="py",
            source="cv_upload",
        )

        report = ProfileSkillBackfillService.repair(user=self.user, apply=True)

        self.assertEqual(report.conflicts, 1)
        self.assertEqual(report.rows_linked, 0)
        row = ProfileSkill.objects.get(profile=self.profile, normalized_name="python")
        self.assertEqual(row.skill, self.java)
        null_row = ProfileSkill.objects.get(profile=self.profile, normalized_name="py")
        self.assertIsNone(null_row.skill)

    def test_repair_converts_legacy_alias_row(self):
        dotnet = Skill.objects.create(
            canonical_name=".NET", slug="dotnet", category="backend"
        )
        SkillAlias.objects.create(
            skill=dotnet,
            alias=".NET Core",
            normalized_alias=normalize_skill_text(".NET Core"),
        )
        alias_row = ProfileSkill.objects.create(
            profile=self.profile,
            raw_name=".NET Core",
            normalized_name=normalize_skill_text(".NET Core"),
            source="cv_upload",
            confidence=80,
        )

        report = ProfileSkillBackfillService.repair(user=self.user, apply=True)

        self.assertEqual(report.rows_linked, 1)
        alias_row.refresh_from_db()
        self.assertEqual(alias_row.skill, dotnet)
        self.assertEqual(
            alias_row.normalized_name, normalize_skill_text(dotnet.canonical_name)
        )
        self.assertEqual(
            ProfileSkill.objects.filter(profile=self.profile).count(), 1
        )

    def test_repair_delegates_to_materialization_service(self):
        alias_row = ProfileSkill.objects.create(
            profile=self.profile,
            raw_name="Python3",
            normalized_name="python3",
            source="cv_upload",
            confidence=80,
        )
        SkillAlias.objects.create(
            skill=self.python,
            alias="Python3",
            normalized_alias=normalize_skill_text("Python3"),
        )

        with patch(
            "apps.profiles.services.backfill.ProfileSkillMaterializationService.materialize"
        ) as mock_materialize:
            mock_materialize.return_value = type(
                "R",
                (),
                {
                    "created": False,
                    "linked_existing": True,
                    "unchanged": False,
                    "conflict": False,
                    "changed": True,
                    "profile_skill": alias_row,
                    "conflict_skill_id": None,
                },
            )()
            ProfileSkillBackfillService.repair(user=self.user, apply=True)

        mock_materialize.assert_called_once()
        call_kwargs = mock_materialize.call_args.kwargs
        self.assertEqual(call_kwargs["skill"], self.python)
        self.assertEqual(call_kwargs["existing_profile_skill"], alias_row)

    def test_per_user_rollback_on_error(self):
        ProfileSkill.objects.create(
            profile=self.profile,
            raw_name="Python",
            normalized_name="python",
            source="cv_upload",
        )

        with patch(
            "apps.profiles.models.ProfileSkill.save",
            side_effect=RuntimeError("boom"),
        ):
            report = ProfileSkillBackfillService.repair(user=self.user, apply=True)

        self.assertEqual(report.errors, 1)
        row = ProfileSkill.objects.get(profile=self.profile, normalized_name="python")
        self.assertIsNone(row.skill_id)

    def test_disappeared_planned_skill_rolls_back_all_user_links(self):
        python_row = ProfileSkill.objects.create(
            profile=self.profile,
            raw_name="Python",
            normalized_name="python",
            source="cv_upload",
        )
        java_row = ProfileSkill.objects.create(
            profile=self.profile,
            raw_name="Java",
            normalized_name="java",
            source="cv_upload",
        )

        with patch.object(
            ProfileSkillBackfillService,
            "_get_skill",
            side_effect=[self.python, None],
        ):
            report = ProfileSkillBackfillService.repair(user=self.user, apply=True)

        python_row.refresh_from_db()
        java_row.refresh_from_db()
        self.assertIsNone(python_row.skill_id)
        self.assertIsNone(java_row.skill_id)
        self.assertEqual(report.errors, 1)
        self.assertEqual(report.rows_linked, 0)
        self.assertIn("disappeared", report.user_reports[0].errors[0])


class ProfileSkillRepairCommandTests(TestCase):
    def setUp(self):
        self.user = make_user("cmduser", "cmd@example.test")
        self.profile = CandidateProfile.objects.create(user=self.user, target_country="France")
        self.python = Skill.objects.create(
            canonical_name="Python", slug="python", category="programming_language"
        )
        SkillAlias.objects.create(
            skill=self.python,
            alias="Python",
            normalized_alias=normalize_skill_text("Python"),
        )
        ProfileSkill.objects.create(
            profile=self.profile,
            raw_name="Python",
            normalized_name="python",
            source="cv_upload",
        )

    @staticmethod
    def _call(*args, **kwargs):
        out = StringIO()
        err = StringIO()
        kwargs.setdefault("stdout", out)
        kwargs.setdefault("stderr", err)
        call_command("repair_profile_skill_links", *args, **kwargs)
        return out.getvalue(), err.getvalue()

    def _command_error_class(self):
        from django.core.management.base import CommandError
        return CommandError

    def test_dry_run_default_outputs_no_writes(self):
        output, _ = self._call("--user-id", str(self.user.pk))
        self.assertIn("Dry run only", output)
        self.assertIn("rows_linked=0", output)

    def test_dry_run_requires_scope(self):
        CommandError = self._command_error_class()
        with self.assertRaises(CommandError) as ctx:
            self._call()
        self.assertIn("one of the arguments --user-id --all-users is required", str(ctx.exception))

    def test_user_id_and_all_users_mutually_exclusive(self):
        CommandError = self._command_error_class()
        with self.assertRaises(CommandError) as ctx:
            self._call("--user-id", str(self.user.pk), "--all-users")
        self.assertIn("not allowed with", str(ctx.exception).lower())

    def test_dry_run_errors_exit_nonzero_after_report(self):
        CommandError = self._command_error_class()
        out = StringIO()
        err = StringIO()
        with patch.object(
            ProfileSkillBackfillService,
            "_plan_row",
            side_effect=RuntimeError("dry-run planning failure"),
        ):
            with self.assertRaises(CommandError):
                call_command(
                    "repair_profile_skill_links",
                    "--user-id",
                    str(self.user.pk),
                    stdout=out,
                    stderr=err,
                )

        output = out.getvalue() + err.getvalue()
        self.assertIn("Dry run only", output)
        self.assertIn("errors=1", output)
        self.assertIn("dry-run planning failure", output)
        row = ProfileSkill.objects.get(profile=self.profile, normalized_name="python")
        self.assertIsNone(row.skill_id)

    def test_refresh_results_requires_apply(self):
        CommandError = self._command_error_class()
        with self.assertRaises(CommandError) as ctx:
            self._call("--user-id", str(self.user.pk), "--refresh-results")
        self.assertIn("--refresh-results requires --apply", str(ctx.exception))

    @override_settings(DEBUG=False)
    def test_production_apply_requires_confirmation(self):
        CommandError = self._command_error_class()
        with self.assertRaises(CommandError) as ctx:
            self._call("--user-id", str(self.user.pk), "--apply")
        self.assertIn("--confirm-production", str(ctx.exception))

    @override_settings(DEBUG=True)
    def test_apply_links_deterministic_row(self):
        output, _ = self._call("--user-id", str(self.user.pk), "--apply")
        self.assertIn("rows_linked=1", output)
        row = ProfileSkill.objects.get(profile=self.profile, normalized_name="python")
        self.assertEqual(row.skill, self.python)

    @override_settings(DEBUG=False)
    def test_apply_with_production_confirmation_links(self):
        output, _ = self._call(
            "--user-id", str(self.user.pk), "--apply", "--confirm-production"
        )
        self.assertIn("rows_linked=1", output)
        row = ProfileSkill.objects.get(profile=self.profile, normalized_name="python")
        self.assertEqual(row.skill, self.python)


class ProfileSkillRepairRefreshTests(TestCase):
    def setUp(self):
        self.user = make_user("refreshuser", "refresh@example.test")
        self.profile = CandidateProfile.objects.create(
            user=self.user,
            target_country="France",
            profile_completion_score=80,
            current_level="junior",
            target_roles=["Developer"],
            french_level="intermediate",
            english_level="fluent",
            relocation_preference="yes",
            remote_preference="hybrid",
        )
        self.python = Skill.objects.create(
            canonical_name="Python", slug="python", category="programming_language"
        )
        SkillAlias.objects.create(
            skill=self.python,
            alias="Python",
            normalized_alias=normalize_skill_text("Python"),
        )
        ProfileSkill.objects.create(
            profile=self.profile,
            raw_name="Python",
            normalized_name="python",
            source="cv_upload",
        )

    def test_only_changed_users_refresh(self):
        other_user = make_user("unchangeduser", "unchanged@example.test")
        other_profile = CandidateProfile.objects.create(
            user=other_user,
            target_country="France",
            profile_completion_score=80,
            current_level="junior",
            target_roles=["Developer"],
            french_level="intermediate",
            english_level="fluent",
            relocation_preference="yes",
            remote_preference="hybrid",
        )
        ProfileSkill.objects.create(
            profile=other_profile,
            skill=self.python,
            raw_name="Python",
            normalized_name="python",
            source="manual",
            is_confirmed=True,
        )

        with patch(
            "apps.profiles.services.backfill.RecommendationService.refresh_for_user"
        ) as mock_refresh:
            mock_refresh.return_value = type(
                "R", (), {"recommendations_created": 0, "recommendations_updated": 0}
            )()
            ProfileSkillBackfillService.repair(apply=True, refresh_results=True)

        mock_refresh.assert_called_once_with(self.user, "profile_skill_repair")

    def test_refresh_uses_public_service_methods(self):
        with patch(
            "apps.profiles.services.backfill.RecommendationService.refresh_for_user"
        ) as mock_refresh, patch(
            "apps.profiles.services.backfill.MatchResultService.recompute_current_matches_for_user"
        ) as mock_recompute:
            mock_refresh.return_value = type(
                "R", (), {"recommendations_created": 2, "recommendations_updated": 3}
            )()
            mock_recompute.return_value = 4
            report = ProfileSkillBackfillService.repair(
                user=self.user, apply=True, refresh_results=True
            )

        mock_refresh.assert_called_once()
        mock_recompute.assert_called_once_with(self.user)
        self.assertEqual(report.users_refreshed, 1)
        self.assertEqual(report.recommendations_created, 2)
        self.assertEqual(report.recommendations_updated, 3)
        self.assertEqual(report.matches_recomputed, 4)


class ProfileSkillBackfillLegacyWrapperTests(TestCase):
    def setUp(self):
        self.user = make_user("legacyuser", "legacy@example.test")
        self.profile = CandidateProfile.objects.create(user=self.user, target_country="France")
        self.python = Skill.objects.create(
            canonical_name="Python", slug="python", category="programming_language"
        )
        SkillAlias.objects.create(
            skill=self.python,
            alias="Python",
            normalized_alias=normalize_skill_text("Python"),
        )

    def test_legacy_service_wrapper_refuses_apply(self):
        with self.assertRaises(RuntimeError) as ctx:
            ProfileSkillBackfillService.backfill_profile_skills(apply=True)
        self.assertIn("no longer accepts apply=True", str(ctx.exception))

    def test_legacy_service_wrapper_allows_dry_run(self):
        ProfileSkill.objects.create(
            profile=self.profile,
            raw_name="Python",
            normalized_name="python",
            source="cv_upload",
        )
        report = ProfileSkillBackfillService.backfill_profile_skills(apply=False)
        self.assertEqual(report["rows_scanned"], 1)
        self.assertEqual(report["rows_linked"], 0)


class ProfileSkillLegacyCommandTests(TestCase):
    def setUp(self):
        self.user = make_user("legacycmduser", "legacycmd@example.test")
        CandidateProfile.objects.create(user=self.user, target_country="France")

    def _call(self, *args, **kwargs):
        out = StringIO()
        err = StringIO()
        kwargs.setdefault("stdout", out)
        kwargs.setdefault("stderr", err)
        call_command("backfill_profile_skills", *args, **kwargs)
        return out.getvalue(), err.getvalue()

    def test_legacy_command_refuses_apply(self):
        from django.core.management.base import CommandError
        with self.assertRaises(CommandError) as ctx:
            self._call("--apply")
        self.assertIn("no longer allowed", str(ctx.exception))

    def test_legacy_command_refuses_refresh_results(self):
        from django.core.management.base import CommandError
        with self.assertRaises(CommandError) as ctx:
            self._call("--refresh-results")
        self.assertIn("no longer supported", str(ctx.exception))

    def test_legacy_command_dry_run_allowed(self):
        output, _ = self._call()
        self.assertIn("DRY RUN only", output)


class ProfileSkillRepairPartialFailureTests(TestCase):
    def setUp(self):
        self.user = make_user("failureuser", "failure@example.test")
        self.profile = CandidateProfile.objects.create(user=self.user, target_country="France")
        self.python = Skill.objects.create(
            canonical_name="Python", slug="python", category="programming_language"
        )
        SkillAlias.objects.create(
            skill=self.python,
            alias="Python",
            normalized_alias=normalize_skill_text("Python"),
        )
        ProfileSkill.objects.create(
            profile=self.profile,
            raw_name="Python",
            normalized_name="python",
            source="cv_upload",
        )

    def _call(self, *args, **kwargs):
        out = StringIO()
        err = StringIO()
        kwargs.setdefault("stdout", out)
        kwargs.setdefault("stderr", err)
        call_command("repair_profile_skill_links", *args, **kwargs)
        return out.getvalue(), err.getvalue()

    @override_settings(DEBUG=True)
    def test_command_exits_nonzero_on_service_error(self):
        from django.core.management.base import CommandError
        out = StringIO()
        err = StringIO()
        with patch(
            "apps.profiles.services.backfill.ProfileSkillMaterializationService.materialize",
            side_effect=RuntimeError("materialization boom"),
        ):
            with self.assertRaises(CommandError) as ctx:
                call_command(
                    "repair_profile_skill_links",
                    "--user-id", str(self.user.pk),
                    "--apply",
                    stdout=out,
                    stderr=err,
                )
        self.assertIn("1 error", str(ctx.exception))
        combined_output = out.getvalue() + err.getvalue()
        self.assertIn("materialization boom", combined_output)
