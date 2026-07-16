"""Tests for the committed skill UID registry file and service.

The registry is the single source of truth for cross-environment
``Skill.skill_uid`` identity. It must be deterministic, append-only,
contain only valid UUIDv4 values, and declare explicit provenance
for every non-seed canonical entry.
"""

import ast
import importlib
import json
import uuid
from collections import Counter
from pathlib import Path

from django.test import SimpleTestCase, TestCase

from apps.skills.services.skill_uid_registry import (
    approved_non_seed_canonical_names,
    assert_registry_complete,
    get_skill_uid,
    has_skill_uid,
    is_approved_non_seed_canonical,
    registry_canonical_names,
    registry_count,
    registry_entries,
    registry_path,
    require_skill_uid,
    registry_version,
    reset_cache,
)


class SkillUidRegistryFileTests(SimpleTestCase):
    """Validate the on-disk registry JSON."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.path = registry_path()
        with cls.path.open("r", encoding="utf-8") as handle:
            cls.data = json.load(handle)

    def test_registry_file_exists(self):
        self.assertTrue(self.path.exists())
        self.assertEqual(self.path.name, "skill_uid_registry_v1.json")

    def test_registry_top_level_shape(self):
        self.assertEqual(self.data["version"], 1)
        self.assertIn("description", self.data)
        self.assertIn("skills", self.data)
        self.assertIsInstance(self.data["skills"], list)

    def test_every_entry_has_canonical_name_and_uuid(self):
        for entry in self.data["skills"]:
            self.assertIn("canonical_name", entry)
            self.assertIn("skill_uid", entry)
            self.assertIsInstance(entry["canonical_name"], str)
            self.assertTrue(entry["canonical_name"])
            self.assertIsInstance(entry["skill_uid"], str)
            self.assertTrue(entry["skill_uid"])

    def test_every_uuid_is_valid_v4(self):
        for entry in self.data["skills"]:
            u = uuid.UUID(entry["skill_uid"])
            self.assertEqual(
                u.version,
                4,
                f"Non-v4 UUID for {entry['canonical_name']!r}: {entry['skill_uid']}",
            )
            # RFC 4122 variant bits: 10xx
            self.assertEqual(u.bytes[8] & 0xC0, 0x80)
            # RFC 4122 version bits
            self.assertEqual(u.bytes[6] & 0xF0, 0x40)

    def test_canonical_names_are_unique(self):
        names = [e["canonical_name"] for e in self.data["skills"]]
        counts = Counter(names)
        dups = {k: v for k, v in counts.items() if v > 1}
        self.assertEqual(dups, {}, f"Duplicate canonical names: {dups}")

    def test_uuids_are_unique(self):
        uuids = [e["skill_uid"] for e in self.data["skills"]]
        counts = Counter(uuids)
        dups = {k: v for k, v in counts.items() if v > 1}
        self.assertEqual(dups, {}, f"Duplicate UUIDs: {dups}")

    def test_deterministic_ordering(self):
        names = [e["canonical_name"] for e in self.data["skills"]]
        self.assertEqual(names, sorted(names))

    def test_count_matches_entries(self):
        self.assertEqual(self.data["count"], len(self.data["skills"]))
        self.assertEqual(self.data["count"], 522)

    def test_declares_approved_non_seed_provenance(self):
        self.assertIn("approved_non_seed_canonical_names", self.data)
        self.assertIsInstance(self.data["approved_non_seed_canonical_names"], list)

    def test_approved_non_seed_canonical_count_matches(self):
        declared = self.data.get("approved_non_seed_canonical_count")
        actual = len(self.data.get("approved_non_seed_canonical_names", []))
        self.assertEqual(declared, actual)
        self.assertEqual(actual, 14)

    def test_invalid_language_artifact_is_not_canonical(self):
        names = {entry["canonical_name"] for entry in self.data["skills"]}
        values = {entry["skill_uid"] for entry in self.data["skills"]}
        approved = set(self.data["approved_non_seed_canonical_names"])
        self.assertNotIn("Langues non précisées", names)
        self.assertNotIn("Langues non précisées", approved)
        self.assertNotIn("a380962e-299b-4583-9c90-b0c0a35367ea", values)

    def test_registry_generation_wording_is_factual(self):
        wording = f"{self.data['description']} {self.data['generator']}".lower()
        self.assertNotIn("fixed seed", wording)
        self.assertNotIn("fixed-seed", wording)
        self.assertIn("generated once", wording)
        self.assertIn("committed immutable identities", wording)


class SkillUidRegistryServiceTests(SimpleTestCase):
    """Validate the registry service API."""

    def setUp(self):
        reset_cache()

    def test_registry_version(self):
        self.assertEqual(registry_version(), 1)

    def test_registry_count_matches_file(self):
        with registry_path().open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        self.assertEqual(registry_count(), len(data["skills"]))

    def test_registry_canonical_names_deterministic(self):
        names1 = registry_canonical_names()
        names2 = registry_canonical_names()
        self.assertEqual(names1, names2)
        self.assertEqual(list(names1), sorted(names1))

    def test_get_skill_uid_returns_uuid(self):
        for name in registry_canonical_names()[:5]:
            uid = get_skill_uid(name)
            self.assertIsInstance(uid, uuid.UUID)
            self.assertEqual(uid.version, 4)

    def test_get_skill_uid_matches_file(self):
        with registry_path().open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        for entry in data["skills"][:25]:
            self.assertEqual(
                str(get_skill_uid(entry["canonical_name"])),
                entry["skill_uid"],
            )

    def test_get_skill_uid_missing_raises(self):
        with self.assertRaises(KeyError):
            get_skill_uid("Definitely Not A Canonical Skill Name 9999")

    def test_require_skill_uid_missing_raises_clearly(self):
        with self.assertRaisesRegex(ValueError, "required canonical skill"):
            require_skill_uid("Definitely Not A Canonical Skill Name 9999")

    def test_has_skill_uid(self):
        self.assertTrue(has_skill_uid("Python"))
        self.assertTrue(has_skill_uid("PostgreSQL"))
        self.assertFalse(has_skill_uid("Definitely Not A Canonical Skill Name 9999"))

    def test_registry_entries_preserve_order(self):
        entries = registry_entries()
        names = [n for n, _ in entries]
        self.assertEqual(names, sorted(names))
        for _, raw in entries:
            uuid.UUID(raw)  # must be parseable

    def test_assert_registry_complete_accepts_all_known(self):
        # Should not raise for any name that is in the registry
        assert_registry_complete(registry_canonical_names())

    def test_assert_registry_complete_rejects_missing(self):
        with self.assertRaises(ValueError) as ctx:
            assert_registry_complete(["Python", "Definitely Not A Canonical Skill Name 9999"])
        self.assertIn("Definitely Not A Canonical Skill Name 9999", str(ctx.exception))

    def test_approved_non_seed_canonical_names_sorted_and_unique(self):
        names = approved_non_seed_canonical_names()
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(list(names), sorted(names))

    def test_every_approved_non_seed_name_is_in_registry(self):
        names_in_registry = set(registry_canonical_names())
        for n in approved_non_seed_canonical_names():
            self.assertIn(
                n, names_in_registry,
                f"approved_non_seed_canonical_names entry {n!r} "
                "is not present in registry 'skills'",
            )

    def test_approved_non_seed_names_have_no_overlap_with_seed(self):
        # The seed-path canonical names must not appear in the
        # approved_non_seed_canonical_names list.
        # This test runs the seed in a test database; therefore it
        # requires ``TestCase`` (the surrounding class is
        # ``SimpleTestCase`` so the actual call is done via a
        # separate ``TestCase`` below).
        # We use a guard attribute to re-invoke this logic from
        # the dedicated ``TestCase`` subclass.
        pass

    def test_is_approved_non_seed_canonical_lookup(self):
        self.assertTrue(is_approved_non_seed_canonical("Crystal Reports"))
        self.assertTrue(is_approved_non_seed_canonical("n8n"))
        self.assertFalse(is_approved_non_seed_canonical("Python"))
        self.assertFalse(is_approved_non_seed_canonical("Definitely Not A Canonical Skill Name 9999"))

    def test_json_registry_equals_embedded_migration_registry(self):
        # The registry embedded in the unapplied migration must be
        # exactly the same as the committed JSON registry.
        from apps.skills.services import skill_uid_registry as registry_module
        registry_path_obj = Path(registry_module.__file__).resolve().parent.parent
        migration_path = (
            registry_path_obj
            / "migrations"
            / "0003_populate_skill_uid.py"
        )
        with migration_path.open("r", encoding="utf-8") as handle:
            tree = ast.parse(handle.read())
        embedded = None
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if (
                        isinstance(target, ast.Name)
                        and target.id == "REGISTRY_UUID_BY_CANONICAL"
                    ):
                        embedded = ast.literal_eval(node.value)
                        break
        self.assertIsNotNone(embedded, "REGISTRY_UUID_BY_CANONICAL not found in migration")
        with registry_path().open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        json_map = {
            s["canonical_name"]: s["skill_uid"] for s in data["skills"]
        }
        self.assertEqual(embedded, json_map)

    def test_invalid_artifact_tombstone_is_unique_v4(self):
        migration = importlib.import_module(
            "apps.skills.migrations.0003_populate_skill_uid"
        )
        invalid = migration.INVALID_ARTIFACT_UUID_BY_CANONICAL
        self.assertEqual(
            set(invalid),
            {"Langues non précisées"},
        )
        invalid_uids = {uuid.UUID(raw) for raw in invalid.values()}
        legacy_uids = {
            uuid.UUID(raw)
            for raw in migration.LEGACY_TOMBSTONE_UUID_BY_OLD.values()
        }
        registry_uids = {uuid.UUID(raw) for _, raw in registry_entries()}
        self.assertTrue(all(uid.version == 4 for uid in invalid_uids))
        self.assertFalse(invalid_uids & legacy_uids)
        self.assertFalse(invalid_uids & registry_uids)


class SkillUidRegistryProvenanceDbTests(TestCase):
    """Provenance tests that require the default database (run the seed)."""

    def setUp(self):
        from apps.skills.services.skill_uid_registry import reset_cache
        reset_cache()

    def test_approved_non_seed_names_have_no_overlap_with_seed(self):
        from apps.skills.models import Skill
        from apps.skills.services.seed import SkillSeedService
        SkillSeedService.seed_initial_taxonomy()
        seeded = set(
            Skill.objects.filter(source="seed").values_list(
                "canonical_name", flat=True
            )
        )
        approved = set(approved_non_seed_canonical_names())
        overlap = seeded & approved
        self.assertEqual(
            overlap, set(),
            f"approved_non_seed_canonical_names overlaps with seeded names: {overlap}",
        )

    def test_registry_names_equal_seed_union_approved_non_seed(self):
        from apps.skills.models import Skill
        from apps.skills.services.seed import SkillSeedService
        SkillSeedService.seed_initial_taxonomy()
        seeded = set(
            Skill.objects.filter(source="seed").values_list(
                "canonical_name", flat=True
            )
        )
        approved = set(approved_non_seed_canonical_names())
        registry = set(registry_canonical_names())
        self.assertEqual(
            registry, seeded | approved,
            "Registry names must exactly equal seed names UNION approved_non_seed_canonical_names",
        )
        self.assertEqual(len(seeded), 508)
        self.assertEqual(len(approved), 14)
        self.assertEqual(len(registry), 522)
        self.assertNotIn("Langues non précisées", seeded)


class SkillUidRegistrySeedAlignmentTests(TestCase):
    """The registry must cover every canonical skill produced by the seed path.

    These tests call the seed service in a test database to enumerate
    canonical names and assert the registry covers them all.
    """

    def setUp(self):
        from apps.skills.services.skill_uid_registry import reset_cache
        reset_cache()

    def test_seed_canonical_names_are_in_registry(self):
        from apps.skills.services.seed import SkillSeedService
        result = SkillSeedService.seed_initial_taxonomy()
        # The seed must succeed
        self.assertGreater(result["skills_created"], 100)

        # Every canonical_name produced by the seed must be in the registry
        from apps.skills.models import Skill
        seeded = set(
            Skill.objects.filter(source="seed").values_list("canonical_name", flat=True)
        )
        missing = [n for n in seeded if not has_skill_uid(n)]
        self.assertEqual(missing, [], f"Seed canonicals missing from registry: {missing}")
