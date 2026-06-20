import csv
import json
import os
from django.core.management.base import BaseCommand
from django.db.models import Count
from django.urls import reverse
from apps.jobs.models import NormalizedJob, JobStatus


FIELDNAMES = [
    "job_id",
    "public_id",
    "title",
    "company",
    "location",
    "status",
    "source",
    "source_external_id",
    "skill_signal_quality",
    "skill_extraction_status",
    "job_skill_count",
    "enrichment_status",
    "enrichment_required_count",
    "enrichment_optional_count",
    "description_excerpt",
    "job_path",
]


def _enrichment_skill_counts(enrichment):
    if not enrichment or not isinstance(enrichment.validated_output_json, dict):
        return 0, 0
    required = enrichment.validated_output_json.get("required_skills", [])
    optional = enrichment.validated_output_json.get("optional_skills", [])
    return (
        len(required) if isinstance(required, list) else 0,
        len(optional) if isinstance(optional, list) else 0,
    )


def _build_record(job):
    enrichment = getattr(job, "enrichment", None)
    required_count, optional_count = _enrichment_skill_counts(enrichment)
    return {
        "job_id": job.id,
        "public_id": str(job.public_id),
        "title": job.title,
        "company": job.company_name,
        "location": job.location,
        "status": job.status,
        "source": job.source.slug,
        "source_external_id": job.source_job_id,
        "skill_signal_quality": job.skill_signal_quality,
        "skill_extraction_status": job.skill_extraction_status,
        "job_skill_count": getattr(job, "skill_count", 0),
        "enrichment_status": enrichment.status if enrichment else "",
        "enrichment_required_count": required_count,
        "enrichment_optional_count": optional_count,
        "description_excerpt": (job.description or "")[:300].replace("\n", " "),
        "job_path": reverse("jobs:detail", args=[job.public_id]),
    }


class Command(BaseCommand):
    help = 'Export jobs that have zero materialized skills for manual review'

    def add_arguments(self, parser):
        parser.add_argument(
            '--active-only',
            action='store_true',
            help='Only export jobs with status active',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=0,
            help='Limit the number of rows exported',
        )
        parser.add_argument(
            '--format',
            type=str,
            choices=['csv', 'jsonl'],
            default='csv',
            help='Output format (csv or jsonl)',
        )

    def handle(self, *args, **options):
        active_only = options['active_only']
        limit = options['limit']
        fmt = options['format']

        qs = (
            NormalizedJob.objects.select_related("source", "enrichment")
            .annotate(skill_count=Count("job_skills"))
            .filter(skill_count=0)
        )
        
        if active_only:
            qs = qs.filter(status=JobStatus.ACTIVE)
            
        qs = qs.order_by('-first_seen_at')

        if limit > 0:
            qs = qs[:limit]

        os.makedirs('var/review', exist_ok=True)
        filename = f'var/review/jobs_needing_skill_review.{fmt}'

        count = 0
        with open(filename, 'w', encoding='utf-8') as f:
            if fmt == 'csv':
                writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
                writer.writeheader()
                for job in qs:
                    writer.writerow(_build_record(job))
                    count += 1
            elif fmt == 'jsonl':
                for job in qs:
                    f.write(json.dumps(_build_record(job), ensure_ascii=False) + '\n')
                    count += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully exported {count} jobs to {filename}'))
