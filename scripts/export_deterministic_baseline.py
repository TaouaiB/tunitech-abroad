#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ML_ROOT = ROOT.parent / "tuniatlas-ml"
APPROVED_ROOT = ML_ROOT / "data/private/baselines/ml0"


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result.stdout.strip()


def validate_source_repository() -> tuple[str, str]:
    branch = _git("branch", "--show-current")
    head = _git("rev-parse", "HEAD")
    origin_dev = _git("rev-parse", "origin/dev")
    if branch != "dev":
        raise ValueError("baseline export requires the dev branch")
    if head != origin_dev:
        raise ValueError("baseline export requires HEAD == origin/dev")
    if _git("status", "--porcelain"):
        raise ValueError("baseline export requires a clean worktree")
    subprocess.run(["git", "diff", "--check"], cwd=ROOT, check=True, timeout=30)
    if len(head) != 40 or any(char not in "0123456789abcdef" for char in head):
        raise ValueError("source commit is malformed")
    return head, branch


def validate_output_path(path: Path, *, allow_temporary: bool) -> Path:
    resolved = path.resolve()
    if resolved == APPROVED_ROOT.resolve() or APPROVED_ROOT.resolve() in resolved.parents:
        return resolved
    temporary_root = Path(tempfile.gettempdir()).resolve()
    if allow_temporary and temporary_root in resolved.parents and resolved.name.startswith("tuniatlas-"):
        return resolved
    raise ValueError("output must be beneath the private ML-0 baseline root or an approved temporary test path")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--allow-temporary-test-output", action="store_true")
    args = parser.parse_args()

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
    if os.environ["DJANGO_SETTINGS_MODULE"] != "config.settings.local":
        raise SystemExit("baseline export refuses non-local settings")

    sys.path.insert(0, str(ROOT))
    os.chdir(ROOT)
    import django

    django.setup()
    from django.conf import settings
    from django.db import connection
    from django.test.runner import DiscoverRunner

    from apps.core.baselines.deterministic import build_bundle, publish_bundle

    if not settings.DEBUG:
        raise SystemExit("baseline export refuses production settings")
    if settings.LLM_ENABLED or settings.JOB_ENRICHMENT_ENABLED or settings.CV_LLM_EXTRACTION_ENABLED:
        raise SystemExit("baseline export requires LLM and enrichment flags off")

    target = validate_output_path(args.output, allow_temporary=args.allow_temporary_test_output)
    commit, branch = validate_source_repository()
    original_name = connection.settings_dict.get("NAME")
    runner = DiscoverRunner(interactive=False, verbosity=1)
    runner.setup_test_environment()
    old_config = runner.setup_databases()
    try:
        test_name = connection.settings_dict.get("NAME")
        if not str(test_name).startswith("test_") or test_name == original_name:
            raise RuntimeError("Django test-database isolation could not be proven")
        manifest, publication = publish_bundle(
            target,
            lambda staging: build_bundle(staging, django_commit=commit, django_branch=branch),
        )
    finally:
        runner.teardown_databases(old_config)
        runner.teardown_test_environment()

    print("DETERMINISTIC BASELINE EXPORT: PASS")
    print(f"PUBLICATION: {publication}")
    print(f"DJANGO COMMIT: {commit}")
    print(f"BUNDLE CONTENT SHA256: {manifest['bundle_content_sha256']}")
    print(f"TOTAL CASES: {sum(manifest['case_counts'].values())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
