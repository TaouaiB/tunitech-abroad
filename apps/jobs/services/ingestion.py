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
    JobIngestionQueryRun,
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
            max_total=overrides.get("max_total", min(config.max_jobs_per_run, config.max_total_per_run)),
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
            keywords = custom_kw_override
        elif cls._is_scheduled_trigger(trigger) and config.queries_json:
            keywords = config.queries_json
        elif cls._is_scheduled_trigger(trigger):
            keywords = get_scheduled_keywords()
        elif preset and preset == "broad_it":
            keywords = get_preset_keywords(preset)
        else:
            keywords = config.queries_json or config.custom_keywords

        is_scheduled = cls._is_scheduled_trigger(trigger)

        run_log.keywords_json = keywords
        run_log.save(update_fields=["keywords_json"])

        dry_run = overrides.get("dry_run", config.dry_run)

        limit_per_keyword = run_log.limit_per_keyword
        max_total = run_log.max_total
        max_pages_per_keyword = overrides.get("max_pages_per_query", config.max_pages_per_query)
        max_provider_requests = overrides.get(
            "max_provider_requests",
            settings.FRANCE_TRAVAIL_MAX_REQUESTS_PER_RUN,
        )
        run_log.config_snapshot_json = cls._build_config_snapshot(
            config=config,
            trigger=trigger,
            preset=preset,
            keywords=keywords,
            limit_per_keyword=limit_per_keyword,
            max_total=max_total,
            max_provider_requests=max_provider_requests,
            max_pages_per_keyword=max_pages_per_keyword,
            page_size=config.page_size if hasattr(config, "page_size") else 50,
        )
        run_log.save(update_fields=["config_snapshot_json"])
        provider_request_count = 0
        provider_cap_reached = False
        provider_warning_count = 0

        if is_scheduled and not overrides:
            max_total = min(config.target_daily_fetch_count, config.max_jobs_per_run, config.max_total_per_run)
            run_log.max_total = max_total
            run_log.config_snapshot_json["max_total_per_run"] = max_total
            run_log.config_snapshot_json["target_daily_fetch_count"] = config.target_daily_fetch_count
            run_log.config_snapshot_json["max_jobs_per_run"] = config.max_jobs_per_run
            run_log.save(update_fields=["max_total", "config_snapshot_json"])
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
        page_size = min(limit_per_keyword, config.page_size if hasattr(config, 'page_size') else 50)  # FT API limit is 150, but let's use up to page_size

        query_stats = run_log.query_stats_json or {}

        for kw in keywords:
            if total_fetched >= max_total or provider_cap_reached:
                break

            fetched_for_kw = 0
            page = 0
            query_started_at = timezone.now()
            query_error_message = ""
            requested_ranges = []

            # Snapshots for query tracking
            kw_start_fetched = run_log.fetched_count
            kw_start_created = run_log.created_raw_count
            kw_start_updated = run_log.updated_raw_count
            kw_start_skipped = run_log.duplicates_skipped_count
            kw_start_error = run_log.error_count
            kw_unchanged = 0

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

                params = {"motsCles": kw, "range": f"{start}-{end}"}
                requested_ranges.append(params["range"])

                try:
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
                        query_error_message = safe_error
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
                        process_result = cls._process_job(
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
                        if process_result == "unchanged":
                            kw_unchanged += 1
                    else:
                        run_log.fetched_count += 1

                if len(jobs) < max_allowed_this_page:
                    break # Last page

                page += 1

            query_stats[kw] = {
                "fetched": run_log.fetched_count - kw_start_fetched,
                "created": run_log.created_raw_count - kw_start_created,
                "updated": run_log.updated_raw_count - kw_start_updated,
                "unchanged": kw_unchanged,
                "skipped": run_log.duplicates_skipped_count - kw_start_skipped,
                "error": run_log.error_count - kw_start_error,
                "params": {"motsCles": kw},
                "requested_ranges": requested_ranges,
            }
            JobIngestionQueryRun.objects.create(
                ingestion_run=run_log,
                query_label=kw,
                params_json={"motsCles": kw},
                requested_range_json={"ranges": requested_ranges},
                fetched_count=run_log.fetched_count - kw_start_fetched,
                created_count=run_log.created_raw_count - kw_start_created,
                updated_count=run_log.updated_raw_count - kw_start_updated,
                unchanged_count=kw_unchanged,
                skipped_count=run_log.duplicates_skipped_count - kw_start_skipped,
                error_count=run_log.error_count - kw_start_error,
                error_message=query_error_message,
                started_at=query_started_at,
                finished_at=timezone.now(),
            )
            # Save query stats progressively
            run_log.query_stats_json = query_stats
            run_log.save(update_fields=["query_stats_json"])

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

    @staticmethod
    def _is_scheduled_trigger(trigger: str) -> bool:
        return trigger in {"celery", "scheduled"}

    @staticmethod
    def _build_config_snapshot(
        *,
        config: JobIngestionConfig,
        trigger: str,
        preset: str,
        keywords: list[str],
        limit_per_keyword: int,
        max_total: int,
        max_provider_requests: int,
        max_pages_per_keyword: int,
        page_size: int,
    ) -> dict[str, Any]:
        return {
            "config_id": config.id,
            "config_name": config.name,
            "trigger": trigger,
            "preset": preset,
            "queries_count": len(keywords),
            "keywords_count": len(keywords),
            "queries": list(keywords),
            "keywords": list(keywords),
            "target_daily_fetch_count": config.target_daily_fetch_count,
            "max_jobs_per_run": config.max_jobs_per_run,
            "max_total_per_run": max_total,
            "limit_per_keyword": limit_per_keyword,
            "max_pages_per_query": max_pages_per_keyword,
            "page_size": page_size,
            "stale_after_hours": config.stale_after_hours,
            "removed_after_hours": config.removed_after_hours,
            "expire_grace_hours": config.expire_grace_hours,
            "provider_request_cap": max_provider_requests,
        }

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
    ) -> str:
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
            unchanged = raw_job.payload_hash == payload_hash
            for key, value in defaults.items():
                setattr(raw_job, key, value)
            raw_job.save(update_fields=list(defaults.keys()) + ["updated_at"])
            created = False
            if unchanged:
                result_status = "unchanged"
            else:
                run_log.updated_raw_count += 1
                result_status = "updated"
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
                result_status = "created"
            except IntegrityError:
                # Concurrent creation fallback
                raw_job = RawJobRecord.objects.get(source=source, source_job_id=job_id)
                for key, value in defaults.items():
                    setattr(raw_job, key, value)
                raw_job.save(update_fields=list(defaults.keys()) + ["updated_at"])
                created = False
                run_log.updated_raw_count += 1
                result_status = "updated"

        if normalize:
            try:
                norm_job = JobNormalizationService.normalize(raw_job)
                if norm_job:
                    run_log.normalized_count += 1

                    try:
                        from apps.jobs.services.skill_extraction import JobSkillExtractionService
                        JobSkillExtractionService.extract_for_job(norm_job)
                    except Exception as extraction_err:
                        run_log.error_summary += f"Skill extraction error for {job_id}: {cls._safe_error(extraction_err)}\n"

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

        return result_status

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
