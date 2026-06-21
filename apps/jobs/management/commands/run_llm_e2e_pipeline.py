import sys
from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management import call_command
from apps.jobs.models import NormalizedJob
from apps.jobs.services.eligibility import JobEligibilityService
from apps.llm.models import JobEnrichment
from apps.llm.services.job_enrichment import enrich_job

class Command(BaseCommand):
    help = 'Run E2E LLM enrichment pipeline and output observability metrics'

    def add_arguments(self, parser):
        parser.add_argument('--preset', type=str, default='broad_it', help='Keyword preset (e.g. broad_it)')
        parser.add_argument('--limit-per-keyword', type=int, default=10, help='Limit fetched jobs per keyword')
        parser.add_argument('--max-total', type=int, default=100, help='Max total jobs to fetch in this run')
        parser.add_argument('--max-pages-per-keyword', type=int, default=2, help='Max pages to paginate per keyword')
        parser.add_argument('--force-llm-count', type=int, default=100, help='Number of jobs to force enrichment on')
        parser.add_argument('--force-provider-call', action='store_true', help='Bypass cache and force provider call')
        parser.add_argument('--min-llm-success', type=int, default=95, help='Minimum successful enrichments required to pass')
        parser.add_argument('--apply', action='store_true', help='Apply changes to DB (otherwise dry-run where applicable)')

    def handle(self, *args, **options):
        preset = options['preset']
        limit_per_keyword = options['limit_per_keyword']
        max_total = options['max_total']
        max_pages_per_keyword = options['max_pages_per_keyword']
        force_llm_count = options['force_llm_count']
        force_provider_call = options['force_provider_call']
        min_llm_success = options['min_llm_success']
        apply = options['apply']

        if force_provider_call and not settings.DEBUG:
            self.stdout.write(self.style.ERROR("--force-provider-call is only allowed when DEBUG=True."))
            sys.exit(1)

        self.stdout.write(self.style.MIGRATE_HEADING("1. France Travail broad IT ingestion & 2. Normalization"))
        call_command(
            "sync_france_travail_it_jobs",
            preset=preset,
            limit_per_keyword=limit_per_keyword,
            max_total=max_total,
            max_pages_per_keyword=max_pages_per_keyword,
            normalize=True,
            no_enrichment=True,
            dry_run=not apply
        )

        self.stdout.write(self.style.MIGRATE_HEADING("\n3. Controlled LLM enrichment & 4. LLM materialization"))
        jobs_to_enrich = list(NormalizedJob.objects.order_by('-created_at')[:force_llm_count])
        enrichment_count = len(jobs_to_enrich)
        self.stdout.write(f"Selected {enrichment_count} jobs for enrichment.")
        
        success_count = 0
        skipped_count = 0
        failed_count = 0
        provider_attempted_count = 0
        reason_counts = {}
        
        for job in jobs_to_enrich:
            if apply:
                existing = JobEnrichment.objects.filter(job=job).first()
                before_attempts = existing.attempt_count if existing else 0
                before_tokens = existing.total_tokens if existing else 0
                enrichment = enrich_job(job, force=True, force_provider_call=force_provider_call)
                if enrichment.status == JobEnrichment.Status.SUCCESS:
                    success_count += 1
                elif enrichment.status == JobEnrichment.Status.SKIPPED:
                    skipped_count += 1
                else:
                    failed_count += 1
                reason = enrichment.status_reason or "(blank)"
                reason_counts[reason] = reason_counts.get(reason, 0) + 1

                attempted = (
                    enrichment.attempt_count > before_attempts
                    or enrichment.total_tokens > before_tokens
                )
                if attempted and enrichment.status_reason != "provider_circuit_open":
                    provider_attempted_count += 1
            else:
                self.stdout.write(f"Dry run: skipping enrichment for job {job.id}")

        self.stdout.write(f"Enrichment Results: Success={success_count}, Skipped={skipped_count}, Failed={failed_count}")
        self.stdout.write(f"LLM provider attempted: {provider_attempted_count}")
        if reason_counts:
            self.stdout.write("Status reasons:")
            for reason, count in sorted(reason_counts.items()):
                self.stdout.write(f"  {reason}: {count}")

        self.stdout.write(self.style.MIGRATE_HEADING("\n5. Seed skills"))
        call_command("seed_skills")

        self.stdout.write(self.style.MIGRATE_HEADING("\n6. Deterministic materialization"))
        call_command(
            "materialize_job_skills",
            active_only=True,
            enriched_only=True,
            force=True,
            source="llm",
            limit=max(force_llm_count, max_total),
            dry_run=not apply,
        )

        self.stdout.write(self.style.MIGRATE_HEADING("\n7. Reconcile unmatched candidates"))
        call_command("reconcile_unmatched_skill_candidates", apply=apply, dry_run=not apply)

        self.stdout.write(self.style.MIGRATE_HEADING("\n8. Zero-skill recovery"))
        call_command("recover_zero_skill_jobs", active_only=True, limit=max(force_llm_count, max_total), apply=apply, dry_run=not apply)

        self.stdout.write(self.style.MIGRATE_HEADING("\n9. Reclassification"))
        call_command("reclassify_jobs", active_only=True, limit=max(force_llm_count, max_total), apply=apply, dry_run=not apply)

        self.stdout.write(self.style.MIGRATE_HEADING("\n10. Final public safety health report"))
        
        public_zero = JobEligibilityService.filter_publicly_visible(
            NormalizedJob.objects.filter(job_skills__isnull=True)
        ).distinct().count()
        
        matchable_zero = JobEligibilityService.filter_matchable(
            NormalizedJob.objects.filter(job_skills__isnull=True)
        ).distinct().count()

        self.stdout.write(f"PUBLIC_ZERO: {public_zero}")
        self.stdout.write(f"MATCHABLE_ZERO: {matchable_zero}")

        failed_checks = []
        if apply and force_provider_call and provider_attempted_count < enrichment_count:
            failed_checks.append(
                f"LLM provider attempted count ({provider_attempted_count}) is less than selected enrichment count ({enrichment_count})"
            )
        if apply and success_count < min_llm_success:
            failed_checks.append(
                f"LLM success count ({success_count}) is less than minimum required ({min_llm_success})"
            )
        if apply and public_zero != 0:
            failed_checks.append(f"PUBLIC_ZERO is {public_zero}, expected 0")
        if apply and matchable_zero != 0:
            failed_checks.append(f"MATCHABLE_ZERO is {matchable_zero}, expected 0")

        if failed_checks:
            for failed_check in failed_checks:
                self.stdout.write(self.style.ERROR(f"FAILURE: {failed_check}"))
            self.stdout.write(self.style.ERROR("\nFAILURE: LLM E2E acceptance checks failed."))
            sys.exit(1)
        elif apply:
            self.stdout.write(self.style.SUCCESS(f"\nPASS: LLM success count ({success_count}) met the minimum required ({min_llm_success})"))
        else:
            self.stdout.write(self.style.SUCCESS("\nDry run completed successfully."))
