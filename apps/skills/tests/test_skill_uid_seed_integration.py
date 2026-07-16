"""Tests for the seed service integration with the skill UID registry.

The seed service must:
- use the registry UUID for every canonical skill it creates;
- preserve the existing ``skill_uid`` on rows that already match;
- never rotate or rewrite an existing ``skill_uid`` at runtime;
- fail loudly when an existing canonical row carries a UUID that
  does not match the committed registry;
- fail loudly when a legacy canonical row carries a UUID that does
  not match the target registry UUID (the migration must have
  converged the legacy row first);
- remain idempotent across re-runs;
- fail loudly if the registry is missing an entry for a seeded skill;
- roll back the entire seed transaction when a mismatch is detected.

There is no public or private model helper that bypasses the
``Skill.skill_uid`` immutability invariant. Converging a legacy row
on the registry UUID is the responsibility of the unapplied data
migration ``0003_populate_skill_uid``, not the seed.
"""

import uuid

from django.test import TestCase
from django.db import transaction

from apps.skills.models import Skill, SkillAlias
from apps.skills.services.seed import SkillSeedService
from apps.skills.services.skill_uid_registry import (
    get_skill_uid,
    has_skill_uid,
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

    def test_legacy_dotnet_rename_preserves_target_uuid(self):
        # The migration is responsible for assigning the registry
        # UUID to the legacy ``.NET Core`` row before the seed runs.
        # The seed rename only preserves the existing UUID.
        from apps.skills.services.normalizer import normalize_skill_text

        legacy_dotnet = Skill.objects.create(
            canonical_name=".NET Core",
            slug="dotnet-core",
            category="backend",
            skill_uid=get_skill_uid(".NET"),
        )
        legacy_aspnet = Skill.objects.create(
            canonical_name="ASP.NET",
            slug="aspdotnet",
            category="backend",
            skill_uid=get_skill_uid("ASP.NET Core"),
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

        # The legacy rows were renamed in place; their existing
        # ``skill_uid`` is preserved (identity migration, not a
        # rotation).
        renamed_dotnet = Skill.objects.get(canonical_name=".NET")
        self.assertEqual(renamed_dotnet.skill_uid, get_skill_uid(".NET"))
        renamed_aspnet = Skill.objects.get(canonical_name="ASP.NET Core")
        self.assertEqual(
            renamed_aspnet.skill_uid, get_skill_uid("ASP.NET Core")
        )
        # The legacy canonical names are gone
        self.assertFalse(Skill.objects.filter(canonical_name=".NET Core").exists())
        self.assertFalse(Skill.objects.filter(canonical_name="ASP.NET").exists())


class SeedServiceRegistryFailureTests(TestCase):
    """Seed must fail loudly and roll back on any skill_uid drift."""

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

    def test_seed_fails_loudly_on_existing_uuid_drift(self):
        # An existing row with the wrong UUID must abort the seed.
        # This proves the runtime never rotates skill_uid.
        existing = Skill.objects.create(
            canonical_name="Python",
            slug="python",
            category="programming_language",
        )
        # Confirm the row's UUID does NOT match the registry
        self.assertNotEqual(existing.skill_uid, get_skill_uid("Python"))

        with self.assertRaises(ValueError) as ctx:
            SkillSeedService.seed_initial_taxonomy()
        self.assertIn("Python", str(ctx.exception))
        self.assertIn("refuses to rotate", str(ctx.exception))

        # The existing row's UUID is preserved unchanged
        existing.refresh_from_db()
        self.assertNotEqual(existing.skill_uid, get_skill_uid("Python"))

    def test_seed_failure_rolls_back_transaction(self):
        # Pre-existing mismatched row triggers a failure; the entire
        # transaction must roll back so partial alias or skill
        # creations are not visible after the failure.
        Skill.objects.create(
            canonical_name="Python",
            slug="python",
            category="programming_language",
        )
        # Snapshot state before the failed seed
        skills_before = Skill.objects.count()
        aliases_before = SkillAlias.objects.count()
        try:
            with transaction.atomic():
                SkillSeedService.seed_initial_taxonomy()
        except ValueError:
            pass
        # After the failed seed, no additional skills or aliases
        # should be present in the database.
        self.assertEqual(Skill.objects.count(), skills_before)
        self.assertEqual(SkillAlias.objects.count(), aliases_before)

    def test_legacy_dotnet_rename_fails_when_uuid_does_not_match_target(self):
        # Simulate a legacy ``.NET Core`` row whose skill_uid was
        # never converged to the target registry UUID (for example,
        # the data migration was skipped). The seed must abort
        # before mutating the row.
        legacy = Skill.objects.create(
            canonical_name=".NET Core",
            slug="dotnet-core",
            category="backend",
            # Default uuid.uuid4() != get_skill_uid(".NET")
            skill_uid=uuid.uuid4(),
        )

        with self.assertRaises(ValueError) as ctx:
            SkillSeedService.seed_initial_taxonomy()
        self.assertIn(".NET Core", str(ctx.exception))
        self.assertIn("refuses to rotate", str(ctx.exception))

        # The legacy row is left unchanged (rename did not happen)
        legacy.refresh_from_db()
        self.assertEqual(legacy.canonical_name, ".NET Core")
        self.assertNotEqual(legacy.skill_uid, get_skill_uid(".NET"))

    def test_legacy_aspnet_rename_fails_when_uuid_does_not_match_target(self):
        # Equivalent coverage for the ASP.NET -> ASP.NET Core legacy
        # rename. Only exercised when the registry already has the
        # target identity.
        legacy = Skill.objects.create(
            canonical_name="ASP.NET",
            slug="aspdotnet",
            category="backend",
            skill_uid=uuid.uuid4(),
        )

        with self.assertRaises(ValueError) as ctx:
            SkillSeedService.seed_initial_taxonomy()
        self.assertIn("ASP.NET", str(ctx.exception))
        self.assertIn("refuses to rotate", str(ctx.exception))

        legacy.refresh_from_db()
        self.assertEqual(legacy.canonical_name, "ASP.NET")
        self.assertNotEqual(legacy.skill_uid, get_skill_uid("ASP.NET Core"))

    def test_legacy_dotnet_rename_succeeds_when_uuid_matches(self):
        # The migration's responsibility: assign the target registry
        # UUID to the legacy row. The seed must then rename in place
        # and preserve the UUID.
        from apps.skills.services.normalizer import normalize_skill_text

        legacy = Skill.objects.create(
            canonical_name=".NET Core",
            slug="dotnet-core",
            category="backend",
            skill_uid=get_skill_uid(".NET"),
        )
        SkillAlias.objects.create(
            skill=legacy,
            alias=".NET Core",
            normalized_alias=normalize_skill_text(".NET Core"),
        )

        SkillSeedService.seed_initial_taxonomy()

        renamed = Skill.objects.get(canonical_name=".NET")
        self.assertEqual(renamed.skill_uid, get_skill_uid(".NET"))
        # Alias was preserved on the renamed skill
        alias = SkillAlias.objects.get(
            normalized_alias=normalize_skill_text(".NET Core")
        )
        self.assertEqual(alias.skill.canonical_name, ".NET")

    def test_two_row_legacy_scenario_preserves_both_uuids(self):
        # Old row and target row both exist. Preserve both UUIDs.
        # The legacy old row's UUID is the tombstone UUID (would be
        # assigned by the migration in production).
        LEGACY_TOMBSTONE_DOTNET = uuid.UUID(
            "23b14296-d0ce-4897-a7fc-1489331f86de"
        )

        old_row = Skill.objects.create(
            canonical_name=".NET Core",
            slug="dotnet-core",
            category="backend",
            skill_uid=LEGACY_TOMBSTONE_DOTNET,
        )
        target_row = Skill.objects.create(
            canonical_name=".NET",
            slug="dotnet",
            category="backend",
            skill_uid=get_skill_uid(".NET"),
        )

        SkillSeedService.seed_initial_taxonomy()

        # The target row keeps its registry UUID
        target_after = Skill.objects.get(canonical_name=".NET")
        self.assertEqual(target_after.skill_uid, get_skill_uid(".NET"))
        # The old row was deactivated, not deleted
        old_after = Skill.objects.get(pk=old_row.pk)
        self.assertFalse(old_after.is_active)
        # Its UUID is preserved (not rotated to the target's UUID)
        self.assertEqual(old_after.skill_uid, LEGACY_TOMBSTONE_DOTNET)

    def test_two_row_legacy_scenario_fails_on_target_uuid_drift(self):
        # Old row and target row both exist. If the target's UUID
        # does not match the registry, the seed must abort.
        LEGACY_TOMBSTONE_DOTNET = uuid.UUID(
            "23b14296-d0ce-4897-a7fc-1489331f86de"
        )
        Skill.objects.create(
            canonical_name=".NET Core",
            slug="dotnet-core",
            category="backend",
            skill_uid=LEGACY_TOMBSTONE_DOTNET,
        )
        target_with_wrong_uuid = Skill.objects.create(
            canonical_name=".NET",
            slug="dotnet",
            category="backend",
            skill_uid=uuid.uuid4(),  # wrong
        )

        with self.assertRaises(ValueError) as ctx:
            SkillSeedService.seed_initial_taxonomy()
        self.assertIn("refuses to rotate", str(ctx.exception))

        # Both rows left unchanged
        old_row = Skill.objects.get(canonical_name=".NET Core")
        self.assertEqual(old_row.skill_uid, LEGACY_TOMBSTONE_DOTNET)
        target_row = Skill.objects.get(canonical_name=".NET")
        self.assertEqual(target_row.skill_uid, target_with_wrong_uuid.skill_uid)
