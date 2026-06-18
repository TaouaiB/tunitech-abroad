from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.llm.services.job_enrichment import force_retry_provider_blocked_enrichments


class Command(BaseCommand):
    help = "Safely canary-retry provider-blocked job enrichments."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=1, help="Maximum provider-blocked enrichments to retry; hard capped at 3.")
        parser.add_argument("--dry-run", action="store_true", default=True, help="Show what would be queued without enqueueing.")
        parser.add_argument("--execute", action="store_true", help="Actually enqueue the canary retry.")

    def handle(self, *args, **options):
        limit = options["limit"]
        if limit < 1:
            raise CommandError("--limit must be greater than zero.")

        dry_run = not options["execute"]
        self.stdout.write(
            self.style.WARNING(
                "WARNING: provider_blocked retries can burn OpenRouter credits or re-trigger provider blocks. "
                "Use only as a canary after provider/admin signoff."
            )
        )

        if not settings.JOB_ENRICHMENT_FORCE_PROVIDER_BLOCKED_RETRY:
            self.stdout.write(
                self.style.WARNING(
                    "JOB_ENRICHMENT_FORCE_PROVIDER_BLOCKED_RETRY is False. No provider-blocked retries queued."
                )
            )
            self.stdout.write("queued: 0")
            return

        result = force_retry_provider_blocked_enrichments(limit=limit, dry_run=dry_run)
        self.stdout.write(f"requested_limit: {result['requested_limit']}")
        self.stdout.write(f"effective_limit: {result['effective_limit']}")
        self.stdout.write(f"candidate_count: {result['candidate_count']}")
        self.stdout.write(f"dry_run: {result['dry_run']}")
        self.stdout.write(f"queued: {result['queued']}")
