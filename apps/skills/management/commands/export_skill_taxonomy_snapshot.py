"""Export the deterministic Django skill taxonomy snapshot.

Run from the Django repository::

    python manage.py export_skill_taxonomy_snapshot \\
        --output-root <directory> \\
        --settings=config.settings.local

The command refuses to run on a dirty worktree or a branch other than
``dev`` (tests inject ``--allow-branch`` to override this). It never
prints snapshot contents and never writes outside ``--output-root``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.skills.services.taxonomy_snapshot import (
    TaxonomySnapshotEnvironmentError,
    TaxonomySnapshotPublishError,
    TaxonomySnapshotService,
    assert_source_environment,
)


class Command(BaseCommand):
    help = "Export a deterministic ML-0 skill taxonomy snapshot."

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--output-root",
            required=True,
            help="Existing directory that will receive the versioned snapshot subdirectory.",
        )
        parser.add_argument(
            "--source-product",
            default="TuniAtlas Jobs",
        )
        parser.add_argument(
            "--source-repository",
            default="TaouaiB/tunitech-abroad",
        )
        parser.add_argument(
            "--source-branch",
            default="dev",
        )
        parser.add_argument(
            "--allow-branch",
            default=None,
            help=(
                "Internal override used by tests to disable the branch guard. "
                "Do not pass in production."
            ),
        )
        parser.add_argument(
            "--allow-dirty",
            action="store_true",
            help=(
                "Internal override used by tests to disable the clean-worktree guard. "
                "Do not pass in production."
            ),
        )
        parser.add_argument(
            "--git-commit",
            default=None,
            help=(
                "Override the recorded source commit. "
                "Used by tests for deterministic metadata."
            ),
        )

    def handle(self, *args, **options):
        output_root = Path(options["output_root"]).resolve()
        if not output_root.is_dir():
            raise CommandError(
                f"Output root does not exist or is not a directory: {output_root}"
            )

        try:
            if not options["allow_dirty"]:
                assert_source_environment(
                    require_branch=options["allow_branch"] or options["source_branch"],
                )
        except TaxonomySnapshotEnvironmentError as exc:
            raise CommandError(str(exc)) from exc

        service = TaxonomySnapshotService(
            source_product=options["source_product"],
            source_repository=options["source_repository"],
            source_branch=options["source_branch"],
        )

        try:
            result = service.export(output_root, git_commit=options["git_commit"])
        except TaxonomySnapshotPublishError as exc:
            raise CommandError(str(exc)) from exc
        except Exception as exc:
            # Avoid leaking database content; only the error type and message
            # are printed.
            self.stderr.write(f"export_failed: {type(exc).__name__}")
            raise CommandError(str(exc)) from exc

        payload = result.to_public_dict()
        self.stdout.write(json.dumps(payload, indent=2, sort_keys=True))
        sys.stdout.flush()
