import json
from django.core.management.base import BaseCommand
from django.db.models import QuerySet

from apps.jobs.models import NormalizedJob, JobStatus
from apps.jobs.services.it_classification import JobITClassificationService
from apps.jobs.services.skill_signals import compute_deterministic_skill_signal_quality
from apps.jobs.services.eligibility import JobEligibilityService, PublicJobState

class Command(BaseCommand):
    help = "Reclassify existing jobs and recompute their skill signals and eligibility"

    def add_arguments(self, parser):
        parser.add_argument("--active-only", action="store_true", help="Only process active jobs")
        parser.add_argument("--dry-run", action="store_true", help="Do not save changes to DB")
        parser.add_argument("--apply", action="store_true", help="Apply changes to DB")
        parser.add_argument("--limit", type=int, default=0, help="Limit number of jobs to process")

    def handle(self, *args, **options):
        active_only = options["active_only"]
        dry_run = options["dry_run"]
        apply = options["apply"]
        limit = options["limit"]

        if dry_run == apply:
            self.stderr.write("Specify exactly one of --dry-run or --apply")
            return

        qs = NormalizedJob.objects.select_related("raw_record").all()
        if active_only:
            qs = qs.filter(status=JobStatus.ACTIVE)

        if limit > 0:
            qs = qs[:limit]

        total_processed = 0
        
        excluded_before = 0
        excluded_after = 0
        
        visible_before = 0
        visible_after = 0
        matchable_after = 0
        admin_review_after = 0
        zero_skill_public_visible_after = 0
        
        changed_to_it = []
        changed_to_excluded = []
        
        for job in qs:
            total_processed += 1
            
            old_signal = job.skill_signal_quality
            
            was_excluded = (old_signal == "excluded_non_it")
            was_visible = JobEligibilityService.is_publicly_visible(job)
            
            if was_excluded:
                excluded_before += 1
            if was_visible:
                visible_before += 1
                
            raw_payload = {}
            if hasattr(job, "raw_record") and job.raw_record and isinstance(job.raw_record.raw_payload_json, dict):
                raw_payload = job.raw_record.raw_payload_json
                
            class_res = JobITClassificationService.classify(raw_payload, job.description, job.title)
            
            new_classification = {
                "family": class_res.family,
                "is_it": class_res.is_it,
                "confidence": class_res.confidence,
                "reasons": class_res.reasons,
                "negative_reasons": class_res.negative_reasons,
            }
            
            # Temporary set for signal computation
            job.classification_json = new_classification
            
            signal_res = compute_deterministic_skill_signal_quality(job)
            new_signal = signal_res.quality
            
            job.skill_signal_quality = new_signal
            
            is_excluded = (new_signal == "excluded_non_it")
            new_state = JobEligibilityService.classify_public_state(job)
            is_visible = new_state in (
                PublicJobState.PUBLIC_MATCHABLE,
                PublicJobState.PUBLIC_LIMITED_PENDING_ANALYSIS,
            )
            
            if is_excluded:
                excluded_after += 1
            if is_visible:
                visible_after += 1
            if new_state == PublicJobState.PUBLIC_MATCHABLE:
                matchable_after += 1
            if new_state == PublicJobState.ADMIN_REVIEW_ONLY:
                admin_review_after += 1
            if is_visible and not job.job_skills.exists():
                zero_skill_public_visible_after += 1
                
            if was_excluded and not is_excluded:
                changed_to_it.append(f"{job.source_job_id}: {job.title} ({old_signal} -> {new_signal}, {class_res.family})")
            elif was_visible and not is_visible:
                changed_to_excluded.append(f"{job.source_job_id}: {job.title} (visible -> not visible, {class_res.family}, {new_signal})")

            if apply:
                # we already set job.classification_json and job.skill_signal_quality
                job.save(update_fields=["classification_json", "skill_signal_quality"])

        self.stdout.write(self.style.SUCCESS(f"Processed {total_processed} jobs"))
        self.stdout.write(f"Excluded: {excluded_before} -> {excluded_after}")
        self.stdout.write(f"Visible: {visible_before} -> {visible_after}")
        self.stdout.write(f"Matchable after: {matchable_after}")
        self.stdout.write(f"Admin review only after: {admin_review_after}")
        self.stdout.write(f"Zero-skill public visible after: {zero_skill_public_visible_after}")
        
        if changed_to_it:
            self.stdout.write(self.style.WARNING("\nJobs changed from excluded -> IT:"))
            for item in changed_to_it[:20]:
                self.stdout.write(f"  - {item}")
            if len(changed_to_it) > 20:
                self.stdout.write(f"  ... and {len(changed_to_it) - 20} more")
                
        if changed_to_excluded:
            self.stdout.write(self.style.WARNING("\nJobs changed from visible -> excluded/admin_review:"))
            for item in changed_to_excluded[:20]:
                self.stdout.write(f"  - {item}")
            if len(changed_to_excluded) > 20:
                self.stdout.write(f"  ... and {len(changed_to_excluded) - 20} more")
