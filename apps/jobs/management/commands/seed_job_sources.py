from django.core.management.base import BaseCommand

from apps.jobs.services.source_seed import seed_job_sources


class Command(BaseCommand):
    help = "Seeds the initial job sources (e.g. France Travail)"

    def handle(self, *args, **options):
        seed_job_sources()
        self.stdout.write(self.style.SUCCESS("Successfully seeded job sources."))
