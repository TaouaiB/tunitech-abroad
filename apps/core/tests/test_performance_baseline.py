from __future__ import annotations

import json
import math
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.test import SimpleTestCase, TransactionTestCase, override_settings

from apps.core.baselines.performance import (
    CONTROLLED_ENVIRONMENT,
    PerformanceBenchmarkError,
    normalize_ru_maxrss,
    percentile_r7,
    run_with_runner,
    summarize_samples,
    validate_controlled_environment,
)
from scripts.run_ml0_deterministic_benchmark import apply_affinity, validate_output_path, write_exclusive


ML_ROOT = Path(__file__).resolve().parents[3].parent / "tuniatlas-ml"
DETERMINISTIC_ROOT = ML_ROOT / "data/private/baselines/ml0/deterministic-v2"
TAXONOMY_ROOT = (
    ML_ROOT
    / "data/private/taxonomy/snapshots"
    / "sha256-d6d5aebf5e4b958f163d2f33b8d441a36e6d638ac8c92379f18e6ebd40e2fc05"
)


class PerformanceStatisticsTests(SimpleTestCase):
    def test_type7_percentiles_and_statistics(self):
        samples = [10, 20, 30, 40]
        self.assertEqual(percentile_r7(samples, 0.5), 25)
        self.assertEqual(percentile_r7(samples, 0.95), 38.5)
        summary = summarize_samples(samples)
        self.assertEqual(summary["sample_count"], 4)
        self.assertEqual(summary["median_ns"], 25)
        self.assertEqual(summary["median_absolute_deviation_ns"], 10)
        self.assertTrue(math.isfinite(summary["coefficient_of_variation"]))

    def test_invalid_statistics_values_are_rejected(self):
        for values in ([], [True], [-1], [1.5]):
            with self.subTest(values=values):
                with self.assertRaises(PerformanceBenchmarkError):
                    summarize_samples(values)

    def test_linux_ru_maxrss_is_normalized_from_kibibytes(self):
        self.assertEqual(normalize_ru_maxrss(123, platform_name="linux"), 125_952)
        self.assertEqual(normalize_ru_maxrss(123, platform_name="darwin"), 123)

    def test_controlled_environment_is_exact(self):
        with patch.dict(os.environ, CONTROLLED_ENVIRONMENT, clear=False):
            self.assertEqual(validate_controlled_environment(), CONTROLLED_ENVIRONMENT)
            os.environ["OMP_NUM_THREADS"] = "2"
            with self.assertRaisesRegex(PerformanceBenchmarkError, "environment differs"):
                validate_controlled_environment()

    def test_output_path_and_exclusive_creation(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "result.json"
            self.assertEqual(validate_output_path(path), path.resolve())
            write_exclusive(path, {"fixture_text_included": False})
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {"fixture_text_included": False})
            with self.assertRaises(FileExistsError):
                write_exclusive(path, {})
        with self.assertRaises(ValueError):
            validate_output_path(Path("/var/lib/unapproved.json"))

    def test_cpu_affinity_rejects_unavailable_or_malformed_values(self):
        with self.assertRaises(ValueError):
            apply_affinity("not-a-cpu")
        with patch("os.sched_getaffinity", return_value={3}), patch("os.sched_setaffinity"):
            with self.assertRaisesRegex(ValueError, "unavailable"):
                apply_affinity("2")


@override_settings(
    LLM_ENABLED=False,
    JOB_ENRICHMENT_ENABLED=False,
    CV_LLM_EXTRACTION_ENABLED=False,
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
)
class PerformanceSmokeTests(TransactionTestCase):
    def test_canonicalization_smoke_is_isolated_correct_private_and_cpu_only(self):
        with patch.dict(os.environ, CONTROLLED_ENVIRONMENT, clear=False):
            result = run_with_runner(
                deterministic_root=DETERMINISTIC_ROOT,
                taxonomy_snapshot_dir=TAXONOMY_ROOT,
                profile="canonicalization",
                warmups=0,
                iterations=1,
            )
        self.assertEqual(result["case_count"], 30)
        self.assertEqual(len(result["case_ids"]), 30)
        self.assertEqual(len(result["output_digest"]), 64)
        self.assertTrue(result["cpu_only"])
        serialized = json.dumps(result)
        self.assertNotIn(str(Path.home()), serialized)
        self.assertNotIn("Synthetic Candidate", serialized)
        self.assertTrue(str(self._database_name_for_assertion()).startswith("test_"))

    def _database_name_for_assertion(self):
        from django.db import connection

        return connection.settings_dict["NAME"]

    def test_runner_cleans_workspace_after_failure(self):
        observed: list[Path] = []

        def fail(runner):
            workspace = Path(runner.workspace.name)
            observed.append(workspace)
            (workspace / "synthetic.pdf").write_bytes(b"private synthetic bytes")
            raise RuntimeError("synthetic failure")

        with patch.dict(os.environ, CONTROLLED_ENVIRONMENT, clear=False):
            with self.assertRaisesRegex(RuntimeError, "synthetic failure"):
                run_with_runner(
                    deterministic_root=DETERMINISTIC_ROOT,
                    taxonomy_snapshot_dir=TAXONOMY_ROOT,
                    profile="cv_extraction",
                    warmups=0,
                    iterations=1,
                    callback=fail,
                )
        self.assertEqual(len(observed), 1)
        self.assertFalse(observed[0].exists())
