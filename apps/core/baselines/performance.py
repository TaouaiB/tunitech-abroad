from __future__ import annotations

import gc
import hashlib
import json
import math
import os
import resource
import statistics
import tempfile
import time
import tracemalloc
from pathlib import Path
from typing import Any, Callable

from django.conf import settings
from django.db import connection

from apps.core.baselines.deterministic import (
    BASELINE_VERSION,
    _build_canonical_domain,
    _build_cv_domain,
    _build_job_domain,
    _build_matching_domain,
    _make_source,
    _skill_map,
    canonical_json_bytes,
    external_calls_forbidden,
    populate_test_database,
    reset_synthetic_state,
)


BENCHMARK_CONTRACT_VERSION = "ml0-hardware-cpu-memory-v1"
EXPECTED_PROFILE_COUNTS = {
    "job_extraction": 43,
    "cv_extraction": 8,
    "canonicalization": 30,
    "matching_recommendation": 10,
    "end_to_end": 91,
}
PROFILE_TO_FILE = {
    "job_extraction": "job_extraction.json",
    "cv_extraction": "cv_extraction.json",
    "canonicalization": "canonicalization.json",
    "matching_recommendation": "matching_recommendation.json",
}
CONTROLLED_ENVIRONMENT = {
    "PYTHONHASHSEED": "0",
    "OMP_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
    "TOKENIZERS_PARALLELISM": "false",
    "CUDA_VISIBLE_DEVICES": "",
}


class PerformanceBenchmarkError(ValueError):
    """A sanitized deterministic performance-benchmark failure."""


def percentile_r7(values: list[int], percentile: float) -> float:
    """Return the Hyndman-Fan type 7 linearly interpolated percentile."""

    if not values:
        raise PerformanceBenchmarkError("percentile requires at least one sample")
    if isinstance(percentile, bool) or not isinstance(percentile, (int, float)):
        raise PerformanceBenchmarkError("percentile must be numeric")
    if not 0 <= percentile <= 1:
        raise PerformanceBenchmarkError("percentile must be between zero and one")
    ordered = sorted(values)
    position = (len(ordered) - 1) * percentile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return float(ordered[lower])
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def summarize_samples(values: list[int]) -> dict[str, float | int]:
    if not values or any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in values):
        raise PerformanceBenchmarkError("samples must be non-negative integers")
    mean = statistics.fmean(values)
    median = statistics.median(values)
    standard_deviation = statistics.pstdev(values)
    mad = statistics.median(abs(value - median) for value in values)
    return {
        "sample_count": len(values),
        "minimum_ns": min(values),
        "maximum_ns": max(values),
        "mean_ns": mean,
        "median_ns": median,
        "p90_ns": percentile_r7(values, 0.90),
        "p95_ns": percentile_r7(values, 0.95),
        "p99_ns": percentile_r7(values, 0.99),
        "standard_deviation_ns": standard_deviation,
        "median_absolute_deviation_ns": mad,
        "coefficient_of_variation": standard_deviation / mean if mean else 0.0,
        "throughput_per_second": 1_000_000_000 / mean if mean else 0.0,
    }


def normalize_ru_maxrss(value: int, *, platform_name: str = "linux") -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise PerformanceBenchmarkError("ru_maxrss must be a non-negative integer")
    return value * 1024 if platform_name == "linux" else value


def current_rss_bytes() -> int:
    try:
        fields = Path("/proc/self/statm").read_text(encoding="ascii").split()
        return int(fields[1]) * os.sysconf("SC_PAGE_SIZE")
    except (OSError, ValueError, IndexError) as exc:
        raise PerformanceBenchmarkError("current RSS is unavailable") from exc


