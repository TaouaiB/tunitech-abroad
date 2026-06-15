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

    def handle(self, *args, **options):
        path = options["path"]
        source_slug = options["source"]
        
        if not os.path.exists(path):
            self.stderr.write(self.style.ERROR(f"File not found: {path}"))
            return
            
        run = JobFixtureIngestionService.load_fixture_file(path, source_slug=source_slug)
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Ingestion run completed ({run.status}). "
                f"Fetched: {run.fetched_count}, Created: {run.created_count}, "
                f"Updated: {run.updated_count}, Unchanged: {run.unchanged_count}, Errors: {run.error_count}"
            )
        )
