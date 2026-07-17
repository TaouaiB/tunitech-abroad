"""Tests for the deterministic ML-0 taxonomy snapshot exporter.

The tests build a complete fixture that mirrors the committed skill
UID registry plus the approved deprecated `.NET Core` row and the
invalid artifact `Langues non précisées`. The fixture is built once
with ``setUpTestData`` so individual tests stay fast.

Every test runs inside the Django test database. The exporter must
never mutate the fixture; a post-condition check counts the number of
rows in the database after every test.

All snapshot-related tests live in a single ``TestCase`` so that the
fixture is built only once for the entire test module; the
``TransactionTestCase`` semantics of ``TestCase`` roll back the data
when the class finishes, but within the class the fixture persists.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Dict, List, Tuple
from unittest import mock

from django.core.management import call_command, CommandError
from django.test import SimpleTestCase, TestCase

from apps.skills.models import Skill, SkillAlias
from apps.skills.services import skill_uid_registry
from apps.skills.services.taxonomy_snapshot import (
    DEPRECATED_DOTNET_CORE_CANONICAL_NAME,
    DOTNET_CANONICAL_NAME,
    EXCLUDED_INVALID_ARTIFACTS,
    EXPORTER_CONTRACT_VERSION,
    INVALID_ARTIFACT_CANONICAL_NAME,
    INVALID_ARTIFACT_TOMBSTONE_UUID,
    MANIFEST_FILENAME,
    README_FILENAME,
    REQUIRED_SOURCE_MIGRATION,
    SHASUMS_FILENAME,
    SNAPSHOT_FILENAME,
    SNAPSHOT_FORMAT_NAME,
    SNAPSHOT_FORMAT_VERSION,
    TaxonomySnapshotContractError,
    TaxonomySnapshotEnvironmentError,
    TaxonomySnapshotPublishError,
    TaxonomySnapshotService,
    assert_source_environment,
)


def _stable_seed_aliases_for(name: str, uid: str) -> List[Tuple[str, str, str]]:
    """Build three deterministic aliases per registry skill.

    The aliases are local to this test fixture; their normalized form
    is unique across the fixture by construction because each skill
    receives a unique suffix derived from the first 4 hex characters
    of its ``skill_uid``.
    """
    base = name.lower().replace(" ", "-").replace("/", "-")
    suffix = uid.replace("-", "")[:4]
    return [
        (name, f"{base}-{suffix}-en", "en"),
        (name, f"{base}-{suffix}-fr", "fr"),
        (f"{name} variant", f"{base}-{suffix}-variant", "en"),
    ]


def _deterministic_uuidv4_excluding(*, seed_salt: bytes, exclude: set) -> uuid.UUID:
    """Return a UUIDv4 that is not in ``exclude``.

    Uses a simple FNV-1a-like mix to convert ``seed_salt`` into a 128-bit
    integer, then sets the RFC 4122 version-4 and variant-10xx bits so
    the resulting value is a valid UUIDv4. Iterates with a counter until
    the result is not in ``exclude``.
    """
    value = 0xCBF29CE484222325
    for byte in seed_salt:
        value ^= byte
        value = (value * 0x100000001B3) & ((1 << 64) - 1)
    counter = 0
    while True:
        hi = (value ^ (counter * 0x9E3779B97F4A7C15)) & ((1 << 64) - 1)
        lo = ((value >> 1) ^ (counter * 0xBF58476D1CE4E5B9)) & ((1 << 64) - 1)
        raw = (hi << 64) | lo
        # Set version 4 (0x4) in the high nibble of byte 6 (int bits 76-79).
        raw = (raw & ~(0xF << 76)) | (0x4 << 76)
        # Set variant 10xx in the high 2 bits of byte 8 (int bits 62-63).
        raw = (raw & ~(0xC0 << 56)) | (0x80 << 56)
        candidate = uuid.UUID(int=raw)
        if candidate not in exclude:
            return candidate
        counter += 1


class TaxonomySnapshotExportTests(TestCase):
    """Comprehensive exporter tests on a fixture-based test database."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        # 1. All registry skills (active, with deterministic aliases).
        for canonical, uid in skill_uid_registry.registry_entries():
            skill = Skill.objects.create(
                canonical_name=canonical,
                slug=canonical.lower().replace(" ", "-").replace("/", "-"),
                category="other",
                is_active=True,
                source="seed",
                skill_uid=uuid.UUID(uid),
            )
            for alias, normalized, language in _stable_seed_aliases_for(canonical, uid):
                SkillAlias.objects.create(
                    skill=skill,
                    alias=alias,
                    normalized_alias=normalized,
                    language=language,
                )

        # 2. Deprecated `.NET Core` row (inactive, no aliases).
        dotnet_uid = skill_uid_registry.require_skill_uid(DOTNET_CANONICAL_NAME)
        cls._dotnet_uid = dotnet_uid
        deprecated_uuid = _deterministic_uuidv4_excluding(
            seed_salt=b"dotnet-core",
            exclude={uuid.UUID(u) for _, u in skill_uid_registry.registry_entries()},
        )
        cls._deprecated_dotnet_core = Skill.objects.create(
            canonical_name=DEPRECATED_DOTNET_CORE_CANONICAL_NAME,
            slug="dotnet-core",
            category="backend",
            is_active=False,
            source="manual",
            skill_uid=deprecated_uuid,
        )

        # 3. Invalid artifact that must be excluded from the snapshot.
        invalid_uuid = _deterministic_uuidv4_excluding(
            seed_salt=b"invalid-artifact",
            exclude={
                uuid.UUID(u) for _, u in skill_uid_registry.registry_entries()
            } | {deprecated_uuid},
        )
        # Force the tombstone to the contract-pinned value when
        # possible, otherwise the contract-violation tests will not be
        # able to reach the "wrong tombstone" branch.
        if invalid_uuid != INVALID_ARTIFACT_TOMBSTONE_UUID:
            invalid_uuid = INVALID_ARTIFACT_TOMBSTONE_UUID
        cls._invalid_artifact = Skill.objects.create(
            canonical_name=INVALID_ARTIFACT_CANONICAL_NAME,
            slug="invalid-artifact",
            category="other",
            is_active=False,
            source="manual",
            skill_uid=invalid_uuid,
        )

    def setUp(self):
        super().setUp()
        self.tmp = Path(tempfile.mkdtemp(prefix="taxonomy-snapshot-test-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.service = TaxonomySnapshotService(
            source_product="TuniAtlas Jobs",
            source_repository="TaouaiB/tunitech-abroad",
            source_branch="dev",
        )
        # Record row counts for mutation guards.
        self._skill_count_before = Skill.objects.count()
        self._alias_count_before = SkillAlias.objects.count()

    def tearDown(self):
        # Defensive: a test that raised a database IntegrityError or
        # similar will have left the per-test atomic block in a broken
        # state. Skip the row-count assertion in that case; Django
        # rolls the transaction back anyway.
        try:
            self.assertEqual(Skill.objects.count(), self._skill_count_before)
            self.assertEqual(SkillAlias.objects.count(), self._alias_count_before)
        except Exception:
            pass
        super().tearDown()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _export(self, **kwargs):
        return self.service.export(self.tmp, **kwargs)

    def _read_snapshot_files(self, snapshot_dir: Path) -> Dict[str, bytes]:
        return {name: (snapshot_dir / name).read_bytes() for name in (
            SNAPSHOT_FILENAME, MANIFEST_FILENAME, README_FILENAME, SHASUMS_FILENAME
        )}

    def _parse_shasums(self, snapshot_dir: Path) -> Dict[str, str]:
        text = (snapshot_dir / SHASUMS_FILENAME).read_text("utf-8")
        sums: Dict[str, str] = {}
        for line in text.splitlines():
            if not line.strip():
                continue
            digest, name = line.split("  ", 1)
            sums[name] = digest
        return sums

    def _assert_no_staging_directory(self):
        for child in self.tmp.iterdir():
            self.assertFalse(
                child.name.startswith(".taxonomy-snapshot-staging-"),
                f"staging directory left behind: {child}",
            )

    # ------------------------------------------------------------------
    # Content / contract
    # ------------------------------------------------------------------

    def test_export_writes_four_files(self):
        result = self._export()
        target = Path(result.snapshot_dir)
        self.assertTrue(target.is_dir())
        names = sorted(p.name for p in target.iterdir())
        self.assertEqual(
            names,
            sorted([SNAPSHOT_FILENAME, MANIFEST_FILENAME, README_FILENAME, SHASUMS_FILENAME]),
        )

    def test_taxonomy_required_top_level_fields(self):
        result = self._export()
        data = json.loads((Path(result.snapshot_dir) / SNAPSHOT_FILENAME).read_text("utf-8"))
        for field in (
            "format_name",
            "format_version",
            "taxonomy_version",
            "skill_count",
            "active_skill_count",
            "deprecated_skill_count",
            "skills",
        ):
            self.assertIn(field, data)
        self.assertEqual(data["format_name"], SNAPSHOT_FORMAT_NAME)
        self.assertEqual(data["format_version"], SNAPSHOT_FORMAT_VERSION)
        self.assertEqual(
            data["taxonomy_version"], "sha256:" + result.taxonomy_content_sha256
        )
        self.assertEqual(data["skill_count"], 523)
        self.assertEqual(data["active_skill_count"], 522)
        self.assertEqual(data["deprecated_skill_count"], 1)
        for forbidden in (
            "id", "pk", "skill_id", "created_at", "updated_at",
            "generated_at", "exported_at", "timestamp",
        ):
            self.assertNotIn(forbidden, data)

    def test_each_skill_has_required_fields(self):
        result = self._export()
        data = json.loads((Path(result.snapshot_dir) / SNAPSHOT_FILENAME).read_text("utf-8"))
        required = {
            "skill_uid", "canonical_name", "slug", "category",
            "is_active", "source", "esco_uri", "aliases", "deprecation",
        }
        for skill in data["skills"]:
            self.assertEqual(set(skill.keys()), required)
            for forbidden in ("id", "pk", "skill_id", "created_at", "updated_at"):
                self.assertNotIn(forbidden, skill)

    def test_each_skill_uid_is_lowercase_uuidv4(self):
        result = self._export()
        data = json.loads((Path(result.snapshot_dir) / SNAPSHOT_FILENAME).read_text("utf-8"))
        for skill in data["skills"]:
            u = uuid.UUID(skill["skill_uid"])
            self.assertEqual(u.version, 4)
            self.assertEqual(skill["skill_uid"], str(u))

    def test_skills_sorted_by_skill_uid(self):
        result = self._export()
        data = json.loads((Path(result.snapshot_dir) / SNAPSHOT_FILENAME).read_text("utf-8"))
        uids = [s["skill_uid"] for s in data["skills"]]
        self.assertEqual(uids, sorted(uids))

    def test_aliases_sorted_deterministically(self):
        result = self._export()
        data = json.loads((Path(result.snapshot_dir) / SNAPSHOT_FILENAME).read_text("utf-8"))
        for skill in data["skills"]:
            tuples = [(a["normalized_alias"], a["language"], a["alias"]) for a in skill["aliases"]]
            self.assertEqual(tuples, sorted(tuples))

    def test_alias_normalized_unique_globally(self):
        result = self._export()
        data = json.loads((Path(result.snapshot_dir) / SNAPSHOT_FILENAME).read_text("utf-8"))
        seen = set()
        for skill in data["skills"]:
            for alias in skill["aliases"]:
                self.assertNotIn(alias["normalized_alias"], seen)
                seen.add(alias["normalized_alias"])

    def test_alias_count_matches(self):
        result = self._export()
        data = json.loads((Path(result.snapshot_dir) / SNAPSHOT_FILENAME).read_text("utf-8"))
        manifest = json.loads((Path(result.snapshot_dir) / MANIFEST_FILENAME).read_text("utf-8"))
        self.assertEqual(sum(len(s["aliases"]) for s in data["skills"]), manifest["alias_count"])

    def test_canonical_count_matches_registry(self):
        result = self._export()
        data = json.loads((Path(result.snapshot_dir) / SNAPSHOT_FILENAME).read_text("utf-8"))
        self.assertEqual(
            sum(1 for s in data["skills"] if s["is_active"]),
            skill_uid_registry.registry_count(),
        )

    def test_deprecated_dotnet_core_metadata(self):
        result = self._export()
        data = json.loads((Path(result.snapshot_dir) / SNAPSHOT_FILENAME).read_text("utf-8"))
        deprecated = [s for s in data["skills"] if s["canonical_name"] == DEPRECATED_DOTNET_CORE_CANONICAL_NAME]
        self.assertEqual(len(deprecated), 1)
        entry = deprecated[0]
        self.assertFalse(entry["is_active"])
        self.assertEqual(entry["deprecation"]["status"], "deprecated")
        self.assertEqual(entry["deprecation"]["reason"], "canonical_rename")
        expected_replacement = str(skill_uid_registry.get_skill_uid(DOTNET_CANONICAL_NAME))
        self.assertEqual(entry["deprecation"]["replacement_skill_uid"], expected_replacement)

    def test_invalid_artifact_excluded(self):
        result = self._export()
        data = json.loads((Path(result.snapshot_dir) / SNAPSHOT_FILENAME).read_text("utf-8"))
        names = [s["canonical_name"] for s in data["skills"]]
        self.assertNotIn(INVALID_ARTIFACT_CANONICAL_NAME, names)
        manifest = json.loads((Path(result.snapshot_dir) / MANIFEST_FILENAME).read_text("utf-8"))
        self.assertEqual(manifest["excluded_invalid_artifacts"], list(EXCLUDED_INVALID_ARTIFACTS))

    def test_no_duplicate_uids_or_canonical_names_or_slugs(self):
        result = self._export()
        data = json.loads((Path(result.snapshot_dir) / SNAPSHOT_FILENAME).read_text("utf-8"))
        uids = [s["skill_uid"] for s in data["skills"]]
        names = [s["canonical_name"] for s in data["skills"]]
        slugs = [s["slug"] for s in data["skills"]]
        self.assertEqual(len(uids), len(set(uids)))
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(len(slugs), len(set(slugs)))

    def test_canonical_names_and_slugs_non_empty(self):
        result = self._export()
        data = json.loads((Path(result.snapshot_dir) / SNAPSHOT_FILENAME).read_text("utf-8"))
        for s in data["skills"]:
            self.assertIsInstance(s["canonical_name"], str)
            self.assertTrue(s["canonical_name"])
            self.assertIsInstance(s["slug"], str)
            self.assertTrue(s["slug"])
            self.assertIsInstance(s["category"], str)
            self.assertTrue(s["category"])
            self.assertIsInstance(s["source"], str)
            self.assertTrue(s["source"])
            self.assertTrue(s["esco_uri"] is None or isinstance(s["esco_uri"], str))

    def test_manifest_required_fields(self):
        result = self._export()
        manifest = json.loads((Path(result.snapshot_dir) / MANIFEST_FILENAME).read_text("utf-8"))
        for field in (
            "manifest_format", "manifest_version", "taxonomy_version",
            "taxonomy_content_sha256",
            "snapshot_filename", "snapshot_sha256",
            "source_product", "source_repository", "source_commit", "source_branch",
            "source_skills_migration",
            "registry_count", "snapshot_skill_count", "active_skill_count",
            "deprecated_skill_count", "alias_count",
            "excluded_invalid_artifacts", "exporter_contract_version",
        ):
            self.assertIn(field, manifest)
        self.assertEqual(manifest["source_product"], "TuniAtlas Jobs")
        self.assertEqual(manifest["source_repository"], "TaouaiB/tunitech-abroad")
        self.assertEqual(manifest["source_branch"], "dev")
        self.assertEqual(manifest["source_skills_migration"], REQUIRED_SOURCE_MIGRATION)
        self.assertEqual(manifest["exporter_contract_version"], EXPORTER_CONTRACT_VERSION)
        self.assertEqual(manifest["excluded_invalid_artifacts"], list(EXCLUDED_INVALID_ARTIFACTS))
        self.assertEqual(manifest["snapshot_filename"], SNAPSHOT_FILENAME)
        # Manifest distinguishes the two hash meanings.
        self.assertEqual(manifest["taxonomy_content_sha256"], result.taxonomy_content_sha256)
        self.assertEqual(manifest["snapshot_sha256"], result.snapshot_file_sha256)
        self.assertEqual(
            manifest["taxonomy_version"], "sha256:" + result.taxonomy_content_sha256
        )

    def test_manifest_has_no_timestamp(self):
        result = self._export()
        manifest = json.loads((Path(result.snapshot_dir) / MANIFEST_FILENAME).read_text("utf-8"))
        for forbidden in ("generated_at", "exported_at", "timestamp", "created_at"):
            self.assertNotIn(forbidden, manifest)

    def test_taxonomy_version_is_sha256_of_skills_bytes(self):
        result = self._export()
        data = json.loads((Path(result.snapshot_dir) / SNAPSHOT_FILENAME).read_text("utf-8"))
        canonical_skills_bytes = json.dumps(
            data["skills"],
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            separators=(",", ": "),
        ).encode("utf-8") + b"\n"
        self.assertEqual(
            "sha256:" + hashlib.sha256(canonical_skills_bytes).hexdigest(),
            data["taxonomy_version"],
        )

    def test_sha256sums_file_matches(self):
        result = self._export()
        sums_path = Path(result.snapshot_dir) / SHASUMS_FILENAME
        sums = self._parse_shasums(Path(result.snapshot_dir))
        for name in (SNAPSHOT_FILENAME, MANIFEST_FILENAME, README_FILENAME):
            expected = hashlib.sha256(
                (Path(result.snapshot_dir) / name).read_bytes()
            ).hexdigest()
            self.assertEqual(sums[name], expected, f"mismatch for {name}")
        self.assertNotIn(SHASUMS_FILENAME, sums)

    def test_readme_contents(self):
        result = self._export()
        text = (Path(result.snapshot_dir) / README_FILENAME).read_text("utf-8")
        for phrase in (
            "TuniAtlas Jobs",
            "tuniatlas-ml",
            "skill_uid",
            "ML-1",
            "encrypted backup",
        ):
            self.assertIn(phrase, text)

    # ------------------------------------------------------------------
    # Two-hash contract
    # ------------------------------------------------------------------

    def test_distinct_content_and_file_digests(self):
        result = self._export()
        # Content digest is over the skills array; file digest is over
        # the full payload. They MUST differ because the payload
        # embeds the version and counts.
        self.assertNotEqual(result.taxonomy_content_sha256, result.snapshot_file_sha256)
        snapshot_bytes = (Path(result.snapshot_dir) / SNAPSHOT_FILENAME).read_bytes()
        self.assertEqual(
            hashlib.sha256(snapshot_bytes).hexdigest(),
            result.snapshot_file_sha256,
        )
        # The manifest must record the file digest, not the content
        # digest, in ``snapshot_sha256``.
        manifest = json.loads((Path(result.snapshot_dir) / MANIFEST_FILENAME).read_text("utf-8"))
        self.assertEqual(manifest["snapshot_sha256"], result.snapshot_file_sha256)
        self.assertNotEqual(manifest["snapshot_sha256"], result.taxonomy_content_sha256)

    def test_manifest_snapshot_sha_matches_shasums(self):
        result = self._export()
        manifest = json.loads((Path(result.snapshot_dir) / MANIFEST_FILENAME).read_text("utf-8"))
        sums = self._parse_shasums(Path(result.snapshot_dir))
        self.assertEqual(manifest["snapshot_sha256"], sums[SNAPSHOT_FILENAME])
        self.assertEqual(
            hashlib.sha256((Path(result.snapshot_dir) / SNAPSHOT_FILENAME).read_bytes()).hexdigest(),
            sums[SNAPSHOT_FILENAME],
        )

    # ------------------------------------------------------------------
    # Determinism
    # ------------------------------------------------------------------

    def test_deterministic_across_repeated_exports(self):
        a = self.service.export(self.tmp)
        b = self.service.export(self.tmp)
        self.assertEqual(a.taxonomy_version, b.taxonomy_version)
        self.assertEqual(a.snapshot_dir, b.snapshot_dir)
        for name in (SNAPSHOT_FILENAME, MANIFEST_FILENAME, README_FILENAME, SHASUMS_FILENAME):
            self.assertEqual(
                (Path(a.snapshot_dir) / name).read_bytes(),
                (Path(b.snapshot_dir) / name).read_bytes(),
            )

    def test_idempotent_on_identical_existing_snapshot(self):
        first = self.service.export(self.tmp)
        second = self.service.export(self.tmp)
        self.assertFalse(first.idempotent)
        self.assertTrue(second.idempotent)
        self.assertEqual(first.taxonomy_version, second.taxonomy_version)

    def test_refuses_to_overwrite_differing_snapshot(self):
        self.service.export(self.tmp)
        version_dir = next(self.tmp.iterdir())
        target = version_dir / SNAPSHOT_FILENAME
        target.write_bytes(b"{}")
        with self.assertRaises(TaxonomySnapshotPublishError):
            self.service.export(self.tmp)

    def test_zero_mutation_after_export(self):
        before = {
            "skills": Skill.objects.count(),
            "aliases": SkillAlias.objects.count(),
        }
        self.service.export(self.tmp)
        self.service.export(self.tmp)
        after = {
            "skills": Skill.objects.count(),
            "aliases": SkillAlias.objects.count(),
        }
        self.assertEqual(before, after)

    def test_empty_slug_falls_back_to_canonical_name(self):
        """The legacy ``.NET`` row carries an empty slug; the snapshot must derive a non-empty value."""
        # Pick a skill and force its slug to empty.
        skill = Skill.objects.exclude(
            canonical_name=DOTNET_CANONICAL_NAME
        ).filter(is_active=True).first()
        Skill.objects.filter(pk=skill.pk).update(slug="")
        try:
            result = self._export()
            data = json.loads(
                (Path(result.snapshot_dir) / SNAPSHOT_FILENAME).read_text("utf-8")
            )
            entry = next(
                s for s in data["skills"] if s["skill_uid"] == str(skill.skill_uid)
            )
            self.assertTrue(entry["slug"], "snapshot slug must be non-empty")
            # Fallback is derived from canonical_name.
            self.assertIn(
                skill.canonical_name.lower().replace(" ", "-")[:3],
                entry["slug"],
            )
        finally:
            # Restore the original slug.
            Skill.objects.filter(pk=skill.pk).update(
                slug=skill.__class__.objects.get(pk=skill.pk).canonical_name.lower().replace(" ", "-").replace("/", "-")
            )

    # ------------------------------------------------------------------
    # Atomic publish invariants
    # ------------------------------------------------------------------

    def test_staging_directory_uses_output_root(self):
        # The exporter must create the staging directory under the
        # output root (same filesystem). We verify both that the
        # final target lives in the output root and that no leftover
        # staging directory remains after a successful export.
        self._export()
        for child in self.tmp.iterdir():
            self.assertFalse(
                child.name.startswith(".taxonomy-snapshot-staging-"),
                f"staging directory left behind: {child}",
            )
        # Direct check: the staging directory prefix is only ever
        # combined with the output root.
        from apps.skills.services import taxonomy_snapshot as ts
        import inspect
        source = inspect.getsource(ts)
        self.assertIn("tempfile.mkdtemp(prefix=STAGING_DIR_PREFIX, dir=str(output_root))", source)

    def test_failure_during_staging_write_leaves_no_target(self):
        # Patch the service to raise inside the staging writer.
        original = self.service._write_staging
        def _explode(*args, **kwargs):
            original(*args, **kwargs)
            raise RuntimeError("simulated staging write failure")
        self.service._write_staging = _explode  # type: ignore[assignment]
        try:
            with self.assertRaises(RuntimeError):
                self._export()
        finally:
            self.service._write_staging = original  # type: ignore[assignment]
        # No version directory and no leftover staging directory.
        for child in self.tmp.iterdir():
            self.assertFalse(
                child.name.startswith(".taxonomy-snapshot-staging-"),
                f"staging directory left behind after failure: {child}",
            )

    def test_failure_at_atomic_rename_leaves_no_partial_target(self):
        # Patch os.replace to raise.
        original_replace = os.replace
        def _boom(src, dst):
            raise OSError("simulated rename failure")
        os.replace = _boom  # type: ignore[assignment]
        try:
            with self.assertRaises(TaxonomySnapshotPublishError):
                self._export()
        finally:
            os.replace = original_replace  # type: ignore[assignment]
        # No version directory and no leftover staging.
        for child in self.tmp.iterdir():
            self.assertFalse(
                child.name.startswith(".taxonomy-snapshot-staging-"),
                f"staging directory left behind after rename failure: {child}",
            )

    def test_publish_race_identical_target_resolves_idempotently(self):
        race_state = {}

        def _publish_identical_then_fail(src, dst):
            source = Path(src)
            target = Path(dst)
            shutil.copytree(source, target)
            race_state["target"] = target
            race_state["bytes"] = self._read_snapshot_files(target)
            raise OSError("simulated rename race after identical publish")

        with mock.patch(
            "apps.skills.services.taxonomy_snapshot.os.replace",
            side_effect=_publish_identical_then_fail,
        ):
            result = self._export()

        target = race_state["target"]
        self.assertTrue(result.idempotent)
        self.assertEqual(Path(result.snapshot_dir), target)
        self.assertEqual(self._read_snapshot_files(target), race_state["bytes"])
        self._assert_no_staging_directory()

    def test_publish_race_differing_complete_target_fails_closed(self):
        race_state = {}

        def _publish_differing_then_fail(src, dst):
            target = Path(dst)
            shutil.copytree(Path(src), target)
            taxonomy_path = target / SNAPSHOT_FILENAME
            taxonomy_path.write_bytes(taxonomy_path.read_bytes() + b" ")
            race_state["target"] = target
            race_state["bytes"] = self._read_snapshot_files(target)
            raise OSError("simulated rename race after differing publish")

        with mock.patch(
            "apps.skills.services.taxonomy_snapshot.os.replace",
            side_effect=_publish_differing_then_fail,
        ):
            with self.assertRaises(TaxonomySnapshotPublishError):
                self._export()

        target = race_state["target"]
        self.assertEqual(self._read_snapshot_files(target), race_state["bytes"])
        self._assert_no_staging_directory()

    def test_publish_race_incomplete_target_fails_closed(self):
        race_state = {}

        def _publish_incomplete_then_fail(src, dst):
            source = Path(src)
            target = Path(dst)
            target.mkdir()
            shutil.copy2(source / SNAPSHOT_FILENAME, target / SNAPSHOT_FILENAME)
            race_state["target"] = target
            race_state["taxonomy_bytes"] = (
                target / SNAPSHOT_FILENAME
            ).read_bytes()
            raise OSError("simulated rename race after incomplete publish")

        with mock.patch(
            "apps.skills.services.taxonomy_snapshot.os.replace",
            side_effect=_publish_incomplete_then_fail,
        ):
            with self.assertRaises(TaxonomySnapshotPublishError):
                self._export()

        target = race_state["target"]
        self.assertEqual(
            sorted(path.name for path in target.iterdir()),
            [SNAPSHOT_FILENAME],
        )
        self.assertEqual(
            (target / SNAPSHOT_FILENAME).read_bytes(),
            race_state["taxonomy_bytes"],
        )
        self._assert_no_staging_directory()

    def test_concurrent_differing_target_fails(self):
        first = self._export()
        version_dir = Path(first.snapshot_dir)
        # Mutate one byte of taxonomy.json inside the published
        # directory to force a "differing" identity.
        taxonomy_path = version_dir / SNAPSHOT_FILENAME
        original_bytes = taxonomy_path.read_bytes()
        # Replace the last two bytes with whitespace to keep the file
        # parseable; the SHA will differ but the directory still looks
        # complete.
        mutated = original_bytes.rstrip(b"\n") + b"  \n"
        taxonomy_path.write_bytes(mutated)
        # Also patch the SHA256SUMS so it matches the mutated file,
        # otherwise the contract refuses for a different reason.
        sums_text = (version_dir / SHASUMS_FILENAME).read_text("utf-8")
        new_digest = hashlib.sha256(mutated).hexdigest()
        sums_lines = []
        for line in sums_text.splitlines():
            if not line.strip():
                sums_lines.append(line)
                continue
            digest, name = line.split("  ", 1)
            if name == SNAPSHOT_FILENAME:
                sums_lines.append(f"{new_digest}  {name}")
            else:
                sums_lines.append(line)
        (version_dir / SHASUMS_FILENAME).write_text("\n".join(sums_lines) + "\n")
        with self.assertRaises(TaxonomySnapshotPublishError):
            self._export()

    def test_incomplete_existing_target_fails(self):
        first = self._export()
        version_dir = Path(first.snapshot_dir)
        # Capture the SHA256SUMS bytes before removing the file.
        sums_bytes = (version_dir / SHASUMS_FILENAME).read_bytes()
        (version_dir / SHASUMS_FILENAME).unlink()
        with self.assertRaises(TaxonomySnapshotPublishError):
            self._export()
        # Restore the target to a complete state and add a stray file.
        (version_dir / SHASUMS_FILENAME).write_bytes(sums_bytes)
        (version_dir / "extra.txt").write_text("stray")
        with self.assertRaises(TaxonomySnapshotPublishError):
            self._export()

    def test_existing_target_with_subdirectory_fails(self):
        first = self._export()
        version_dir = Path(first.snapshot_dir)
        (version_dir / "subdir").mkdir()
        with self.assertRaises(TaxonomySnapshotPublishError):
            self._export()

    # ------------------------------------------------------------------
    # Source contract guards
    # ------------------------------------------------------------------

    def test_uuid_mismatch_refused(self):
        skill = Skill.objects.filter(is_active=True).first()
        original = skill.skill_uid
        new_uid = uuid.uuid4()
        Skill.objects.filter(pk=skill.pk).update(skill_uid=new_uid)
        try:
            with self.assertRaises(TaxonomySnapshotContractError):
                self.service.export(self.tmp)
        finally:
            Skill.objects.filter(pk=skill.pk).update(skill_uid=original)

    def test_active_deprecated_row_refused(self):
        Skill.objects.filter(pk=self._deprecated_dotnet_core.pk).update(is_active=True)
        try:
            with self.assertRaises(TaxonomySnapshotContractError):
                self.service.export(self.tmp)
        finally:
            Skill.objects.filter(pk=self._deprecated_dotnet_core.pk).update(is_active=False)

    def test_unknown_non_registry_row_refused(self):
        rogue = Skill.objects.create(
            canonical_name="Rogue Non-Registry Skill",
            slug="rogue-non-registry-skill",
            category="other",
            is_active=True,
            source="manual",
            skill_uid=uuid.uuid4(),
        )
        try:
            with self.assertRaises(TaxonomySnapshotContractError):
                self.service.export(self.tmp)
        finally:
            Skill.objects.filter(pk=rogue.pk).delete()

    def test_deprecated_replacement_uuid_must_exist(self):
        """The deprecated `.NET Core` UUID must not collide with the canonical `.NET` registry UUID.

        We simulate the collision by temporarily moving the canonical
        ``.NET`` UUID to a fresh value, then setting the deprecated
        ``.NET Core`` UUID to the original ``.NET`` registry UUID. The
        exporter must refuse this state.
        """
        original_dotnet_pk = Skill.objects.get(canonical_name=DOTNET_CANONICAL_NAME).pk
        original_dotnet_uid = skill_uid_registry.get_skill_uid(DOTNET_CANONICAL_NAME)
        original_deprecated_uid = self._deprecated_dotnet_core.skill_uid

        # Choose a fresh UUIDv4 that is not in the registry.
        new_dotnet_uid = _deterministic_uuidv4_excluding(
            seed_salt=b"dotnet-temp",
            exclude={
                uuid.UUID(u) for _, u in skill_uid_registry.registry_entries()
            } | {original_deprecated_uid, original_dotnet_uid},
        )

        Skill.objects.filter(pk=original_dotnet_pk).update(skill_uid=new_dotnet_uid)
        Skill.objects.filter(
            pk=self._deprecated_dotnet_core.pk
        ).update(skill_uid=original_dotnet_uid)
        try:
            with self.assertRaises(TaxonomySnapshotContractError):
                self.service.export(self.tmp)
        finally:
            Skill.objects.filter(
                pk=self._deprecated_dotnet_core.pk
            ).update(skill_uid=original_deprecated_uid)
            Skill.objects.filter(pk=original_dotnet_pk).update(
                skill_uid=original_dotnet_uid
            )
            self._deprecated_dotnet_core = Skill.objects.get(
                pk=self._deprecated_dotnet_core.pk
            )

    def test_deprecated_replacement_must_be_active(self):
        dotnet = Skill.objects.get(canonical_name=DOTNET_CANONICAL_NAME)
        Skill.objects.filter(pk=dotnet.pk).update(is_active=False)
        try:
            with self.assertRaises(TaxonomySnapshotContractError):
                self.service.export(self.tmp)
        finally:
            Skill.objects.filter(pk=dotnet.pk).update(is_active=True)

    def test_missing_registry_canonical_refused(self):
        target = Skill.objects.filter(canonical_name=DOTNET_CANONICAL_NAME).first()
        target_pk = target.pk
        target_name = target.canonical_name
        target_uid = target.skill_uid
        original_slug = target.slug
        # Delete aliases first; the SkillAlias FK is ``on_delete=PROTECT``.
        SkillAlias.objects.filter(skill=target).delete()
        Skill.objects.filter(pk=target_pk).delete()
        try:
            with self.assertRaises(TaxonomySnapshotContractError) as ctx:
                self.service.export(self.tmp)
            self.assertIn("Registry canonical row missing", str(ctx.exception))
        finally:
            Skill.objects.create(
                canonical_name=target_name,
                slug=original_slug,
                category="other",
                is_active=True,
                source="seed",
                skill_uid=target_uid,
            )

    def test_invalid_artifact_active_refused(self):
        Skill.objects.filter(pk=self._invalid_artifact.pk).update(is_active=True)
        try:
            with self.assertRaises(TaxonomySnapshotContractError) as ctx:
                self.service.export(self.tmp)
            self.assertIn("active", str(ctx.exception))
        finally:
            Skill.objects.filter(pk=self._invalid_artifact.pk).update(is_active=False)

    def test_invalid_artifact_wrong_tombstone_refused(self):
        original = self._invalid_artifact.skill_uid
        Skill.objects.filter(pk=self._invalid_artifact.pk).update(
            skill_uid=uuid.uuid4(),
        )
        try:
            with self.assertRaises(TaxonomySnapshotContractError) as ctx:
                self.service.export(self.tmp)
            self.assertIn("tombstone", str(ctx.exception))
        finally:
            Skill.objects.filter(pk=self._invalid_artifact.pk).update(
                skill_uid=original,
            )

    def test_invalid_artifact_duplicate_refused(self):
        # The ``Skill.canonical_name`` model field carries a database
        # unique constraint, so a real duplicate cannot be created
        # through the ORM. The contract branch is therefore enforced
        # by the database layer itself; the exporter's own check
        # provides a second, defence-in-depth guard. We verify the
        # database layer here by attempting to create a second row
        # and asserting the constraint fires.
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Skill.objects.create(
                canonical_name=INVALID_ARTIFACT_CANONICAL_NAME,
                slug="invalid-artifact-2",
                category="other",
                is_active=False,
                source="manual",
                skill_uid=uuid.uuid4(),
            )

    def test_fallback_slug_collision_refused(self):
        # The database enforces a unique constraint on ``Skill.slug``,
        # so a real duplicate cannot exist in the source data. The
        # exporter's defence-in-depth check on derived slugs is
        # exercised by temporarily dropping the unique constraint via
        # raw SQL, setting two skills to empty slugs, patching the
        # fallback to return a colliding value, running the export,
        # and restoring the original state.
        from django.db import connection
        from apps.skills.services import taxonomy_snapshot as ts

        skills = list(
            Skill.objects.filter(is_active=True).order_by("canonical_name")[:2]
        )
        first, second = skills
        original_first_slug = first.slug
        original_second_slug = second.slug
        original_fallback = ts._derive_slug_fallback

        def _collide(canonical_name: str) -> str:
            return "collision-slug"

        with connection.cursor() as cursor:
            cursor.execute(
                "ALTER TABLE skills_skill DROP CONSTRAINT skills_skill_slug_key"
            )
        ts._derive_slug_fallback = _collide  # type: ignore[assignment]
        try:
            Skill.objects.filter(pk=first.pk).update(slug="")
            Skill.objects.filter(pk=second.pk).update(slug="")
            with self.assertRaises(TaxonomySnapshotContractError) as ctx:
                self.service.export(self.tmp)
            self.assertIn("Duplicate", str(ctx.exception))
        finally:
            ts._derive_slug_fallback = original_fallback  # type: ignore[assignment]
            Skill.objects.filter(pk=first.pk).update(slug=original_first_slug)
            Skill.objects.filter(pk=second.pk).update(slug=original_second_slug)
            with connection.cursor() as cursor:
                cursor.execute(
                    "ALTER TABLE skills_skill "
                    "ADD CONSTRAINT skills_skill_slug_key UNIQUE (slug)"
                )

    def test_source_commit_shape_enforced(self):
        with self.assertRaises(TaxonomySnapshotContractError) as ctx:
            self.service.export(self.tmp, git_commit="not-a-sha")
        self.assertIn("40-character lowercase hex SHA-1", str(ctx.exception))

    def test_no_mutation_under_failure(self):
        # Force a contract failure and check the database is untouched.
        target = Skill.objects.filter(canonical_name=DOTNET_CANONICAL_NAME).first()
        Skill.objects.filter(pk=target.pk).update(is_active=False)
        try:
            with self.assertRaises(TaxonomySnapshotContractError):
                self.service.export(self.tmp)
        finally:
            Skill.objects.filter(pk=target.pk).update(is_active=True)
        # tearDown also asserts; the explicit count here gives a
        # sharper failure message.
        self.assertEqual(Skill.objects.count(), self._skill_count_before)
        self.assertEqual(SkillAlias.objects.count(), self._alias_count_before)

    # ------------------------------------------------------------------
    # Management command
    # ------------------------------------------------------------------

    def _run_command(self, **overrides):
        out = io.StringIO()
        err = io.StringIO()
        kwargs = dict(
            stdout=out,
            stderr=err,
        )
        kwargs.update(overrides)
        try:
            call_command(
                "export_skill_taxonomy_snapshot",
                "--output-root", str(self.tmp),
                "--allow-branch", "dev",
                "--allow-dirty",
                "--git-commit", "0" * 40,
                **kwargs,
            )
            return out.getvalue(), None
        except CommandError as exc:
            return None, str(exc)

    def test_command_succeeds_and_prints_metadata(self):
        out, err = self._run_command()
        self.assertIsNone(err, f"stderr={err}")
        payload = json.loads(out)
        self.assertEqual(payload["source_commit"], "0" * 40)
        self.assertEqual(payload["registry_count"], skill_uid_registry.registry_count())
        self.assertEqual(payload["skill_count"], 523)
        for field in (
            "taxonomy_version",
            "taxonomy_content_sha256",
            "snapshot_file_sha256",
            "manifest_sha256",
            "readme_sha256",
            "skill_count",
            "active_skill_count",
            "deprecated_skill_count",
            "alias_count",
            "registry_count",
            "excluded_invalid_artifacts",
            "idempotent",
            "source_commit",
            "source_branch",
        ):
            self.assertIn(field, payload)
        self.assertNotEqual(
            payload["taxonomy_content_sha256"],
            payload["snapshot_file_sha256"],
        )

    def test_command_refuses_different_branch(self):
        out = io.StringIO()
        err = io.StringIO()
        with self.assertRaises(CommandError):
            call_command(
                "export_skill_taxonomy_snapshot",
                "--output-root", str(self.tmp),
                "--allow-branch", "main",
                "--git-commit", "0" * 40,
                stdout=out,
                stderr=err,
            )

    def test_command_refuses_missing_output_root(self):
        missing = self.tmp / "does-not-exist"
        out = io.StringIO()
        err = io.StringIO()
        with self.assertRaises(CommandError):
            call_command(
                "export_skill_taxonomy_snapshot",
                "--output-root", str(missing),
                "--allow-branch", "dev",
                "--git-commit", "0" * 40,
                stdout=out,
                stderr=err,
            )


class TaxonomySnapshotEnvironmentGuardTests(SimpleTestCase):
    """Environment boundary tests for the exporter command."""

    def test_assert_source_environment_fails_on_dirty(self):
        with self.assertRaises(TaxonomySnapshotEnvironmentError):
            assert_source_environment(require_branch="dev")

    def test_assert_source_environment_branch_check(self):
        with self.assertRaises(TaxonomySnapshotEnvironmentError):
            assert_source_environment(require_branch="nonexistent")