def validate_controlled_environment() -> dict[str, str]:
    actual = {name: os.environ.get(name) for name in CONTROLLED_ENVIRONMENT}
    if actual != CONTROLLED_ENVIRONMENT:
        raise PerformanceBenchmarkError("controlled benchmark environment differs")
    return dict(CONTROLLED_ENVIRONMENT)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _combined_output_digest(digests: dict[str, str]) -> str:
    digest = hashlib.sha256()
    for profile in sorted(digests):
        digest.update(profile.encode("ascii"))
        digest.update(b"\0")
        digest.update(digests[profile].encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


class DeterministicPerformanceRunner:
    def __init__(self, *, deterministic_root: Path, taxonomy_snapshot_dir: Path):
        if not str(connection.settings_dict.get("NAME", "")).startswith("test_"):
            raise PerformanceBenchmarkError("benchmark requires an isolated Django test database")
        if settings.LLM_ENABLED or settings.JOB_ENRICHMENT_ENABLED or settings.CV_LLM_EXTRACTION_ENABLED:
            raise PerformanceBenchmarkError("benchmark requires LLM and enrichment flags off")
        validate_controlled_environment()
        self.deterministic_root = deterministic_root.resolve()
        self.expected_documents = {
            profile: json.loads((self.deterministic_root / filename).read_text(encoding="utf-8"))
            for profile, filename in PROFILE_TO_FILE.items()
        }
        self.expected_digests = {
            profile: _sha256_bytes((self.deterministic_root / filename).read_bytes())
            for profile, filename in PROFILE_TO_FILE.items()
        }
        self.expected_digests["end_to_end"] = _combined_output_digest(self.expected_digests)
        self.workspace = tempfile.TemporaryDirectory(prefix="tuniatlas-performance-")
        reset_synthetic_state()
        populate_test_database(taxonomy_snapshot_dir.resolve())

    def close(self) -> None:
        reset_synthetic_state()
        self.workspace.cleanup()

    def _domain_once(self, profile: str) -> tuple[list[str], str]:
        reset_synthetic_state()
        skills = _skill_map()
        workspace = Path(self.workspace.name)
        with external_calls_forbidden():
            if profile == "job_extraction":
                _cases, outputs = _build_job_domain(_make_source(), skills)
            elif profile == "cv_extraction":
                _cases, outputs = _build_cv_domain(skills, workspace)
            elif profile == "canonicalization":
                _cases, outputs = _build_canonical_domain(skills)
            elif profile == "matching_recommendation":
                _cases, outputs = _build_matching_domain(_make_source(), skills)
            elif profile == "end_to_end":
                source = _make_source()
                _job_cases, job_outputs = _build_job_domain(source, skills)
                _canonical_cases, canonical_outputs = _build_canonical_domain(skills)
                _cv_cases, cv_outputs = _build_cv_domain(skills, workspace)
                _matching_cases, matching_outputs = _build_matching_domain(source, skills)
                documents = {
                    "job_extraction": job_outputs,
                    "cv_extraction": cv_outputs,
                    "canonicalization": canonical_outputs,
                    "matching_recommendation": matching_outputs,
                }
                digests: dict[str, str] = {}
                case_ids: list[str] = []
                for domain, domain_outputs in documents.items():
                    document = {
                        "baseline_version": BASELINE_VERSION,
                        "domain": domain,
                        "outputs": sorted(domain_outputs, key=lambda item: item["case_id"]),
                    }
                    rendered = canonical_json_bytes(document)
                    digest = _sha256_bytes(rendered)
                    if digest != self.expected_digests[domain]:
                        raise PerformanceBenchmarkError("deterministic output digest mismatch")
                    digests[domain] = digest
                    case_ids.extend(item["case_id"] for item in document["outputs"])
                combined = _combined_output_digest(digests)
                if combined != self.expected_digests["end_to_end"]:
                    raise PerformanceBenchmarkError("end-to-end output digest mismatch")
                return sorted(case_ids), combined
            else:
                raise PerformanceBenchmarkError("unknown application benchmark profile")

        document = {
            "baseline_version": BASELINE_VERSION,
            "domain": profile,
            "outputs": sorted(outputs, key=lambda item: item["case_id"]),
        }
        rendered = canonical_json_bytes(document)
        digest = _sha256_bytes(rendered)
        if digest != self.expected_digests[profile]:
            raise PerformanceBenchmarkError("deterministic output digest mismatch")
        return [item["case_id"] for item in document["outputs"]], digest

    def measure(self, *, profile: str, warmups: int, iterations: int) -> dict[str, Any]:
        if profile not in EXPECTED_PROFILE_COUNTS:
            raise PerformanceBenchmarkError("unknown application benchmark profile")
        if isinstance(warmups, bool) or not isinstance(warmups, int) or warmups < 0:
            raise PerformanceBenchmarkError("warmups must be a non-negative integer")
        if isinstance(iterations, bool) or not isinstance(iterations, int) or iterations < 1:
            raise PerformanceBenchmarkError("iterations must be a positive integer")

        gc.collect()
        rss_before = current_rss_bytes()
        peak_before = normalize_ru_maxrss(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        tracemalloc.start()
        try:
            for _ in range(warmups):
                self._domain_once(profile)
            samples: list[int] = []
            case_ids: list[str] = []
            output_digest = ""
            for _ in range(iterations):
                gc.collect()
                started = time.perf_counter_ns()
                case_ids, output_digest = self._domain_once(profile)
                samples.append(time.perf_counter_ns() - started)
            python_current, python_peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        rss_after = current_rss_bytes()
        peak_rss = normalize_ru_maxrss(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        if len(case_ids) != EXPECTED_PROFILE_COUNTS[profile]:
            raise PerformanceBenchmarkError("application profile case count mismatch")
        return {
            "benchmark_contract_version": BENCHMARK_CONTRACT_VERSION,
            "profile": profile,
            "case_count": len(case_ids),
            "case_ids": case_ids,
            "warmup_count": warmups,
            "samples_ns": samples,
            "summary": summarize_samples(samples),
            "memory": {
                "rss_before_bytes": rss_before,
                "rss_after_bytes": rss_after,
                "peak_rss_bytes": peak_rss,
                "peak_rss_delta_bytes": max(0, peak_rss - peak_before),
                "python_allocation_peak_bytes": python_peak,
                "python_allocation_current_end_bytes": python_current,
            },
            "output_digest": output_digest,
            "process_exit_code": 0,
            "cpu_only": os.environ.get("CUDA_VISIBLE_DEVICES") == "",
            "controlled_environment": validate_controlled_environment(),
        }


def run_with_runner(
    *,
    deterministic_root: Path,
    taxonomy_snapshot_dir: Path,
    profile: str,
    warmups: int,
    iterations: int,
    callback: Callable[[DeterministicPerformanceRunner], None] | None = None,
) -> dict[str, Any]:
    runner = DeterministicPerformanceRunner(
        deterministic_root=deterministic_root,
        taxonomy_snapshot_dir=taxonomy_snapshot_dir,
    )
    try:
        if callback is not None:
            callback(runner)
        return runner.measure(profile=profile, warmups=warmups, iterations=iterations)
    finally:
        runner.close()
