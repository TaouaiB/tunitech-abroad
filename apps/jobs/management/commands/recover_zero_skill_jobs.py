from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count
from apps.jobs.models import NormalizedJob, JobStatus
from apps.jobs.services.zero_skill_recovery import ZeroSkillJobRecoveryService

class Command(BaseCommand):
    help = "Recover technical skills for zero-skill jobs based on deterministic rules."

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Actually update the database. If not passed, runs in dry-run mode.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without committing changes (default if --apply is missing).',
        )
        parser.add_argument(
            '--active-only',
            action='store_true',
            help='Only process jobs with status=ACTIVE.',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=0,
            help='Limit the number of jobs processed.',
        )

    def handle(self, *args, **options):
        apply = options['apply']
        dry_run = options['dry_run']
        active_only = options['active_only']
        limit = options['limit']

        if not apply and not dry_run:
            dry_run = True

        qs = NormalizedJob.objects.annotate(skill_count=Count('job_skills')).filter(skill_count=0)
        
        if active_only:
            qs = qs.filter(status=JobStatus.ACTIVE)
            
        if limit > 0:
            # We must evaluate the queryset to a list before applying limit to avoid slicing issues in Django when using annotate
            jobs = list(qs[:limit])
        else:
            jobs = list(qs)

        self.stdout.write(f"Found {len(jobs)} jobs with zero skills to inspect.")

        with transaction.atomic():
            result = ZeroSkillJobRecoveryService.recover_queryset(jobs, dry_run=dry_run or not apply)

            if dry_run or not apply:
                transaction.set_rollback(True)
                self.stdout.write(self.style.WARNING("Dry run: Changes rolled back."))
            else:
                self.stdout.write(self.style.SUCCESS("Apply: Changes committed."))

        self.stdout.write(f"Jobs inspected: {result['jobs_inspected']}")
        self.stdout.write(f"Skipped excluded/non-IT: {result['skipped_excluded']}")
        self.stdout.write(f"Recovered jobs: {result['recovered_jobs']}")
        self.stdout.write(f"Skills created: {result['skills_created']}")
        self.stdout.write(f"Still zero-skill: {result['still_zero_skill']}")
        self.stdout.write(f"Skipped already skilled: {result['skipped_existing_skills']}")
        if result["examples"]:
            self.stdout.write("Examples:")
            for example in result["examples"]:
                self.stdout.write(f"- {example}")
