from django.core.management.base import BaseCommand

from apps.jobs.models import NormalizedJob
from apps.jobs.services.skill_extraction import JobSkillExtractionService


class Command(BaseCommand):
    help = "Re-extracts and rematerializes skills for normalized jobs."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, help="Limit number of jobs to rematerialize")
        parser.add_argument("--batch-size", type=int, default=500, help="Batch size for query")
        parser.add_argument("--dry-run", action="store_true", help="Print what would happen without actually doing it")

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
            self.stdout.write(self.style.SUCCESS(f"[Dry Run] Would rematerialize skills for {total} jobs."))
            return

        self.stdout.write(f"Rematerializing skills for {total} jobs (batch size {batch_size})...")

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
                JobSkillExtractionService.extract_for_job(job)
                processed += 1
                last_id = job.id

            self.stdout.write(f"  Processed {processed}/{total} jobs.")

        self.stdout.write(self.style.SUCCESS(f"Finished rematerializing skills for {processed} jobs."))
