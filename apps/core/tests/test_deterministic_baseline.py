from __future__ import annotations

import json
import math
import shutil
import tempfile
import urllib.request
import uuid
from datetime import datetime, timezone as datetime_timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from django.db import connection
from django.test import SimpleTestCase, TransactionTestCase, override_settings

from apps.core.baselines.deterministic import (
    BASELINE_VERSION,
    EXPECTED_FILES,
    BaselineError,
    build_bundle,
    canonical_json_bytes,
    compare_bundles,
    external_calls_forbidden,
    _rename_noreplace,
    publish_bundle,
    reset_synthetic_state,
)
from apps.core.baselines.taxonomy_snapshot import (
    EXPECTED_ACTIVE_COUNT,
    EXPECTED_ALIAS_COUNT,
    EXPECTED_INACTIVE_COUNT,
    EXPECTED_REGISTRY_COUNT,
    EXPECTED_SNAPSHOT_SKILL_COUNT,
    SnapshotTaxonomyError,
    populate_test_database,
    prove_database_equality,
    read_approved_snapshot,
)
from apps.cvs.services.deterministic_extractor import CVDeterministicExtractorService
from apps.jobs.services.skill_extraction import JobSkillExtractionService
from apps.matching.services.scoring import MatchScoringService
from apps.recommendations.services.recommendation import RecommendationService
from apps.skills.services.normalizer import SkillNormalizerService
from scripts.export_deterministic_baseline import APPROVED_ROOT, validate_output_path


COMMIT = "1b7252a6cb9c229140385c4147384c5fbd7dccdb"
SNAPSHOT_DIR = (
    Path(__file__).resolve().parents[3].parent
    / "tuniatlas-ml/data/private/taxonomy/snapshots"
    / "sha256-d6d5aebf5e4b958f163d2f33b8d441a36e6d638ac8c92379f18e6ebd40e2fc05"
)


def load_json(root: Path, name: str):
    return json.loads((root / name).read_text(encoding="utf-8"))


class CanonicalSerializationTests(SimpleTestCase):
    def test_decimal_datetime_uuid_and_key_order_are_canonical(self):
        value = {
            "uuid": uuid.UUID("10000000-0000-4000-8000-000000000001"),
            "decimal": Decimal("10.5000"),
            "datetime": datetime(2020, 1, 1, tzinfo=datetime_timezone.utc),
            "items": {"b", "a"},
        }

        rendered = canonical_json_bytes(value)

        self.assertEqual(
            rendered,
            b'{"datetime":"2020-01-01T00:00:00+00:00","decimal":"10.5","items":["a","b"],"uuid":"10000000-0000-4000-8000-000000000001"}\n',
        )

    def test_non_finite_values_are_rejected(self):
        for value in (Decimal("NaN"), Decimal("Infinity"), math.nan, math.inf):
            with self.subTest(value=value):
                with self.assertRaises(BaselineError):
                    canonical_json_bytes({"value": value})

    def test_output_path_restrictions(self):
        approved = APPROVED_ROOT / BASELINE_VERSION
        self.assertEqual(validate_output_path(approved, allow_temporary=False), approved.resolve())
        with tempfile.TemporaryDirectory() as temporary:
            allowed = Path(temporary) / "tuniatlas-export"
            self.assertEqual(validate_output_path(allowed, allow_temporary=True), allowed.resolve())
        with self.assertRaises(ValueError):
            validate_output_path(Path("/var/tmp/unapproved-baseline"), allow_temporary=False)

    def test_external_call_guard_fails_closed(self):
        with external_calls_forbidden():
            with self.assertRaisesRegex(AssertionError, "forbids LLM and external calls"):
                urllib.request.urlopen("https://fixture.invalid")


