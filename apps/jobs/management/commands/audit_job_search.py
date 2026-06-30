import json
from django.core.management.base import BaseCommand
from apps.jobs.services.search_audit import JobSearchAuditService

class Command(BaseCommand):
    help = "Run job search audit and output as JSON following the shared contract."

    def handle(self, *args, **options):
        diagnostics = JobSearchAuditService.audit()
        self.stdout.write(json.dumps(diagnostics, indent=2))
