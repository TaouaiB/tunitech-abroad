from django.core.management.base import BaseCommand

from apps.jobs.models import NormalizedJob
from apps.jobs.services.search_vector import JobSearchVectorService


class Command(BaseCommand):
    help = "Rebuilds search vectors for normalized jobs."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, help="Limit number of jobs to rebuild")
        parser.add_argument("--batch-size", type=int, default=500, help="Batch size for rebuild")
        parser.add_argument("--dry-run", action="store_true", help="Print what would happen without rebuilding")

    def handle(self, *args, **options):
        limit = options.get("limit")
        batch_size = max(options.get("batch_size", 500), 1)
        dry_run = options.get("dry_run")

        qs = NormalizedJob.objects.all().order_by("-id")
        if limit is not None:
            total = min(max(limit, 0), qs.count())
        else:
            total = qs.count()

        if dry_run:
            self.stdout.write(self.style.SUCCESS(f"[Dry Run] Would rebuild search vectors for {total} jobs."))
            return

        self.stdout.write(f"Rebuilding search vectors for {total} jobs (batch size {batch_size})...")

        processed = 0
        last_id = None

        while processed < total:
            batch_qs = qs
            if last_id is not None:
                batch_qs = batch_qs.filter(id__lt=last_id)

            current_limit = min(batch_size, total - processed)
            batch = list(batch_qs[:current_limit])

            if not batch:
                break

            for job in batch:
                JobSearchVectorService.update_search_vector(job)
                processed += 1
                last_id = job.id

            self.stdout.write(f"  Processed {processed}/{total} jobs.")

        self.stdout.write(self.style.SUCCESS(f"Finished rebuilding search vectors for {processed} jobs."))
