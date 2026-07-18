#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ML_ROOT = ROOT.parent / "tuniatlas-ml"
DETERMINISTIC_ROOT = ML_ROOT / "data/private/baselines/ml0/deterministic-v2"
TAXONOMY_ROOT = (
    ML_ROOT
    / "data/private/taxonomy/snapshots"
    / "sha256-d6d5aebf5e4b958f163d2f33b8d441a36e6d638ac8c92379f18e6ebd40e2fc05"
)
APPROVED_OUTPUT_ROOTS = (ML_ROOT / "tmp", Path("/tmp"))


def validate_output_path(path: Path) -> Path:
    resolved = path.resolve()
    if any(root.resolve() in resolved.parents for root in APPROVED_OUTPUT_ROOTS):
        return resolved
    raise ValueError("output must be below an approved private temporary root")


def apply_affinity(raw: str) -> list[int]:
    try:
        cpus = sorted({int(value) for value in raw.split(",") if value})
    except ValueError as exc:
        raise ValueError("affinity CPU list is malformed") from exc
    if not cpus or any(cpu < 0 for cpu in cpus):
        raise ValueError("affinity CPU list is invalid")
    if not hasattr(os, "sched_setaffinity"):
        raise ValueError("CPU affinity is unavailable")
    available = os.sched_getaffinity(0)
    if not set(cpus).issubset(available):
        raise ValueError("requested affinity is unavailable")
    os.sched_setaffinity(0, set(cpus))
    actual = sorted(os.sched_getaffinity(0))
    if actual != cpus:
        raise ValueError("CPU affinity could not be enforced")
    return actual


def write_exclusive(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    payload = (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
    except Exception:
        path.unlink(missing_ok=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True)
    parser.add_argument("--warmups", required=True, type=int)
    parser.add_argument("--iterations", required=True, type=int)
    parser.add_argument("--affinity-cpus", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    if os.geteuid() == 0:
        raise SystemExit("benchmark refuses root")
    affinity = apply_affinity(args.affinity_cpus)
    output = validate_output_path(args.output)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
    if os.environ["DJANGO_SETTINGS_MODULE"] != "config.settings.local":
        raise SystemExit("benchmark refuses non-local settings")

    sys.path.insert(0, str(ROOT))
    os.chdir(ROOT)
    import django

    django.setup()
    from django.conf import settings
    from django.db import connection
    from django.test.runner import DiscoverRunner

    from apps.core.baselines.performance import run_with_runner

    if not settings.DEBUG:
        raise SystemExit("benchmark refuses production settings")
    original_name = connection.settings_dict.get("NAME")
    runner = DiscoverRunner(interactive=False, verbosity=0)
    runner.setup_test_environment()
    old_config = runner.setup_databases()
    try:
        test_name = connection.settings_dict.get("NAME")
        if not str(test_name).startswith("test_") or test_name == original_name:
            raise RuntimeError("Django test-database isolation could not be proven")
        result = run_with_runner(
            deterministic_root=DETERMINISTIC_ROOT,
            taxonomy_snapshot_dir=TAXONOMY_ROOT,
            profile=args.profile,
            warmups=args.warmups,
            iterations=args.iterations,
        )
        result["affinity_cpus"] = affinity
        result["test_database_isolated"] = True
        write_exclusive(output, result)
    finally:
        runner.teardown_databases(old_config)
        runner.teardown_test_environment()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
