from django.core.management.base import BaseCommand

from apps.jobs.services.ingestion import JobIngestionService


class Command(BaseCommand):
    help = "Repair France Travail JobSource.last_successful_sync_at from completed successful ingestion runs."

    def handle(self, *args, **options):
        repaired = JobIngestionService.repair_france_travail_source_sync_from_runs()
        if repaired:
            self.stdout.write(self.style.SUCCESS("France Travail JobSource sync timestamp repaired."))
        else:
            self.stdout.write("No France Travail JobSource sync repair was needed.")
