from datetime import timedelta
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apps.accounts.models import User
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
    SkillExtractionStatus,
    SkillSource,
    SourceType,
)
from apps.matching.models import MatchResult
from apps.matching.services.match_result import MatchResultService
from apps.matching.services.policy_version import RECOMMENDATION_VERSION
from apps.profiles.models import CandidateProfile, ProfileSkill
from apps.profiles.services.backfill import ProfileSkillBackfillService
from apps.recommendations.models import JobRecommendation
from apps.recommendations.services.recommendation import RecommendationService
from apps.skills.models import Skill, SkillAlias, UnmatchedSkillCandidate
from apps.skills.services.normalizer import normalize_skill_text


@override_settings(DEBUG=True)
class ProfileSkillRepairIntegrationTests(TestCase):
    def setUp(self):
        self.python = Skill.objects.create(
            canonical_name="Python",
            slug="python-repair-integration",
            category="programming_language",
        )
        SkillAlias.objects.create(
            skill=self.python,
            alias="Python",
            normalized_alias=normalize_skill_text("Python"),
        )
        self.user, self.profile, self.profile_skill = self._create_repair_user(
            "repair-first", "repair-first@example.test"
        )
        self.active_job = self._create_job("active")

    def _create_repair_user(self, username, email):
        user = User(username=username, email=email)
        user.set_password("pw")
        user.save()
        profile = CandidateProfile.objects.create(
            user=user,
            target_country="France",
            profile_completion_score=80,
            current_level="junior",
            target_roles=["Python Developer"],
            french_level="intermediate",
            english_level="fluent",
            relocation_preference="yes",
            remote_preference="hybrid",
        )
        profile_skill = ProfileSkill.objects.create(
            profile=profile,
            raw_name="Python",
            normalized_name="python",
            source="cv_upload",
        )
        return user, profile, profile_skill

    def _create_job(self, suffix, *, expires_at=None):
        now = timezone.now()
        source = JobSource.objects.create(
            name=f"Repair Source {suffix}",
            slug=f"repair-source-{suffix}",
            source_type=SourceType.FIXTURE,
        )
        raw = RawJobRecord.objects.create(
            source=source,
            source_job_id=f"repair-{suffix}",
            raw_payload_json={},
            payload_hash=f"repair-{suffix}",
            first_seen_at=now,
            last_seen_at=now,
            last_fetched_at=now,
        )
        job = NormalizedJob.objects.create(
            source=source,
            raw_record=raw,
            source_job_id=f"repair-{suffix}",
            title="Python Developer",
            company_name="Repair Corp",
            location="Paris",
            country="France",
            city="Paris",
            contract_type="CDI",
            remote_type=RemoteType.HYBRID,
            job_type=JobType.FULL_TIME_JOB,
            experience_level=ExperienceLevel.JUNIOR,
            description="Build Python services.",
            published_at=now,
            expires_at=expires_at,
            status=JobStatus.ACTIVE,
            skill_extraction_status=SkillExtractionStatus.SUCCESS,
            skill_signal_quality="strong",
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
        NormalizedJobSkill.objects.create(
            job=job,
            skill=self.python,
            requirement_type=RequirementType.REQUIRED,
            source=SkillSource.RULE,
            confidence=1,
        )
        return job

    @staticmethod
    def _call_command(*args):
        stdout = StringIO()
        stderr = StringIO()
        call_command(
            "repair_profile_skill_links",
            *args,
            stdout=stdout,
            stderr=stderr,
        )
        return stdout.getvalue(), stderr.getvalue()

    def test_all_users_partial_refresh_failure_rolls_back_and_continues(self):
        failing_user, _, failing_skill = self._create_repair_user(
            "repair-failing", "repair-failing@example.test"
        )
        later_user, _, later_skill = self._create_repair_user(
            "repair-later", "repair-later@example.test"
        )

        first_match = MatchResultService.create_match_result(self.user, self.active_job)
        failing_match = MatchResultService.create_match_result(failing_user, self.active_job)
        later_match = MatchResultService.create_match_result(later_user, self.active_job)
        failing_match_updated_at = failing_match.updated_at

        now = timezone.now()
        failing_recommendation = JobRecommendation.objects.create(
            user=failing_user,
            profile=failing_user.candidate_profile,
            job=self.active_job,
            fit_score=1,
            ranking_score=1,
            rank=99,
            recommendation_version=RECOMMENDATION_VERSION,
            computed_at=now,
            status="active",
        )
        failing_recommendation_updated_at = failing_recommendation.updated_at

        real_refresh = RecommendationService.refresh_for_user

        def refresh_then_fail(user, trigger_type):
            result = real_refresh(user, trigger_type)
            if user.pk == failing_user.pk:
                raise RuntimeError("forced refresh failure")
            return result

        stdout = StringIO()
        stderr = StringIO()
        with patch(
            "apps.profiles.services.backfill.RecommendationService.refresh_for_user",
            side_effect=refresh_then_fail,
        ):
            with self.assertRaises(CommandError):
                call_command(
                    "repair_profile_skill_links",
                    "--all-users",
                    "--apply",
                    "--refresh-results",
                    stdout=stdout,
                    stderr=stderr,
                )

        self.profile_skill.refresh_from_db()
        failing_skill.refresh_from_db()
        later_skill.refresh_from_db()
        self.assertEqual(self.profile_skill.skill, self.python)
        self.assertIsNone(failing_skill.skill_id)
        self.assertEqual(later_skill.skill, self.python)

        failing_match.refresh_from_db()
        failing_recommendation.refresh_from_db()
        self.assertEqual(failing_match.updated_at, failing_match_updated_at)
        self.assertEqual(failing_recommendation.updated_at, failing_recommendation_updated_at)
        self.assertEqual(failing_recommendation.fit_score, 1)
        self.assertEqual(failing_recommendation.status, "active")

        first_match.refresh_from_db()
        later_match.refresh_from_db()
        self.assertTrue(
            JobRecommendation.objects.filter(user=self.user, job=self.active_job).exists()
        )
        self.assertTrue(
            JobRecommendation.objects.filter(user=later_user, job=self.active_job).exists()
        )
        self.assertGreater(first_match.updated_at, failing_match_updated_at)
        self.assertGreater(later_match.updated_at, failing_match_updated_at)

        output = stdout.getvalue() + stderr.getvalue()
        self.assertIn("users_scanned=3", output)
        self.assertIn("users_changed=2", output)
        self.assertIn("users_refreshed=2", output)
        self.assertIn("recommendations_created=2", output)
        self.assertIn("recommendations_updated=0", output)
        self.assertIn("matches_recomputed=2", output)
        self.assertIn("errors=1", output)
        self.assertIn("forced refresh failure", output)

    def test_repair_command_refreshes_only_current_available_rows_and_is_idempotent(self):
        historical = MatchResultService.create_match_result(self.user, self.active_job)
        current = MatchResultService.create_match_result(self.user, self.active_job)
        historical_updated_at = historical.updated_at
        current_public_id = current.public_id
        current_updated_at = current.updated_at

        expired_job = self._create_job("expired")
        expired_match = MatchResultService.create_match_result(self.user, expired_job)
        expired_job.expires_at = timezone.now() - timedelta(days=1)
        expired_job.save(update_fields=["expires_at"])
        expired_updated_at = expired_match.updated_at

        inactive_job = self._create_job("inactive-source")
        inactive_match = MatchResultService.create_match_result(self.user, inactive_job)
        inactive_job.source.is_active = False
        inactive_job.source.save(update_fields=["is_active"])
        inactive_updated_at = inactive_match.updated_at

        first_output, _ = self._call_command(
            "--user-id",
            str(self.user.pk),
            "--apply",
            "--refresh-results",
        )

        self.assertIn("users_refreshed=1", first_output)
        self.assertIn("recommendations_created=1", first_output)
        self.assertIn("recommendations_updated=0", first_output)
        self.assertIn("matches_recomputed=1", first_output)
        self.assertTrue(
            JobRecommendation.objects.filter(
                user=self.user, job=self.active_job, status="active"
            ).exists()
        )

        historical.refresh_from_db()
        current.refresh_from_db()
        expired_match.refresh_from_db()
        inactive_match.refresh_from_db()
        self.assertEqual(historical.updated_at, historical_updated_at)
        self.assertGreater(current.updated_at, current_updated_at)
        self.assertEqual(current.public_id, current_public_id)
        self.assertEqual(expired_match.updated_at, expired_updated_at)
        self.assertEqual(inactive_match.updated_at, inactive_updated_at)

        second_output, _ = self._call_command(
            "--user-id",
            str(self.user.pk),
            "--apply",
            "--refresh-results",
        )
        self.assertIn("rows_linked=0", second_output)
        self.assertIn("users_refreshed=0", second_output)
        self.assertIn("recommendations_created=0", second_output)
        self.assertIn("recommendations_updated=0", second_output)
        self.assertIn("matches_recomputed=0", second_output)

    def test_repair_makes_no_external_or_unmatched_candidate_writes(self):
        ProfileSkill.objects.create(
            profile=self.profile,
            raw_name="MysterySkillXYZ",
            normalized_name="mysteryskillxyz",
            source="cv_upload",
        )

        with patch(
            "apps.llm.services.client.OpenRouterClient._make_request"
        ) as openrouter_call, patch(
            "apps.jobs.services.france_travail.client.FranceTravailClient.search_offers"
        ) as france_travail_search, patch(
            "apps.jobs.services.france_travail.client.FranceTravailClient.get_offer_detail"
        ) as france_travail_detail:
            self._call_command(
                "--user-id",
                str(self.user.pk),
                "--apply",
                "--refresh-results",
            )

        openrouter_call.assert_not_called()
        france_travail_search.assert_not_called()
        france_travail_detail.assert_not_called()
        self.assertFalse(UnmatchedSkillCandidate.objects.exists())

    def test_profile_skill_locks_do_not_use_nullable_outer_joins(self):
        with CaptureQueriesContext(connection) as queries:
            report = ProfileSkillBackfillService.repair(user=self.user, apply=True)

        self.assertEqual(report.errors, 0)
        profile_skill_selects = [
            query["sql"].upper()
            for query in queries.captured_queries
            if 'FROM "PROFILES_PROFILESKILL"' in query["sql"].upper()
        ]
        self.assertGreaterEqual(len(profile_skill_selects), 2)
        self.assertTrue(all("LEFT OUTER JOIN" not in sql for sql in profile_skill_selects))
