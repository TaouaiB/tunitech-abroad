from django.test import TestCase
from django.core.management import call_command
from io import StringIO

from apps.skills.models import Skill, SkillAlias, UnmatchedSkillCandidate
from apps.skills.services.ignored import IgnoredSkillService
from apps.skills.services.normalizer import SkillNormalizerService

class IgnoreRulesTests(TestCase):
    def test_exact_terms(self):
        self.assertTrue(IgnoredSkillService.is_ignored("informatique"))
        self.assertTrue(IgnoredSkillService.is_ignored("e commerce"))
        self.assertTrue(IgnoredSkillService.is_ignored("pedagogie"))
        self.assertTrue(IgnoredSkillService.is_ignored("bac pro mspc"))
        self.assertTrue(IgnoredSkillService.is_ignored("secteur industriel"))
        self.assertTrue(IgnoredSkillService.is_ignored("asset management"))
        self.assertFalse(IgnoredSkillService.is_ignored("python"))
        self.assertFalse(IgnoredSkillService.is_ignored("java"))

    def test_prefix_patterns(self):
        self.assertTrue(IgnoredSkillService.is_ignored("bac pro systèmes électroniques numériques"))
        self.assertTrue(IgnoredSkillService.is_ignored("secteur aéronautique"))
        self.assertTrue(IgnoredSkillService.is_ignored("experience in the aerospace sector"))
        self.assertTrue(IgnoredSkillService.is_ignored("experience secteur defense"))
        self.assertFalse(IgnoredSkillService.is_ignored("bac"))
        self.assertFalse(IgnoredSkillService.is_ignored("secteur"))
        self.assertFalse(IgnoredSkillService.is_ignored("experience in python"))

    def test_ignored_terms_do_not_become_pending_candidates(self):
        result = SkillNormalizerService.normalize_many(["Pédagogie"], source_type="job")

        self.assertEqual(result.canonical_skills, [])
        candidate = UnmatchedSkillCandidate.objects.get(normalized_text="pedagogie", source_type="job")
        self.assertEqual(candidate.status, "ignored")

    def test_reconcile_dry_run_and_apply_curated_decisions_only(self):
        skill = Skill.objects.create(canonical_name="Agile", slug="agile")
        SkillAlias.objects.create(skill=skill, alias="Agile Methodologies", normalized_alias="agile methodologies")

        alias_candidate = UnmatchedSkillCandidate.objects.create(
            raw_skill_text="Agile Methodologies",
            normalized_text="agile methodologies",
            source_type="job",
            status="pending",
        )
        ignored_candidate = UnmatchedSkillCandidate.objects.create(
            raw_skill_text="Pédagogie",
            normalized_text="pedagogie",
            source_type="job",
            status="pending",
        )
        keep_pending_candidate = UnmatchedSkillCandidate.objects.create(
            raw_skill_text="Électronique",
            normalized_text="electronique",
            source_type="job",
            status="pending",
        )

        out = StringIO()
        call_command("reconcile_unmatched_skill_candidates", "--dry-run", stdout=out)
        alias_candidate.refresh_from_db()
        ignored_candidate.refresh_from_db()
        keep_pending_candidate.refresh_from_db()
        self.assertEqual(alias_candidate.status, "pending")
        self.assertEqual(ignored_candidate.status, "pending")
        self.assertEqual(keep_pending_candidate.status, "pending")

        out = StringIO()
        call_command("reconcile_unmatched_skill_candidates", "--apply", stdout=out)
        alias_candidate.refresh_from_db()
        ignored_candidate.refresh_from_db()
        keep_pending_candidate.refresh_from_db()

        self.assertEqual(alias_candidate.status, "mapped")
        self.assertEqual(alias_candidate.mapped_skill, skill)
        self.assertEqual(ignored_candidate.status, "ignored")
        self.assertEqual(keep_pending_candidate.status, "pending")
