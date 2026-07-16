"""Tests for the seed service integration with the skill UID registry.

The seed service must:
- use the registry UUID for every canonical skill it creates;
- preserve the existing ``skill_uid`` on rows that already match;
- converge legacy canonical renames onto the registry UUID via the
  controlled ``set_skill_uid_for_rename`` helper;
- remain idempotent across re-runs;
- fail loudly if the registry is missing an entry for a seeded skill.
"""

import uuid

from django.test import TestCase

from apps.skills.models import Skill, SkillAlias
from apps.skills.services.seed import SkillSeedService
from apps.skills.services.skill_uid_registry import (
    get_skill_uid,
    has_skill_uid,
    registry_canonical_names,
    reset_cache,
)


class SeedServiceRegistryIntegrationTests(TestCase):
    """``SkillSeedService.seed_initial_taxonomy`` honours the registry."""

    def setUp(self):
        reset_cache()

    def test_fresh_seed_assigns_registry_uuids(self):
        result = SkillSeedService.seed_initial_taxonomy()
        self.assertGreater(result["skills_created"], 100)

        # Every seeded canonical_name must have its registry UUID
        seeded_qs = Skill.objects.filter(source="seed")
        mismatches = []
        for skill in seeded_qs:
            if not has_skill_uid(skill.canonical_name):
                mismatches.append(("missing-in-registry", skill.canonical_name))
                continue
            expected = get_skill_uid(skill.canonical_name)
            if skill.skill_uid != expected:
                mismatches.append(
                    (
                        "wrong-uuid",
                        skill.canonical_name,
                        str(skill.skill_uid),
                        str(expected),
                    )
                )
        self.assertEqual(mismatches, [], f"Registry mismatches: {mismatches}")

    def test_repeated_seed_is_idempotent_and_preserves_uuids(self):
        SkillSeedService.seed_initial_taxonomy()
        first_uuids = {
            s.canonical_name: s.skill_uid
            for s in Skill.objects.filter(source="seed")
        }

        result = SkillSeedService.seed_initial_taxonomy()
        self.assertEqual(result["skills_created"], 0)
        self.assertEqual(result["aliases_created"], 0)

        second_uuids = {
            s.canonical_name: s.skill_uid
            for s in Skill.objects.filter(source="seed")
        }
        self.assertEqual(first_uuids, second_uuids)

    def test_seed_repeated_does_not_rotate_uuids(self):
        SkillSeedService.seed_initial_taxonomy()
        first_uuids = list(
            Skill.objects.filter(source="seed").values_list("skill_uid", flat=True)
        )
        # Run 3 more times
        for _ in range(3):
            SkillSeedService.seed_initial_taxonomy()
        last_uuids = list(
            Skill.objects.filter(source="seed").values_list("skill_uid", flat=True)
        )
        self.assertEqual(sorted(first_uuids), sorted(last_uuids))

    def test_seed_aligns_legacy_dotnet_rename_with_registry(self):
        from apps.skills.services.normalizer import normalize_skill_text

        # Simulate the legacy '.NET Core' row that exists in older databases
        legacy_dotnet = Skill.objects.create(
            canonical_name=".NET Core",
            slug="dotnet-core",
            category="backend",
        )
        legacy_aspnet = Skill.objects.create(
            canonical_name="ASP.NET",
            slug="aspdotnet",
            category="backend",
        )
        SkillAlias.objects.create(
            skill=legacy_dotnet,
            alias=".NET Core",
            normalized_alias=normalize_skill_text(".NET Core"),
        )
        SkillAlias.objects.create(
            skill=legacy_aspnet,
            alias="ASP.NET",
            normalized_alias=normalize_skill_text("ASP.NET"),
        )

        SkillSeedService.seed_initial_taxonomy()

        # The legacy rows were renamed in place and now carry the registry UUID
        renamed_dotnet = Skill.objects.get(canonical_name=".NET")
        self.assertEqual(renamed_dotnet.skill_uid, get_skill_uid(".NET"))
        renamed_aspnet = Skill.objects.get(canonical_name="ASP.NET Core")
        self.assertEqual(
            renamed_aspnet.skill_uid, get_skill_uid("ASP.NET Core")
        )
        # The legacy canonical names are gone
        self.assertFalse(Skill.objects.filter(canonical_name=".NET Core").exists())
        self.assertFalse(Skill.objects.filter(canonical_name="ASP.NET").exists())

    def test_seed_aligns_existing_row_with_registry_uuid(self):
        # Pre-existing row created by a different code path with a random UUID
        Skill.objects.create(
            canonical_name="Python",
            slug="python",
            category="programming_language",
        )
        # Run the seed
        SkillSeedService.seed_initial_taxonomy()
        python = Skill.objects.get(canonical_name="Python")
        self.assertEqual(python.skill_uid, get_skill_uid("Python"))


class SeedServiceRegistryFailureTests(TestCase):
    """Seed must fail safely when the registry is missing an entry."""

    def setUp(self):
        reset_cache()

    def test_seed_fails_loudly_when_registry_missing_entry(self):
        from unittest.mock import patch
        from apps.skills.services import seed as seed_module
        from apps.skills.services.skill_uid_registry import has_skill_uid as real_has

        def fake_has(name):
            if name == "Python":
                return False
            return real_has(name)

        with patch.object(seed_module, "has_skill_uid", side_effect=fake_has):
            with self.assertRaises(ValueError) as ctx:
                SkillSeedService.seed_initial_taxonomy()
            self.assertIn("Python", str(ctx.exception))

    def test_legacy_dotnet_rename_keeps_aliases(self):
        from apps.skills.services.normalizer import normalize_skill_text

        legacy = Skill.objects.create(
            canonical_name=".NET Core", slug="dotnet-core", category="backend"
        )
        SkillAlias.objects.create(
            skill=legacy,
            alias=".NET Core",
            normalized_alias=normalize_skill_text(".NET Core"),
        )
        SkillSeedService.seed_initial_taxonomy()
        alias = SkillAlias.objects.get(normalized_alias=normalize_skill_text(".NET Core"))
        self.assertEqual(alias.skill.canonical_name, ".NET")
