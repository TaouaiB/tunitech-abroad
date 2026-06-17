from django.core.management.base import BaseCommand
from apps.jobs.models import JobIngestionConfig
from apps.jobs.services.ingestion import JobIngestionService
from apps.jobs.services.expiry import JobExpiryService

class Command(BaseCommand):
    help = 'Automatically sync broad IT jobs from France Travail'

    def add_arguments(self, parser):
        parser.add_argument('--config', type=str, default='default', help='Config name in DB')
        parser.add_argument('--preset', type=str, help='Keyword preset (e.g. broad_it)')
        parser.add_argument('--limit-per-keyword', type=int, help='Limit fetched jobs per keyword')
        parser.add_argument('--max-total', type=int, help='Max total jobs to fetch in this run')
        parser.add_argument('--max-pages-per-keyword', type=int, help='Max pages to paginate per keyword')
        parser.add_argument('--normalize', action='store_true', help='Enable normalization after fetch')
        parser.add_argument('--enqueue-enrichment', action='store_true', help='Enable queuing enrichment')
        parser.add_argument('--no-enrichment', action='store_true', help='Disable queuing enrichment')
        parser.add_argument('--expire-stale', action='store_true', help='Run stale job expiry after sync')
        parser.add_argument('--dry-run', action='store_true', help='Do not save to database')
        parser.add_argument('--sync-enrichment', action='store_true', help='Run enrichment synchronously (only for local testing)')

    def handle(self, *args, **options):
        config_name = options['config']
        config, _ = JobIngestionConfig.objects.get_or_create(
            name=config_name,
            defaults={
                'enabled': True,
                'preset': 'broad_it',
                'limit_per_keyword': 50,
                'max_total_per_run': 1000,
                'enrichment_enabled': True,
            }
        )

        overrides = {}
        if options['preset']:
            overrides['preset'] = options['preset']
        if options['limit_per_keyword'] is not None:
            overrides['limit_per_keyword'] = options['limit_per_keyword']
        if options['max_total'] is not None:
            overrides['max_total'] = options['max_total']
        if options['max_pages_per_keyword'] is not None:
            overrides['max_pages_per_keyword'] = options['max_pages_per_keyword']
            
        if options['normalize']:
            overrides['normalize'] = True
            
        if options['enqueue_enrichment']:
            overrides['enrichment_enabled'] = True
            overrides['enrich_every_fetched_it_job'] = True
        elif options['no_enrichment']:
            overrides['enrichment_enabled'] = False
            
        if options['dry_run']:
            overrides['dry_run'] = True
            
        if options['sync_enrichment']:
            overrides['sync_enrichment'] = True

        self.stdout.write(f"Starting ingestion with config: {config_name}")
        self.stdout.write(f"Overrides: {overrides}")

        run_log = JobIngestionService.run(config, trigger="command", overrides=overrides)

        self.stdout.write(self.style.SUCCESS(f"Ingestion finished with status: {run_log.status}"))
        self.stdout.write(f"Fetched: {run_log.fetched_count}")
        self.stdout.write(f"Created raw: {run_log.created_raw_count}")
        self.stdout.write(f"Updated raw: {run_log.updated_raw_count}")
        self.stdout.write(f"Normalized: {run_log.normalized_count}")
        self.stdout.write(f"Duplicates skipped: {run_log.duplicates_skipped_count}")
        self.stdout.write(f"Enrichment queued: {run_log.enrichment_queued_count}")
        self.stdout.write(f"Enrichment skipped: {run_log.enrichment_skipped_count}")
        self.stdout.write(f"Errors: {run_log.error_count}")
        
        if run_log.error_summary:
            self.stdout.write(self.style.WARNING(f"Error summary:\n{run_log.error_summary}"))

        if options['expire_stale']:
            self.stdout.write("Running stale job expiry...")
            if not overrides.get('dry_run'):
                expired_count = JobExpiryService.mark_stale_jobs(config.expire_after_days)
                self.stdout.write(self.style.SUCCESS(f"Marked {expired_count} jobs as stale."))
                run_log.expired_count = expired_count
                run_log.save(update_fields=['expired_count'])
            else:
                self.stdout.write("Skipping expiry due to dry-run.")
