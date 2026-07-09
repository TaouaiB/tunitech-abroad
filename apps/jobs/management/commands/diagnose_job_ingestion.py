import json
from django.core.management.base import BaseCommand
from apps.jobs.services.diagnostics import JobIngestionDiagnosticsService

class Command(BaseCommand):
    help = "Run job ingestion diagnostics and output as JSON following the shared contract."

    def add_arguments(self, parser):
        parser.add_argument("--source-slug", default="france_travail")

    def handle(self, *args, **options):
        diagnostics = JobIngestionDiagnosticsService.run(source_slug=options["source_slug"])
        self.stdout.write(json.dumps(diagnostics, indent=2))
