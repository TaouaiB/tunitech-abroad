from django.core.management.base import BaseCommand, CommandError
from apps.jobs.services.france_travail.client import FranceTravailClient
from apps.jobs.models import JobSource, RawJobRecord, NormalizedJob
from django.utils import timezone
from apps.jobs.services.normalization import JobNormalizationService

class Command(BaseCommand):
    help = 'Safely sync jobs from France Travail for testing/stabilization'

    def add_arguments(self, parser):
        parser.add_argument('--keyword', type=str, default='django', help='Keyword to search for')
        parser.add_argument('--limit', type=int, default=5, help='Maximum number of jobs to fetch')
        parser.add_argument('--normalize', action='store_true', help='Normalize fetched jobs immediately')

    def handle(self, *args, **options):
        keyword = options['keyword']
        limit = options['limit']
        normalize = options['normalize']
        keywords_to_try = [keyword, 'developpeur', 'informatique', 'python', 'django']
        jobs = []
        actual_limit = limit
        client = FranceTravailClient()

        for kw in keywords_to_try:
            self.stdout.write(f"Starting safe sync for '{kw}' with limit {actual_limit}...")
            try:
                result = client.search_offers({'motsCles': kw, 'range': f'0-{actual_limit-1}'})
                jobs = result.get('resultats', [])
                if jobs:
                    self.stdout.write(self.style.SUCCESS(f"Found {len(jobs)} jobs for keyword '{kw}'."))
                    break
            except Exception as e:
                raise CommandError(f"BLOCKED: {e.__class__.__name__} - {str(e)}")
        
        if not jobs:
            self.stdout.write(self.style.WARNING("No jobs returned by API for any keyword."))
            return

        jobs = jobs[:actual_limit]
        self.stdout.write("Diagnostics: no credentials or tokens printed.")

        source, _ = JobSource.objects.get_or_create(
            name='France Travail',
            defaults={
                'slug': 'france_travail',
                'is_active': True,
                'scraper_config': {},
                'priority': 1
            }
        )

        saved_raw = 0
        updated_raw = 0
        normalized_count = 0
        normalization_failures = 0
        fetched_count = len(jobs)

        for job_data in jobs:
            job_id = job_data.get('id', str(hash(str(job_data))))
            
            import hashlib
            raw_job, created = RawJobRecord.objects.update_or_create(
                source=source,
                source_job_id=job_id,
                defaults={
                    'raw_payload_json': job_data,
                    'payload_hash': hashlib.sha256(str(job_data).encode()).hexdigest(),
                    'first_seen_at': timezone.now(),
                    'last_seen_at': timezone.now(),
                    'last_fetched_at': timezone.now()
                }
            )
            if created:
                saved_raw += 1
            else:
                updated_raw += 1

            if normalize:
                try:
                    norm_job = JobNormalizationService.normalize(raw_job)
                    if norm_job:
                        normalized_count += 1
                    else:
                        normalization_failures += 1
                        self.stdout.write(self.style.ERROR(f"Normalization failed for {job_id} (returned None)"))
                except Exception as e:
                    normalization_failures += 1
                    self.stdout.write(self.style.ERROR(f"Normalization error for {job_id}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"Fetched: {fetched_count}"))
        self.stdout.write(self.style.SUCCESS(f"Saved (Raw): {saved_raw}"))
        self.stdout.write(self.style.SUCCESS(f"Updated (Raw): {updated_raw}"))
        if normalize:
            self.stdout.write(self.style.SUCCESS(f"Normalized (New/Updated): {normalized_count}"))
            if normalization_failures > 0:
                raise CommandError(f"{normalization_failures} jobs failed normalization.")
