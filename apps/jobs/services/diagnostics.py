import logging
from datetime import timedelta
from typing import Any, Dict

from django.db.models import Count
from django.utils import timezone

from apps.jobs.models import (
    JobIngestionConfig,
    JobIngestionQueryRun,
    JobIngestionRun,
    JobSource,
    NormalizedJob,
    RawJobRecord,
)
from apps.jobs.services.eligibility import JobEligibilityService

logger = logging.getLogger(__name__)


class JobIngestionDiagnosticsService:
    @classmethod
    def run(cls, source_slug: str = "france_travail") -> Dict[str, Any]:
        now = timezone.now()

        source = JobSource.objects.filter(slug=source_slug).first()
        config = JobIngestionConfig.objects.filter(enabled=True).order_by("name").first()
        latest_runs = list(JobIngestionRun.objects.select_related("config").order_by("-started_at")[:5])

        raw_qs = RawJobRecord.objects.all()
        normalized_qs = NormalizedJob.objects.select_related("source").prefetch_related("job_skills")
        if source:
            raw_qs = raw_qs.filter(source=source)
            normalized_qs = normalized_qs.filter(source=source)

        raw_count = raw_qs.count()
        normalization_statuses = dict(
            raw_qs.values_list("normalization_status")
            .annotate(count=Count("id"))
        )

        normalized_count = normalized_qs.count()
        statuses = dict(
            normalized_qs.values_list("status")
            .annotate(count=Count("id"))
        )

        skill_extraction_statuses = dict(
            normalized_qs.values_list("skill_extraction_status")
            .annotate(count=Count("id"))
        )

        active_qs = normalized_qs.filter(status="active")
        active_count = active_qs.count()
        public_visible_count = JobEligibilityService.filter_publicly_visible(active_qs).count()
        matchable_count = JobEligibilityService.filter_matchable(active_qs).count()

        eligibility_reasons: dict[str, int] = {}
        for job in active_qs[:2000]:
            reason = JobEligibilityService.reason(job)
            eligibility_reasons[reason] = eligibility_reasons.get(reason, 0) + 1

        diagnostics = {
            "ok": True,
            "service": "job_ingestion_diagnostics",
            "generated_at": now.isoformat(),
            "scope": {
                "source_slug": source_slug,
                "source_exists": bool(source),
            },
            "counts": {
                "fetched_latest_runs": sum(run.fetched_count for run in latest_runs),
                "raw_total": raw_count,
                "normalized_total": normalized_count,
                "active": active_count,
                "stale": statuses.get("stale", 0),
                "expired": statuses.get("expired", 0),
                "removed": statuses.get("removed", 0),
                "public_visible": public_visible_count,
                "public_matchable": matchable_count,
                "zero_skill_jobs": normalized_qs.filter(job_skills__isnull=True).distinct().count(),
            },
            "statuses": {
                "normalization_statuses": normalization_statuses,
                "freshness_statuses": statuses,
                "skill_extraction_statuses": skill_extraction_statuses,
            },
            "reasons": {
                "eligibility_reasons": eligibility_reasons,
                "freshness_reasons": {
                    "stale": statuses.get("stale", 0),
                    "expired": statuses.get("expired", 0),
                    "removed": statuses.get("removed", 0),
                },
            },
            "top_items": [],
            "warnings": [],
            "errors": [],
            "recommended_actions": [],
        }

        if config:
            diagnostics["scope"]["active_config"] = {
                "name": config.name,
                "target_daily_fetch_count": config.target_daily_fetch_count,
                "max_jobs_per_run": config.max_jobs_per_run,
                "max_pages_per_query": config.max_pages_per_query,
                "page_size": config.page_size,
                "queries_count": len(config.queries_json or config.custom_keywords or []),
                "stale_after_hours": config.stale_after_hours,
                "removed_after_hours": config.removed_after_hours,
                "expire_grace_hours": config.expire_grace_hours,
            }

        # Format latest runs
        runs_info = []
        for run in latest_runs:
            query_runs = list(
                JobIngestionQueryRun.objects.filter(ingestion_run=run)
                .order_by("started_at")
                .values(
                    "query_label",
                    "fetched_count",
                    "created_count",
                    "updated_count",
                    "unchanged_count",
                    "skipped_count",
                    "error_count",
                    "requested_range_json",
                    "error_message",
                )
            )
            runs_info.append({
                "id": run.id,
                "started_at": run.started_at.isoformat(),
                "status": run.status,
                "fetched": run.fetched_count,
                "created_raw": run.created_raw_count,
                "updated_raw": run.updated_raw_count,
                "normalized": run.normalized_count,
                "errors": run.error_count,
                "config_snapshot": run.config_snapshot_json,
                "query_runs": query_runs,
            })

        diagnostics["artifacts"] = {
            "latest_runs": runs_info,
        }

        # Calculate warnings explaining low job counts
        # e.g., if manual ingestion fetches a lot but active is low
        if latest_runs and latest_runs[0].fetched_count > 0 and public_visible_count < 300:
            diagnostics["warnings"].append(
                "Public visible jobs are low compared to fetched amounts. "
                "This can happen if jobs are being aggressively marked as stale, "
                "failing skill extraction, or being hidden by eligibility rules."
            )

            hidden_by_eligibility = active_count - public_visible_count
            if hidden_by_eligibility > 0:
                diagnostics["warnings"].append(
                    f"{hidden_by_eligibility} active jobs are hidden by eligibility rules "
                    "(e.g., missing skills, non-IT classification)."
                )

            stale_or_removed = statuses.get("stale", 0) + statuses.get("removed", 0) + statuses.get("expired", 0)
            if stale_or_removed > active_count:
                diagnostics["warnings"].append(
                    f"High number of stale/removed/expired jobs ({stale_or_removed}) compared to active ({active_count}). "
                    "Check freshness settings or recent ingestion failures."
                )

        if config and latest_runs:
            latest = latest_runs[0]
            if latest.fetched_count < config.target_daily_fetch_count:
                diagnostics["warnings"].append(
                    f"Latest run fetched {latest.fetched_count}, below target_daily_fetch_count {config.target_daily_fetch_count}."
                )
                diagnostics["recommended_actions"].append(
                    "Review per-query counts, provider request caps, max_pages_per_query, and source availability."
                )

        return diagnostics
