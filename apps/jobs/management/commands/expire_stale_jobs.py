from django.core.management.base import BaseCommand
from apps.jobs.services.expiry import JobExpiryService

class Command(BaseCommand):
    help = 'Expire stale IT jobs'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=21, help='Number of days before expiring')
        parser.add_argument('--dry-run', action='store_true', help='Do not save to database')

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        
        self.stdout.write(f"Looking for active jobs not seen in {days} days...")
        
        if dry_run:
            self.stdout.write("Dry run, not marking any jobs as stale.")
            return

        expired_count = JobExpiryService.mark_stale_jobs(days)
        self.stdout.write(self.style.SUCCESS(f"Marked {expired_count} jobs as stale."))
