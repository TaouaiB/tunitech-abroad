import json
from django.core.management.base import BaseCommand
from apps.jobs.services.eligibility_diagnostics import JobEligibilityDiagnosticsService

class Command(BaseCommand):
    help = "Inspects public job eligibility and outputs diagnostics."

    def handle(self, *args, **options):
        diagnostics = JobEligibilityDiagnosticsService.run()
        self.stdout.write(json.dumps(diagnostics, indent=2))