@override_settings(
    LLM_ENABLED=False,
    JOB_ENRICHMENT_ENABLED=False,
    CV_LLM_EXTRACTION_ENABLED=False,
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
)
class DeterministicBundleBuildTests(TransactionTestCase):
    reset_sequences = False

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.temporary = tempfile.TemporaryDirectory()
        cls.bundle = Path(cls.temporary.name) / "bundle"
        cls.service_patches = (
            patch.object(JobSkillExtractionService, "extract_for_job", wraps=JobSkillExtractionService.extract_for_job),
            patch.object(CVDeterministicExtractorService, "extract", wraps=CVDeterministicExtractorService.extract),
            patch.object(SkillNormalizerService, "normalize_many", wraps=SkillNormalizerService.normalize_many),
            patch.object(MatchScoringService, "calculate", wraps=MatchScoringService.calculate),
            patch.object(RecommendationService, "refresh_for_user", wraps=RecommendationService.refresh_for_user),
        )
        cls.mocks = []
        for service_patch in cls.service_patches:
            cls.mocks.append(service_patch.start())
        try:
            cls.manifest = build_bundle(
                cls.bundle,
                django_commit=COMMIT,
                taxonomy_snapshot_dir=SNAPSHOT_DIR,
            )
        finally:
            for service_patch in reversed(cls.service_patches):
                service_patch.stop()

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()
        super().tearDownClass()

    def test_isolated_test_database_and_production_service_entry_points(self):
        self.assertTrue(str(connection.settings_dict["NAME"]).startswith("test_"))
        for mocked_service in self.mocks:
            self.assertGreater(mocked_service.call_count, 0)

    def test_exact_file_set_hashes_and_no_wall_clock_fields(self):
        self.assertEqual(sorted(path.name for path in self.bundle.iterdir()), sorted(EXPECTED_FILES))
        sums = (self.bundle / "SHA256SUMS").read_text(encoding="ascii").splitlines()
        self.assertEqual(len(sums), len(EXPECTED_FILES) - 1)
        for name, digest in self.manifest["file_sha256"].items():
            self.assertEqual(len(digest), 64, name)
        joined = b"".join(path.read_bytes() for path in sorted(self.bundle.iterdir()))
        for forbidden in (b'"created_at"', b'"updated_at"', b'"exported_at"', b'"run_id"'):
            self.assertNotIn(forbidden, joined)

    def test_fixture_minimums_classifications_and_metrics_reconcile(self):
        cases = load_json(self.bundle, "cases.json")["cases"]
        metrics = load_json(self.bundle, "metrics.json")
        counts = metrics["case_counts_by_domain"]
        self.assertGreaterEqual(counts["job_extraction"], 30)
        self.assertGreaterEqual(counts["canonicalization"], 30)
        self.assertGreaterEqual(counts["cv_extraction"], 6)
        self.assertGreaterEqual(counts["matching_recommendation"], 8)
        self.assertEqual(sum(counts.values()), len(cases))
        self.assertEqual(metrics["deterministic_reproduction"]["pass_count"], len(cases))
        self.assertGreater(metrics["case_counts_by_classification"]["POLICY_PENDING"], 0)
        self.assertFalse(metrics["runtime_benchmarks_included"])

    def test_exact_approved_snapshot_populates_and_equals_test_database(self):
        snapshot = populate_test_database(SNAPSHOT_DIR)
        prove_database_equality(snapshot)
        self.assertEqual(self.manifest["taxonomy_registry_count"], EXPECTED_REGISTRY_COUNT)
        self.assertEqual(self.manifest["taxonomy_active_count"], EXPECTED_ACTIVE_COUNT)
        self.assertEqual(self.manifest["taxonomy_inactive_count"], EXPECTED_INACTIVE_COUNT)
        self.assertEqual(self.manifest["taxonomy_alias_count"], EXPECTED_ALIAS_COUNT)
        self.assertEqual(len(snapshot.skills), EXPECTED_SNAPSHOT_SKILL_COUNT)
        self.assertEqual(self.manifest["taxonomy_registry_digest"], snapshot.registry_digest)

    def test_fixed_public_and_skill_uuids_and_no_internal_ids(self):
        cases = load_json(self.bundle, "cases.json")["cases"]
        all_json = [load_json(self.bundle, name) for name in EXPECTED_FILES if name.endswith(".json")]
        forbidden_keys = {"id", "pk", "user_id", "job_id", "profile_id", "skill_id", "source_object_id", "run_id"}

        def walk(value):
            if isinstance(value, dict):
                self.assertFalse(forbidden_keys.intersection(value))
                for key, item in value.items():
                    if key.endswith("public_id") or key == "skill_uid":
                        parsed = uuid.UUID(item)
                        self.assertEqual(parsed.version, 4)
                    walk(item)
            elif isinstance(value, list):
                for item in value:
                    walk(item)

        for value in all_json:
            walk(value)
        self.assertEqual(len({case["case_id"] for case in cases}), len(cases))

    def test_synthetic_only_no_cv_filename_or_translated_text_coupling(self):
        cases_text = (self.bundle / "cases.json").read_text(encoding="utf-8")
        matching_text = (self.bundle / "matching_recommendation.json").read_text(encoding="utf-8")
        self.assertIn("@fixture.invalid", cases_text)
        self.assertNotIn("private_media", cases_text)
        self.assertNotIn(".pdf", cases_text)
        self.assertNotIn('"recommended_actions"', matching_text)
        self.assertNotIn('"reason_summary"', matching_text)
        self.assertFalse(any(path.suffix == ".pdf" for path in self.bundle.iterdir()))

    def test_known_hard_negative_observations_are_not_silently_passing(self):
        ledger = load_json(self.bundle, "known_failures.json")
        metrics = load_json(self.bundle, "metrics.json")
        failures = ledger["failed_assertions"]
        pending = ledger["policy_pending"]
        failed_metric_count = (
            metrics["obvious_gold_skill_assertions"]["false_positives"]
            + metrics["obvious_gold_skill_assertions"]["false_negatives"]
        )
        self.assertEqual(len(failures), failed_metric_count)
        self.assertEqual(len({entry["failure_id"] for entry in failures}), len(failures))
        self.assertEqual(len(pending), metrics["policy_pending_count"])
        self.assertTrue({"job_017", "job_021", "job_023", "job_033"}.issubset({entry["case_id"] for entry in failures}))
        for entry in pending:
            self.assertNotIn("desired", entry)
            self.assertNotIn("expected", entry)

    def test_chef_and_sql_family_current_observations(self):
        outputs = {item["case_id"]: item for item in load_json(self.bundle, "job_extraction.json")["outputs"]}

        def names(case_id):
            return {item["canonical_name"] for item in outputs[case_id]["canonical_skills"]}

        self.assertIn("Chef", names("job_018"))
        self.assertNotIn("Chef", names("job_019"))
        self.assertNotIn("Chef", names("job_020"))
        self.assertEqual(names("job_010").intersection({"SQL", "SQL Server"}), {"SQL Server"})
        self.assertEqual(names("job_011").intersection({"SQL", "SQLite"}), {"SQLite"})
        self.assertEqual(names("job_012").intersection({"SQL", "MySQL"}), {"MySQL"})

    def test_matching_scores_components_and_recommendation_order_are_present(self):
        outputs = {item["case_id"]: item for item in load_json(self.bundle, "matching_recommendation.json")["outputs"]}
        self.assertEqual(outputs["match_001"]["score"]["match_confidence"], "reliable")
        self.assertTrue(outputs["match_002"]["score"]["missing_required_skills"])
        order = outputs["match_010"]["recommendation_order"]
        self.assertGreaterEqual(len(order), 3)
        self.assertEqual([item["rank"] for item in order], list(range(1, len(order) + 1)))


