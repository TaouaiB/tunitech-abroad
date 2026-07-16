"""Tests for the committed skill UID registry file and service.

The registry is the single source of truth for cross-environment
``Skill.skill_uid`` identity. It must be deterministic, append-only,
and contain only valid UUIDv4 values.
"""

import json
import uuid
from collections import Counter
from pathlib import Path

from django.test import SimpleTestCase, TestCase

from apps.skills.services.skill_uid_registry import (
    assert_registry_complete,
    get_skill_uid,
    has_skill_uid,
    registry_canonical_names,
    registry_count,
    registry_entries,
    registry_path,
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
