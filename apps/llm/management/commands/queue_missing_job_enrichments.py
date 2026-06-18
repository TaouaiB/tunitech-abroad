from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.jobs.models import NormalizedJob, JobStatus
from apps.llm.models import JobEnrichment
from apps.llm.services.job_enrichment import (
    get_allowed_skill_signal_qualities,
    queue_selected_eligible_enrichments,
)


class Command(BaseCommand):
    help = "Safely queue enrichment for active FR jobs without any JobEnrichment record."

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='Maximum number of jobs to queue',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print what would be queued without actually queuing',
        )

    def handle(self, *args, **options):
        limit = options['limit']
        dry_run = options['dry_run']
        if limit < 1:
            raise CommandError("--limit must be greater than zero.")

        if not settings.JOB_ENRICHMENT_ENABLED:
            self.stdout.write(self.style.WARNING("JOB_ENRICHMENT_ENABLED is False. Skipping."))
            self.stdout.write("eligible: 0")
            self.stdout.write("skipped_low_relevance: 0")
            self.stdout.write("queued: 0")
            return

        effective_limit = min(limit, settings.JOB_ENRICHMENT_RETRY_MAX_PER_RUN)
        allowed_qualities = get_allowed_skill_signal_qualities()

        base_jobs_qs = NormalizedJob.objects.filter(
            status=JobStatus.ACTIVE,
            country="FR",
        ).exclude(
            id__in=JobEnrichment.objects.values_list('job_id', flat=True)
        )

        eligible_qs = base_jobs_qs.filter(
            classification_json__confidence="high",
            skill_signal_quality__in=allowed_qualities
        )
        skipped_low_relevance = base_jobs_qs.exclude(
            classification_json__confidence="high",
        ).count() + base_jobs_qs.filter(
            classification_json__confidence="high",
        ).exclude(
            skill_signal_quality__in=allowed_qualities
        ).count()
        eligible_count = eligible_qs.count()

        self.stdout.write(f"eligible: {eligible_count}")
        self.stdout.write(f"skipped_low_relevance: {skipped_low_relevance}")

        if eligible_count == 0:
            self.stdout.write("queued: 0")
            return

        jobs_to_queue = list(
            eligible_qs.order_by('created_at').values_list('id', flat=True)[:effective_limit]
        )

        if dry_run:
            self.stdout.write(f"queued: 0")
            self.stdout.write(self.style.SUCCESS(f"[DRY-RUN] would_queue: {len(jobs_to_queue)}"))
            return

        queued = queue_selected_eligible_enrichments(
            job_ids=jobs_to_queue,
            limit=effective_limit,
            require_retry_enabled=False
        )

        self.stdout.write(self.style.SUCCESS(f"queued: {queued}"))