@override_settings(
    LLM_ENABLED=False,
    JOB_ENRICHMENT_ENABLED=False,
    CV_LLM_EXTRACTION_ENABLED=False,
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
)
class DeterministicReproductionTests(TransactionTestCase):
    def test_two_builds_are_byte_identical(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = root / "first"
            second = root / "second"
            build_bundle(first, django_commit=COMMIT, taxonomy_snapshot_dir=SNAPSHOT_DIR)
            reset_synthetic_state()
            build_bundle(second, django_commit=COMMIT, taxonomy_snapshot_dir=SNAPSHOT_DIR)
            self.assertTrue(compare_bundles(first, second))


class SnapshotContractTests(SimpleTestCase):
    def test_modified_private_snapshot_is_rejected_before_database_use(self):
        with tempfile.TemporaryDirectory() as temporary:
            copy = Path(temporary) / "snapshot"
            shutil.copytree(SNAPSHOT_DIR, copy)
            with (copy / "taxonomy.json").open("ab") as handle:
                handle.write(b"changed")
            with self.assertRaisesRegex(SnapshotTaxonomyError, "checksum"):
                read_approved_snapshot(copy)


class AtomicPublicationTests(SimpleTestCase):
    @staticmethod
    def _builder(marker: bytes = b"same"):
        def build(path: Path):
            path.mkdir(parents=True)
            for name in EXPECTED_FILES:
                (path / name).write_bytes(marker + name.encode("ascii"))
            return {"bundle_content_sha256": "0" * 64}

        return build

    def test_publish_then_identical_target_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "target"
            _, first = publish_bundle(target, self._builder())
            _, second = publish_bundle(target, self._builder())
            self.assertEqual(first, "published")
            self.assertEqual(second, "idempotent")

    def test_different_or_incomplete_target_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "target"
            publish_bundle(target, self._builder())
            before = {path.name: path.read_bytes() for path in target.iterdir()}
            with self.assertRaises(BaselineError):
                publish_bundle(target, self._builder(b"different"))
            self.assertEqual(before, {path.name: path.read_bytes() for path in target.iterdir()})
            (target / "manifest.json").unlink()
            with self.assertRaises(BaselineError):
                publish_bundle(target, self._builder())

    def test_concurrent_empty_target_is_not_replaced(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "target"

            def race(source, destination):
                destination.mkdir()
                _rename_noreplace(source, destination)

            with self.assertRaisesRegex(BaselineError, "concurrent"):
                publish_bundle(target, self._builder(), rename_noreplace=race)
            self.assertTrue(target.is_dir())
            self.assertEqual(list(target.iterdir()), [])
            self.assertEqual([path.name for path in Path(temporary).iterdir()], ["target"])

    def test_concurrent_nonempty_target_is_not_replaced(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "target"

            def race(source, destination):
                destination.mkdir()
                (destination / "owner-marker").write_text("other", encoding="utf-8")
                _rename_noreplace(source, destination)

            with self.assertRaisesRegex(BaselineError, "concurrent"):
                publish_bundle(target, self._builder(), rename_noreplace=race)
            self.assertEqual((target / "owner-marker").read_text(encoding="utf-8"), "other")
            self.assertEqual([path.name for path in Path(temporary).iterdir()], ["target"])

    def test_unsupported_no_replace_primitive_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "target"

            def unavailable(source, destination):
                raise BaselineError("atomic no-replace publication is unavailable")

            with self.assertRaisesRegex(BaselineError, "unavailable"):
                publish_bundle(target, self._builder(), rename_noreplace=unavailable)
            self.assertFalse(target.exists())
            self.assertEqual(list(Path(temporary).iterdir()), [])

    def test_failed_build_cleans_staging(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "target"

            def fail(path: Path):
                path.mkdir(parents=True)
                (path / "partial").write_text("partial", encoding="utf-8")
                raise RuntimeError("synthetic failure")

            with self.assertRaisesRegex(RuntimeError, "synthetic failure"):
                publish_bundle(target, fail)
            self.assertFalse(target.exists())
            self.assertEqual(list(Path(temporary).iterdir()), [])
