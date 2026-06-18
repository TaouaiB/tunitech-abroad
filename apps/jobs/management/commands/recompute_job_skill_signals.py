from django.core.management.base import BaseCommand, CommandError

from apps.jobs.models import JobStatus, NormalizedJob
from apps.jobs.services.it_classification import JobITClassificationService
from apps.jobs.services.skill_signals import compute_deterministic_skill_signal_quality


class Command(BaseCommand):
    help = "Recompute deterministic IT classification and skill signal quality for active jobs."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=100)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        limit = options["limit"]
        dry_run = options["dry_run"]
        if limit < 1:
            raise CommandError("--limit must be greater than zero.")

        counters = {
            "changed_to_strong": 0,
            "changed_to_partial": 0,
            "unchanged": 0,
            "skipped": 0,
        }

        jobs = (
            NormalizedJob.objects.filter(status=JobStatus.ACTIVE)
            .select_related("raw_record")
            .order_by("id")[:limit]
        )
        for job in jobs:
            raw_payload = {}
            if job.raw_record and isinstance(job.raw_record.raw_payload_json, dict):
                raw_payload = job.raw_record.raw_payload_json

            classification = JobITClassificationService.classify(
                raw_payload,
                job.description or "",
                job.title or "",
            )
            new_classification_json = {
                "family": classification.family,
                "is_it": classification.is_it,
                "confidence": classification.confidence,
                "reasons": classification.reasons,
                "negative_reasons": classification.negative_reasons,
            }
            original_classification_json = job.classification_json or {}
            job.classification_json = new_classification_json
            signal_result = compute_deterministic_skill_signal_quality(job)
            new_quality = signal_result.quality
            old_quality = job.skill_signal_quality

            if old_quality == new_quality and original_classification_json == new_classification_json:
                counters["unchanged"] += 1
                continue

            if new_quality == "strong":
                counters["changed_to_strong"] += 1
            elif new_quality == "partial":
                counters["changed_to_partial"] += 1
            else:
                counters["skipped"] += 1

            if not dry_run:
                NormalizedJob.objects.filter(id=job.id).update(
                    classification_json=new_classification_json,
                    skill_signal_quality=new_quality,
                )

        for key in ["changed_to_strong", "changed_to_partial", "unchanged", "skipped"]:
            self.stdout.write(f"{key}: {counters[key]}")
        if dry_run:
            self.stdout.write(self.style.SUCCESS("[DRY-RUN] no changes written"))
