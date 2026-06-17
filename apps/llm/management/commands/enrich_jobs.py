from django.core.management.base import BaseCommand
from django.conf import settings
from apps.jobs.models import NormalizedJob, JobStatus
from apps.llm.services.job_enrichment import job_qualifies_for_enrichment, enrich_job
from apps.llm.tasks import enrich_job_task

class Command(BaseCommand):
    help = "Enqueue jobs for LLM enrichment."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=50, help="Max jobs to enqueue")
        parser.add_argument("--only-qualifying", action="store_true", help="Only process jobs that qualify based on rules")
        parser.add_argument("--dry-run", action="store_true", help="Print what would happen without doing it")
        parser.add_argument("--force", action="store_true", help="Force processing regardless of qualification or daily limit")
        parser.add_argument("--sync", action="store_true", help="Run synchronously instead of enqueuing Celery tasks (local dev only)")

    def handle(self, *args, **options):
        limit = options["limit"]
        only_qualifying = options["only_qualifying"]
        dry_run = options["dry_run"]
        force = options["force"]
        sync = options["sync"]

        if sync and not settings.DEBUG:
            self.stdout.write(self.style.ERROR("--sync is only allowed in local DEV mode (DEBUG=True)"))
            return

        if not settings.JOB_ENRICHMENT_ENABLED and not force and not dry_run:
            self.stdout.write(self.style.WARNING("Job enrichment is disabled via JOB_ENRICHMENT_ENABLED. Use --force to override."))
            return

        jobs = NormalizedJob.objects.filter(status=JobStatus.ACTIVE, country="FR").order_by("-published_at")
        
        candidates = []
        for job in jobs:
            if len(candidates) >= limit:
                break
                
            if force or not only_qualifying or job_qualifies_for_enrichment(job):
                candidates.append(job)

        self.stdout.write(self.style.SUCCESS(f"Found {len(candidates)} candidates for enrichment."))

        if dry_run:
            self.stdout.write("DRY RUN mode. Nothing will be enqueued or processed.")
            return

        enqueued = 0
        processed = 0

        for job in candidates:
            if sync:
                enrichment = enrich_job(job, force=force)
                self.stdout.write(f"Sync processed {job.id}: {enrichment.status}")
                processed += 1
            else:
                enrich_job_task.delay(job.id, force=force)
                enqueued += 1

        if sync:
            self.stdout.write(self.style.SUCCESS(f"Successfully processed {processed} jobs synchronously."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Successfully enqueued {enqueued} jobs for enrichment."))
