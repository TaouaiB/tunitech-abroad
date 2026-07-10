from __future__ import annotations

import os
import subprocess
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.jobs.services.gate_e_rematerialization import GateEOptions, GateERematerializationService


class Command(BaseCommand):
    help = "Gate E local-only job skill rematerialization and before/after comparison."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", help="Write changes. Defaults to dry-run.")
        parser.add_argument("--report-path", default="", help="Markdown report path.")
        parser.add_argument("--limit", type=int, help="Limit active jobs processed.")
        parser.add_argument("--job-public-id", help="Process one public job UUID.")
        parser.add_argument("--include-cvs", action="store_true", help="Explicitly reparse active non-deleted CVs.")
        parser.add_argument("--include-matches", action="store_true", help="Refresh affected matches and recommendations.")
        parser.add_argument("--skip-search-vectors", action="store_true", help="Skip search vector rebuild.")
        parser.add_argument("--backup-dir", default="/tmp", help="Local directory for apply-mode pg_dump backups.")

    def handle(self, *args, **options):
        apply = options["apply"]
        if options.get("limit") is not None and options["limit"] < 1:
            raise CommandError("--limit must be greater than zero.")
        if options["include_cvs"] and not apply:
            raise CommandError("Refusing --include-cvs without --apply; CV reparsing is explicit apply-only work.")
        if options["include_cvs"] and getattr(settings, "LLM_ENABLED", False):
            raise CommandError("Refusing --include-cvs while LLM_ENABLED=True.")

        db_info = self._safe_database_info()
        backup_path = ""
        if apply:
            self._assert_local_apply_allowed(db_info)
            backup_path = self._create_backup(options["backup_dir"])
            self.stdout.write(f"Verified local backup: {backup_path}")

        service_options = GateEOptions(
            apply=apply,
            report_path=options["report_path"],
            limit=options.get("limit"),
            job_public_id=options.get("job_public_id"),
            include_cvs=options["include_cvs"],
            include_matches=options["include_matches"],
            skip_search_vectors=options["skip_search_vectors"],
            backup_path=backup_path,
            settings_module=os.environ.get("DJANGO_SETTINGS_MODULE", ""),
            git_commit=self._git_commit(),
            database_info=db_info,
        )
        result = GateERematerializationService.run(service_options)

        mode = "APPLY" if apply else "DRY-RUN"
        self.stdout.write(self.style.SUCCESS(f"[{mode}] Gate E report: {result.report_path}"))
        self.stdout.write(
            "Processed jobs: "
            f"{result.processed_jobs}; rematerialized: {result.rematerialized_jobs}; "
            f"search vectors: {result.search_vectors_rebuilt}; failures: {len(result.failures)}"
        )
        if result.failures:
            raise CommandError(f"Gate E completed with {len(result.failures)} row failures. See report.")

    @staticmethod
    def _safe_database_info() -> dict[str, str]:
        db = settings.DATABASES["default"]
        return {
            "engine": db.get("ENGINE", ""),
            "host": db.get("HOST") or "",
            "name": db.get("NAME") or "",
            "port": str(db.get("PORT") or ""),
        }

    @staticmethod
    def _assert_local_apply_allowed(db_info: dict[str, str]) -> None:
        settings_module = os.environ.get("DJANGO_SETTINGS_MODULE", "")
        if settings_module != "config.settings.local":
            raise CommandError("Refusing Gate E apply unless DJANGO_SETTINGS_MODULE=config.settings.local.")
        if not settings.DEBUG:
            raise CommandError("Refusing Gate E apply when DEBUG=False.")

        host = (db_info.get("host") or "").lower()
        local_hosts = {"", "localhost", "127.0.0.1", "::1"}
        if host not in local_hosts:
            raise CommandError("Refusing Gate E apply because database host is not local.")
        if "postgresql" not in (db_info.get("engine") or ""):
            raise CommandError("Refusing Gate E apply because the configured database is not PostgreSQL.")

    def _create_backup(self, backup_dir: str) -> str:
        db = settings.DATABASES["default"]
        backup_root = Path(backup_dir)
        backup_root.mkdir(parents=True, exist_ok=True)
        timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_root / f"tuniatlas_gate_e_backup_{timestamp}.dump"

        command = [
            "pg_dump",
            "--format=custom",
            "--file",
            str(backup_path),
            "--dbname",
            str(db.get("NAME") or ""),
        ]
        if db.get("HOST"):
            command.extend(["--host", str(db["HOST"])])
        if db.get("PORT"):
            command.extend(["--port", str(db["PORT"])])
        if db.get("USER"):
            command.extend(["--username", str(db["USER"])])

        env = os.environ.copy()
        if db.get("PASSWORD"):
            env["PGPASSWORD"] = str(db["PASSWORD"])

        try:
            completed = subprocess.run(command, env=env, capture_output=True, text=True, check=False)
        except FileNotFoundError as exc:
            self._create_backup_with_docker_client(db, backup_path, env)
            return str(backup_path)
        if completed.returncode != 0:
            raise CommandError("PostgreSQL backup failed; no mutation was run.")
        if not backup_path.exists() or backup_path.stat().st_size <= 0:
            raise CommandError("PostgreSQL backup file was not created or is empty; no mutation was run.")
        return str(backup_path)

    @staticmethod
    def _create_backup_with_docker_client(db: dict, backup_path: Path, env: dict[str, str]) -> None:
        host = str(db.get("HOST") or "")
        if not host:
            raise CommandError("PostgreSQL backup failed because pg_dump is not installed and socket backup cannot use Docker.")

        docker_host = "127.0.0.1" if host in {"localhost", "::1"} else host
        command = [
            "docker",
            "run",
            "--rm",
            "--network",
            "host",
            "-e",
            "PGPASSWORD",
            "postgres:16-alpine",
            "pg_dump",
            "--format=custom",
            "--dbname",
            str(db.get("NAME") or ""),
            "--host",
            docker_host,
        ]
        if db.get("PORT"):
            command.extend(["--port", str(db["PORT"])])
        if db.get("USER"):
            command.extend(["--username", str(db["USER"])])

        try:
            completed = subprocess.run(command, env=env, capture_output=True, check=False)
        except FileNotFoundError as exc:
            raise CommandError("PostgreSQL backup failed because neither pg_dump nor Docker is available; no mutation was run.") from exc
        if completed.returncode != 0:
            raise CommandError("PostgreSQL Docker backup failed; no mutation was run.")
        backup_path.write_bytes(completed.stdout)
        if not backup_path.exists() or backup_path.stat().st_size <= 0:
            raise CommandError("PostgreSQL Docker backup file was not created or is empty; no mutation was run.")

    @staticmethod
    def _git_commit() -> str:
        completed = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            return "unknown"
        return completed.stdout.strip()
