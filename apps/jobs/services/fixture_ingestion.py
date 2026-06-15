import json
from typing import Any, cast

from django.utils import timezone
from apps.jobs.models import (
    JobSource,
    IngestionRun,
    IngestionRunStatus,
    TriggerType,
    RawJobRecord,
    NormalizationStatus,
)
from apps.jobs.services.helpers import compute_payload_hash


class JobFixtureIngestionService:
    @staticmethod
    def load_fixture_file(path: str, source_slug: str = "france_travail") -> IngestionRun:
        source = JobSource.objects.get(slug=source_slug)
        now = timezone.now()
        
        run = IngestionRun.objects.create(
            source=source,
            status=IngestionRunStatus.RUNNING,
            trigger_type=TriggerType.STARTUP_FIXTURE,
            started_at=now,
        )

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, dict) and "resultats" in data:
                jobs = data["resultats"]
            elif isinstance(data, list):
                jobs = data
            else:
                jobs = []

            run.fetched_count = len(jobs)
            run.save(update_fields=["fetched_count"])

            for job_payload in jobs:
                source_job_id = job_payload.get("id")
                if not source_job_id:
                    run.error_count += 1
                    continue
                
                payload_hash = compute_payload_hash(job_payload)

                try:
                    raw_record = RawJobRecord.objects.get(source=source, source_job_id=source_job_id)
                    
                    if raw_record.payload_hash == payload_hash:
                        run.unchanged_count += 1
                        raw_record.last_seen_at = now
                        raw_record.last_fetched_at = now
                        raw_record.ingestion_run = run
                        raw_record.save(update_fields=["last_seen_at", "last_fetched_at", "ingestion_run"])
                    else:
                        raw_record.raw_payload_json = job_payload
                        raw_record.payload_hash = payload_hash
                        raw_record.last_seen_at = now
                        raw_record.last_fetched_at = now
                        raw_record.normalization_status = NormalizationStatus.PENDING
                        raw_record.ingestion_run = run
                        raw_record.save()
                        run.updated_count += 1
                        
                except RawJobRecord.DoesNotExist:
                    RawJobRecord.objects.create(
                        source=source,
                        source_job_id=source_job_id,
                        raw_payload_json=job_payload,
                        payload_hash=payload_hash,
                        first_seen_at=now,
                        last_seen_at=now,
                        last_fetched_at=now,
                        normalization_status=NormalizationStatus.PENDING,
                        ingestion_run=run,
                    )
                    run.created_count += 1

            run.status = IngestionRunStatus.SUCCESS
            
        except Exception as e:
            run.status = IngestionRunStatus.FAILED
            run.error_message = str(e)
            
        finally:
            run.finished_at = timezone.now()
            run.save()

        return run

    @staticmethod
    def ingest_fixture_and_dispatch_normalization(path: str, source_slug: str = "france_travail") -> str:
        from apps.jobs.tasks import normalize_raw_job_record

        run = JobFixtureIngestionService.load_fixture_file(path, source_slug=source_slug)

        if run.status == IngestionRunStatus.SUCCESS:
            pending_record_ids = RawJobRecord.objects.filter(
                ingestion_run=run,
                normalization_status=NormalizationStatus.PENDING,
            ).values_list("id", flat=True)

            for record_id in pending_record_ids:
                # Celery task proxy exposes delay() at runtime; cast keeps Pyright clean.
                cast(Any, normalize_raw_job_record).delay(record_id)

        return f"Fixture ingestion complete: {run.status}. Fetched {run.fetched_count}."
