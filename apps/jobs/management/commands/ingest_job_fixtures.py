import os
from django.core.management.base import BaseCommand
from apps.jobs.services.fixture_ingestion import JobFixtureIngestionService


class Command(BaseCommand):
    help = "Ingest sample jobs from a fixture file"

    def add_arguments(self, parser):
        parser.add_argument("path", type=str, help="Path to the JSON fixture file")
        parser.add_argument(
            "--source", type=str, default="france_travail", help="Source slug (default: france_travail)"
        )
        parser.add_argument(
            "--normalize",
            action="store_true",
            help="Synchronously normalize ingested fixture jobs into public searchable jobs.",
        )

    def handle(self, *args, **options):
        path = options["path"]
        source_slug = options["source"]
        normalize = options["normalize"]
        
        if not os.path.exists(path):
            self.stderr.write(self.style.ERROR(f"File not found: {path}"))
            return
            
        if normalize:
            run, normalized_count, failed_count = JobFixtureIngestionService.ingest_fixture_and_normalize(
                path,
                source_slug=source_slug,
            )
        else:
            run = JobFixtureIngestionService.load_fixture_file(path, source_slug=source_slug)
            normalized_count = 0
            failed_count = 0

        self.stdout.write(
            self.style.SUCCESS(
                f"Ingestion run completed ({run.status}). "
                f"Fetched: {run.fetched_count}, Created: {run.created_count}, "
                f"Updated: {run.updated_count}, Unchanged: {run.unchanged_count}, Errors: {run.error_count}, "
                f"Normalized: {normalized_count}, Normalization failed: {failed_count}"
            )
        )
