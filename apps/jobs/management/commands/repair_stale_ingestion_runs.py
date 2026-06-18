from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from apps.jobs.models import JobIngestionRun

class Command(BaseCommand):
    help = 'Finds running JobIngestionRun older than INGESTION_STALE_RUNNING_MINUTES and marks them as failed'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print what would be repaired without actually making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        stale_cutoff = timezone.now() - timedelta(minutes=settings.INGESTION_STALE_RUNNING_MINUTES)
        
        stale_runs = JobIngestionRun.objects.filter(
            status="running",
            started_at__lt=stale_cutoff,
        )
        
        count = stale_runs.count()
        if count == 0:
            self.stdout.write(self.style.SUCCESS("No stale running ingestion runs found."))
            return
            
        self.stdout.write(f"Found {count} stale running ingestion runs.")
        
        if dry_run:
            for run in stale_runs:
                self.stdout.write(self.style.SUCCESS(f"[DRY-RUN] Would mark run {run.id} as failed."))
            return
            
        for run in stale_runs:
            run.status = "failed"
            run.finished_at = timezone.now()
            run.error_summary = "Marked failed by stale-run repair"
            run.save(update_fields=['status', 'finished_at', 'error_summary'])
            
        self.stdout.write(self.style.SUCCESS(f"Successfully repaired {count} stale runs."))
