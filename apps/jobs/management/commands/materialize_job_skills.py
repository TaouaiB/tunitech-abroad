from django.core.management.base import BaseCommand
from django.db.models import Q
from apps.jobs.models import NormalizedJob, SkillExtractionStatus
from apps.llm.models import JobEnrichment
from apps.jobs.services.skill_materialization import JobSkillMaterializationService
from apps.jobs.services.skill_extraction import JobSkillExtractionService

class Command(BaseCommand):
    help = 'Backfill missing canonical skills for jobs via materialization pipeline'

    def add_arguments(self, parser):
        parser.add_argument('--active-only', action='store_true', help='Only process active jobs')
        parser.add_argument('--status', nargs='+', type=str, help='Filter by specific statuses (e.g., active stale removed)')
        parser.add_argument('--limit', type=int, default=200, help='Max number of jobs to process')
        parser.add_argument('--dry-run', action='store_true', help='Do not actually materialize or save anything')
        parser.add_argument('--enriched-only', action='store_true', help='Only process jobs with successful enrichment')
        parser.add_argument('--pending-only', action='store_true', help='Only process jobs stuck in pending extraction status')
        parser.add_argument('--force', action='store_true', help='Force materialization even if skills already exist')
        parser.add_argument('--source', type=str, choices=['rule', 'llm', 'both'], default='both', help='Which source to prefer/use')

    def handle(self, *args, **options):
        active_only = options['active_only']
        statuses = options['status']
        limit = options['limit']
        dry_run = options['dry_run']
        enriched_only = options['enriched_only']
        pending_only = options['pending_only']
        force = options['force']
        source_opt = options['source']

        qs = NormalizedJob.objects.all().select_related('enrichment')

        if active_only:
            qs = qs.filter(status='active')
        elif statuses:
            qs = qs.filter(status__in=statuses)

        filters = Q()

        if pending_only:
            filters &= Q(skill_extraction_status=SkillExtractionStatus.PENDING)
        
        if enriched_only:
            filters &= Q(enrichment__status=JobEnrichment.Status.SUCCESS)

        if not force:
            # We want to process jobs that:
            # 1. Are pending extraction OR
            # 2. Have successful enrichment but no skills OR
            # 3. Have raw required/optional skills JSON but no canonical skills
            needs_skills = Q(job_skills__isnull=True)
            has_raw = ~Q(required_skills_json=[]) | ~Q(optional_skills_json=[])
            has_enrichment = Q(enrichment__status=JobEnrichment.Status.SUCCESS)
            
            missing_skills_condition = needs_skills & (has_raw | has_enrichment | Q(skill_extraction_status=SkillExtractionStatus.PENDING))
            filters &= missing_skills_condition

        qs = qs.filter(filters).distinct()[:limit]

        self.stdout.write(f"Found {qs.count()} jobs matching criteria.")

        if dry_run:
            self.stdout.write("DRY RUN: Exiting without materialization.")
            return

        processed = 0
        materialized_success = 0
        no_skill_candidates = 0
        failed = 0

        created_skills_total = 0
        unmatched_candidates_total = 0

        for job in qs:
            processed += 1
            enrichment = getattr(job, 'enrichment', None)
            
            source_to_use = 'rule'
            if source_opt in ('llm', 'both') and enrichment and enrichment.status == JobEnrichment.Status.SUCCESS:
                source_to_use = 'llm'

            try:
                if source_to_use == 'llm':
                    result = JobSkillMaterializationService.materialize_for_job(job, source='llm', enrichment=enrichment)
                else:
                    # Use existing extraction wrapper to respect rules like "generic FT labels"
                    result = JobSkillExtractionService.extract_for_job(job)
                
                # Check status via job
                job.refresh_from_db()
                if job.skill_extraction_status == SkillExtractionStatus.SUCCESS:
                    materialized_success += 1
                    # Result from materializer could be used if returned directly
                    if hasattr(result, 'created_count'):
                        created_skills_total += result.created_count
                        unmatched_candidates_total += result.unmatched_count
                elif job.skill_extraction_status == SkillExtractionStatus.NOT_ENOUGH_TEXT:
                    no_skill_candidates += 1
                else:
                    failed += 1
            except Exception as e:
                failed += 1
                self.stderr.write(f"Error materializing job {job.id}: {e}")

        self.stdout.write(self.style.SUCCESS(f"Finished processing {processed} jobs."))
        self.stdout.write(f"Success: {materialized_success}")
        self.stdout.write(f"No skill candidates: {no_skill_candidates}")
        self.stdout.write(f"Failed: {failed}")
        self.stdout.write(f"Skills created (if tracked): {created_skills_total}")
        self.stdout.write(f"Unmatched candidates (if tracked): {unmatched_candidates_total}")
