import logging
import hashlib
from typing import Any, cast
from django.utils import timezone
from apps.jobs.models import (
    JobIngestionConfig,
    JobIngestionRun,
    JobSource,
    SourceType,
    RawJobRecord,
    NormalizedJob,
)
from apps.jobs.services.france_travail.client import FranceTravailClient
from apps.jobs.services.normalization import JobNormalizationService
from apps.jobs.services.broad_it_preset import get_preset_keywords
from apps.llm.services.job_enrichment import job_qualifies_for_enrichment_with_reason
from apps.llm.models import JobEnrichment
from apps.llm.tasks import enrich_job_task

logger = logging.getLogger(__name__)

class JobIngestionService:
    @classmethod
    def run(cls, config: JobIngestionConfig, trigger: str, overrides: dict[str, Any] | None = None):
        if overrides is None:
            overrides = {}

        run_log = JobIngestionRun.objects.create(
            config=config,
            trigger=trigger,
            status="running",
            preset=overrides.get("preset", config.preset),
            limit_per_keyword=overrides.get("limit_per_keyword", config.limit_per_keyword),
            max_total=overrides.get("max_total", config.max_total_per_run),
        )

        preset = run_log.preset
        keywords = overrides.get("custom_keywords") or config.custom_keywords
        if preset and preset == "broad_it":
            keywords = get_preset_keywords(preset)
        
        run_log.keywords_json = keywords
        run_log.save(update_fields=["keywords_json"])

        dry_run = overrides.get("dry_run", config.dry_run)
        
        limit_per_keyword = run_log.limit_per_keyword
        max_total = run_log.max_total
        max_pages_per_keyword = overrides.get("max_pages_per_keyword", config.max_pages_per_keyword)
        normalize = overrides.get("normalize", config.normalize_after_fetch)
        enrichment_enabled = overrides.get("enrichment_enabled", config.enrichment_enabled)
        enrich_every_fetched_it_job = overrides.get(
            "enrich_every_fetched_it_job",
            config.enrich_every_fetched_it_job,
        )
        sync_enrichment = overrides.get("sync_enrichment", False)
        
        client = FranceTravailClient()

        source, _ = JobSource.objects.get_or_create(
            slug="france_travail",
            defaults={
                "name": "France Travail",
                "base_url": "https://candidat.francetravail.fr/offres/recherche",
                "source_type": SourceType.API,
                "is_active": True,
            },
        )

        seen_source_ids: set[str] = set()
        total_fetched = 0
        page_size = min(limit_per_keyword, 50)  # FT API limit is 150, but let's use up to 50
        
        for kw in keywords:
            if total_fetched >= max_total:
                break
                
            fetched_for_kw = 0
            page = 0
            
            while page < max_pages_per_keyword and fetched_for_kw < limit_per_keyword and total_fetched < max_total:
                start = page * page_size
                end = start + page_size - 1
                
                # Adjust end if it exceeds limits
                remaining_for_kw = limit_per_keyword - fetched_for_kw
                remaining_total = max_total - total_fetched
                max_allowed_this_page = min(page_size, remaining_for_kw, remaining_total)
                
                if max_allowed_this_page <= 0:
                    break
                    
                end = start + max_allowed_this_page - 1

                try:
                    params = {"motsCles": kw, "range": f"{start}-{end}"}
                    result = client.search_offers(params)
                except Exception as e:
                    run_log.error_count += 1
                    run_log.error_summary += f"Error fetching {kw} page {page}: {str(e)}\n"
                    break # Skip to next keyword on error
                
                jobs = result.get("resultats", [])
                if not jobs:
                    break # No more results for this keyword

                for job_data in jobs:
                    if total_fetched >= max_total or fetched_for_kw >= limit_per_keyword:
                        break
                        
                    job_id = job_data.get("id")
                    if not job_id:
                        continue
                        
                    if job_id in seen_source_ids:
                        run_log.duplicates_skipped_count += 1
                        continue
                        
                    seen_source_ids.add(job_id)
                    total_fetched += 1
                    fetched_for_kw += 1

                    if not dry_run:
                        cls._process_job(
                            job_data,
                            job_id,
                            source,
                            run_log,
                            normalize,
                            enrichment_enabled,
                            enrich_every_fetched_it_job,
                            sync_enrichment,
                            config,
                        )
                    else:
                        run_log.fetched_count += 1

                if len(jobs) < max_allowed_this_page:
                    break # Last page
                    
                page += 1

        run_log.status = "success" if run_log.error_count == 0 else "partial_success"
        if run_log.error_count > 0 and total_fetched == 0:
            run_log.status = "failed"
            
        run_log.finished_at = timezone.now()
        run_log.save()
        
        if not dry_run:
            config.last_run_at = timezone.now()
            if run_log.status in ["success", "partial_success"]:
                config.last_success_at = timezone.now()
            config.save(update_fields=["last_run_at", "last_success_at"])
            
        return run_log

    @classmethod
    def _process_job(
        cls,
        job_data,
        job_id,
        source,
        run_log,
        normalize,
        enrichment_enabled,
        enrich_every_fetched_it_job,
        sync_enrichment,
        config,
    ):
        run_log.fetched_count += 1
        now = timezone.now()
        payload_hash = hashlib.sha256(str(job_data).encode()).hexdigest()
        
        try:
            raw_job = RawJobRecord.objects.get(source=source, source_job_id=job_id)
            raw_job.raw_payload_json = job_data
            raw_job.payload_hash = payload_hash
            raw_job.last_seen_at = now
            raw_job.last_fetched_at = now
            raw_job.save(update_fields=["raw_payload_json", "payload_hash", "last_seen_at", "last_fetched_at", "updated_at"])
            created = False
            run_log.updated_raw_count += 1
        except RawJobRecord.DoesNotExist:
            raw_job = RawJobRecord.objects.create(
                source=source,
                source_job_id=job_id,
                raw_payload_json=job_data,
                payload_hash=payload_hash,
                first_seen_at=now,
                last_seen_at=now,
                last_fetched_at=now,
            )
            created = True
            run_log.created_raw_count += 1
            
        if normalize:
            try:
                norm_job = JobNormalizationService.normalize(raw_job)
                if norm_job:
                    run_log.normalized_count += 1
                    if enrichment_enabled and enrich_every_fetched_it_job:
                        cls._queue_enrichment(norm_job, run_log, sync_enrichment, config)
                    elif enrichment_enabled:
                        cls._record_enrichment_skip(
                            run_log,
                            norm_job,
                            "enrich_every_fetched_it_job is False",
                        )
            except Exception as e:
                run_log.error_count += 1
                run_log.error_summary += f"Normalization error for {job_id}: {str(e)}\n"

    @classmethod
    def _queue_enrichment(cls, norm_job, run_log, sync_enrichment, config):
        qualifies, reason = job_qualifies_for_enrichment_with_reason(norm_job)
        if not qualifies:
            cls._record_enrichment_skip(run_log, norm_job, reason)
            return

        payload_hash = hashlib.md5(f"{norm_job.title}\n{norm_job.description}".encode('utf-8')).hexdigest()
        
        # Check for existing enrichment
        enrichment_exists = JobEnrichment.objects.filter(
            job=norm_job,
            payload_hash=payload_hash,
            status__in=[JobEnrichment.Status.SUCCESS, JobEnrichment.Status.PENDING, JobEnrichment.Status.PROCESSING]
        ).exists()
        
        if enrichment_exists:
            cls._record_enrichment_skip(
                run_log,
                norm_job,
                "Successful, pending, or processing enrichment already exists for this payload hash",
            )
            return
            
        # Check run limits
        if run_log.enrichment_queued_count >= config.enrichment_limit_per_run:
            cls._record_enrichment_skip(run_log, norm_job, "Run enrichment limit reached")
            return
            
        if sync_enrichment:
            from apps.llm.services.job_enrichment import enrich_job
            enrich_job(norm_job)
        else:
            cast(Any, enrich_job_task.delay)(norm_job.id)
            
        run_log.enrichment_queued_count += 1

    @staticmethod
    def _record_enrichment_skip(run_log, norm_job, reason):
        run_log.enrichment_skipped_count += 1
        run_log.error_summary += f"Enrichment skipped for {norm_job.source_job_id}: {reason}\n"
