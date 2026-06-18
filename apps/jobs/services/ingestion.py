import logging
import hashlib
import time
from typing import Any
from django.utils import timezone
from django.conf import settings
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
from apps.jobs.services.broad_it_preset import get_preset_keywords, get_scheduled_keywords
from apps.llm.services.job_enrichment import (
    compute_job_enrichment_payload_hash,
    get_openrouter_circuit_status,
    job_qualifies_for_enrichment_with_reason,
)
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

        source = None
        dry_run = overrides.get("dry_run", config.dry_run)
        try:
            return cls._run_with_log(config, trigger, overrides, run_log)
        except Exception as exc:
            source = JobSource.objects.filter(slug="france_travail").first()
            cls._finalize_run(
                run_log=run_log,
                config=config,
                source=source,
                dry_run=dry_run,
                status="failed",
                error_summary=f"Unhandled ingestion error: {cls._safe_error(exc)}",
                increment_error=True,
            )
            raise

    @classmethod
    def _run_with_log(
        cls,
        config: JobIngestionConfig,
        trigger: str,
        overrides: dict[str, Any],
        run_log: JobIngestionRun,
    ):
        preset = run_log.preset
        custom_kw_override = overrides.get("custom_keywords")
        if custom_kw_override:
            # Explicit custom keywords from overrides take priority
            keywords = custom_kw_override
        elif preset and preset == "broad_it":
            keywords = get_preset_keywords(preset)
        else:
            keywords = config.custom_keywords

        # For scheduled (Beat) runs, use conservative defaults:
        # - Curated 8-keyword subset instead of full 58 keywords
        # - Lower per-keyword limit to prevent runaway API calls
        # - Fewer pages per keyword
        # This keeps a 4-hourly schedule reasonable. Full preset stays
        # available for manual syncs.
        is_scheduled = trigger == "celery"
        if is_scheduled and not custom_kw_override:
            keywords = get_scheduled_keywords()

        run_log.keywords_json = keywords
        run_log.save(update_fields=["keywords_json"])

        dry_run = overrides.get("dry_run", config.dry_run)

        limit_per_keyword = run_log.limit_per_keyword
        max_total = run_log.max_total
        max_pages_per_keyword = overrides.get("max_pages_per_keyword", config.max_pages_per_keyword)
        max_provider_requests = overrides.get(
            "max_provider_requests",
            settings.FRANCE_TRAVAIL_MAX_REQUESTS_PER_RUN,
        )
        provider_request_count = 0
        provider_cap_reached = False
        provider_warning_count = 0

        if is_scheduled and not overrides:
            limit_per_keyword = min(limit_per_keyword, 25)
            max_pages_per_keyword = min(max_pages_per_keyword, 2)
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
            if total_fetched >= max_total or provider_cap_reached:
                break

            fetched_for_kw = 0
            page = 0

            while page < max_pages_per_keyword and fetched_for_kw < limit_per_keyword and total_fetched < max_total:
                if provider_request_count >= max_provider_requests:
                    provider_cap_reached = True
                    provider_warning_count += 1
                    cls._append_warning(
                        run_log,
                        f"France Travail request cap reached after {provider_request_count} request(s); remaining pages/keywords skipped.",
                    )
                    break

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
                    if provider_request_count > 0 and settings.FRANCE_TRAVAIL_REQUEST_DELAY_SECONDS > 0:
                        time.sleep(settings.FRANCE_TRAVAIL_REQUEST_DELAY_SECONDS)
                    provider_request_count += 1
                    result = client.search_offers(params)
                except Exception as e:
                    safe_error = cls._safe_error(e)
                    if "HTTP 429" in safe_error:
                        provider_warning_count += 1
                        cls._append_warning(
                            run_log,
                            f"France Travail rate limited on keyword '{kw}' page {page}; configured backoff {settings.FRANCE_TRAVAIL_BACKOFF_ON_429_SECONDS}s.",
                        )
                        if settings.FRANCE_TRAVAIL_BACKOFF_ON_429_SECONDS > 0:
                            time.sleep(settings.FRANCE_TRAVAIL_BACKOFF_ON_429_SECONDS)
                    else:
                        run_log.error_count += 1
                        run_log.error_summary += f"Error fetching {kw} page {page}: {safe_error}\n"
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

        status = "success" if run_log.error_count == 0 and provider_warning_count == 0 else "partial_success"
        if run_log.error_count > 0 and total_fetched == 0:
            status = "failed"

        cls._finalize_run(
            run_log=run_log,
            config=config,
            source=source,
            dry_run=dry_run,
            status=status,
        )

        return run_log

    @classmethod
    def _finalize_run(
        cls,
        *,
        run_log: JobIngestionRun,
        config: JobIngestionConfig,
        source: JobSource | None,
        dry_run: bool,
        status: str,
        error_summary: str = "",
        increment_error: bool = False,
    ) -> JobIngestionRun:
        now = timezone.now()
        if increment_error:
            run_log.error_count += 1
        if error_summary:
            existing = run_log.error_summary or ""
            run_log.error_summary = f"{existing}{error_summary}\n"[:4000]
        run_log.status = status
        run_log.finished_at = now
        run_log.save()

        if dry_run:
            return run_log

        config.last_run_at = now
        update_fields = ["last_run_at"]
        if status in ["success", "partial_success"]:
            config.last_success_at = now
            config.last_error = ""
            update_fields.extend(["last_success_at", "last_error"])
            if source:
                source.last_successful_sync_at = now
                source.save(update_fields=["last_successful_sync_at"])
        else:
            config.last_error = (run_log.error_summary or "")[:1000]
            update_fields.append("last_error")
        config.save(update_fields=update_fields)
        return run_log

    @staticmethod
    def _safe_error(exc: Exception) -> str:
        return str(exc).replace("\n", " ")[:500]

    @staticmethod
    def _append_warning(run_log: JobIngestionRun, message: str) -> None:
        run_log.error_summary = f"{run_log.error_summary or ''}WARNING: {message}\n"[:4000]

    @classmethod
    def repair_france_travail_source_sync_from_runs(cls) -> bool:
        source = JobSource.objects.filter(slug="france_travail").first()
        last_success = JobIngestionRun.objects.filter(
            status__in=["success", "partial_success"],
            finished_at__isnull=False,
        ).order_by("-finished_at").first()
        if not source or not last_success:
            return False
        if source.last_successful_sync_at and source.last_successful_sync_at >= last_success.finished_at:
            return False
        source.last_successful_sync_at = last_success.finished_at
        source.save(update_fields=["last_successful_sync_at"])
        return True

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

        defaults = {
            "raw_payload_json": job_data,
            "payload_hash": payload_hash,
            "last_seen_at": now,
            "last_fetched_at": now,
        }
        try:
            raw_job = RawJobRecord.objects.get(source=source, source_job_id=job_id)
            for key, value in defaults.items():
                setattr(raw_job, key, value)
            raw_job.save(update_fields=list(defaults.keys()) + ["updated_at"])
            created = False
            run_log.updated_raw_count += 1
        except RawJobRecord.DoesNotExist:
            from django.db import IntegrityError, transaction
            try:
                with transaction.atomic():
                    raw_job = RawJobRecord.objects.create(
                        source=source,
                        source_job_id=job_id,
                        first_seen_at=now,
                        **defaults
                    )
                created = True
                run_log.created_raw_count += 1
            except IntegrityError:
                # Concurrent creation fallback
                raw_job = RawJobRecord.objects.get(source=source, source_job_id=job_id)
                for key, value in defaults.items():
                    setattr(raw_job, key, value)
                raw_job.save(update_fields=list(defaults.keys()) + ["updated_at"])
                created = False
                run_log.updated_raw_count += 1

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
                run_log.error_summary += f"Normalization error for {job_id}: {cls._safe_error(e)}\n"

    @classmethod
    def _queue_enrichment(cls, norm_job, run_log, sync_enrichment, config):
        payload_hash = compute_job_enrichment_payload_hash(norm_job)

        if get_openrouter_circuit_status()["is_open"]:
            cls._record_enrichment_skip(run_log, norm_job, "provider_circuit_open")
            JobEnrichment.objects.update_or_create(
                job=norm_job,
                defaults={
                    "payload_hash": payload_hash,
                    "status": JobEnrichment.Status.SKIPPED,
                    "status_reason": "provider_circuit_open",
                    "last_error": "",
                },
            )
            return

        enrichment_exists = JobEnrichment.objects.filter(
            job=norm_job,
            payload_hash=payload_hash,
            status__in=[
                JobEnrichment.Status.SUCCESS,
                JobEnrichment.Status.PENDING,
                JobEnrichment.Status.PROCESSING,
            ],
        ).exists()

        if enrichment_exists:
            cls._record_enrichment_skip(
                run_log,
                norm_job,
                "Successful, pending, or processing enrichment already exists for this payload hash",
            )
            return

        limit_to_use = min(
            config.enrichment_limit_per_run,
            settings.JOB_ENRICHMENT_MAX_PER_INGESTION_RUN
        )

        if run_log.enrichment_queued_count >= limit_to_use:
            cls._record_enrichment_skip(run_log, norm_job, "Run enrichment limit reached")
            return

        qualifies, reason = job_qualifies_for_enrichment_with_reason(
            norm_job,
            daily_limit=config.daily_enrichment_limit,
        )
        if not qualifies:
            cls._record_enrichment_skip(run_log, norm_job, reason)
            return

        JobEnrichment.objects.update_or_create(
            job=norm_job,
            defaults={
                "payload_hash": payload_hash,
                "status": JobEnrichment.Status.PENDING,
                "status_reason": "Queued by automated ingestion.",
            },
        )

        if sync_enrichment:
            from apps.llm.services.job_enrichment import enrich_job
            enrich_job(norm_job)
        else:
            enrich_job_task.delay(norm_job.id)

        run_log.enrichment_queued_count += 1

    @staticmethod
    def _record_enrichment_skip(run_log, norm_job, reason):
        run_log.enrichment_skipped_count += 1
