from datetime import time, timedelta
from django.utils import timezone

from apps.jobs.models import NormalizedJob, JobStatus, JobIngestionConfig, JobIngestionRun


class JobFreshnessService:
    @staticmethod
    def mark_stale_and_expired(now=None) -> dict:
        if now is None:
            now = timezone.now()

        config = JobIngestionConfig.objects.filter(enabled=True).first()
        stale_hours = getattr(config, "stale_after_hours", 24) if config else 24
        removed_hours = getattr(config, "removed_after_hours", 72) if config else 72
        expire_grace_hours = getattr(config, "expire_grace_hours", 24) if config else 24

        stale_threshold = now - timedelta(hours=stale_hours)
        removed_threshold = now - timedelta(hours=removed_hours)

        results = {
            "expired_count": 0,
            "removed_count": 0,
            "stale_count": 0,
            "active_count": 0,
            "aborted": False,
        }

        # Safety: Failed ingestion run does not mass-stale jobs
        last_run = JobIngestionRun.objects.order_by("-started_at").first()
        if last_run and last_run.status == "failed":
            results["aborted"] = True
            return results

        updates_by_status = {
            JobStatus.EXPIRED.value: [],
            JobStatus.REMOVED.value: [],
            JobStatus.STALE.value: [],
            JobStatus.ACTIVE.value: [],
        }

        for job in NormalizedJob.objects.exclude(status=JobStatus.ARCHIVED.value).only(
            "id",
            "status",
            "expires_at",
            "last_seen_at",
        ):
            new_status = JobFreshnessService._status_for_job(
                job,
                now=now,
                stale_threshold=stale_threshold,
                removed_threshold=removed_threshold,
                expire_grace_hours=expire_grace_hours,
            )
            if new_status != job.status:
                updates_by_status[new_status].append(job.id)

        for status, ids in updates_by_status.items():
            if ids:
                NormalizedJob.objects.filter(id__in=ids).update(status=status)

        results["expired_count"] = len(updates_by_status[JobStatus.EXPIRED.value])
        results["removed_count"] = len(updates_by_status[JobStatus.REMOVED.value])
        results["stale_count"] = len(updates_by_status[JobStatus.STALE.value])
        results["active_count"] = len(updates_by_status[JobStatus.ACTIVE.value])

        return results

    @staticmethod
    def _status_for_job(job, *, now, stale_threshold, removed_threshold, expire_grace_hours) -> str:
        expires_at = JobFreshnessService._effective_expires_at(job.expires_at)
        if expires_at and expires_at < now - timedelta(hours=expire_grace_hours):
            return JobStatus.EXPIRED.value
        if job.last_seen_at and job.last_seen_at < removed_threshold:
            return JobStatus.REMOVED.value
        if job.last_seen_at and job.last_seen_at < stale_threshold:
            return JobStatus.STALE.value
        return JobStatus.ACTIVE.value

    @staticmethod
    def _effective_expires_at(expires_at):
        if not expires_at:
            return None
        if expires_at.timetz().replace(tzinfo=None) == time.min:
            return expires_at + timedelta(days=1) - timedelta(microseconds=1)
        return expires_at
