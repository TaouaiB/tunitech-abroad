from datetime import timedelta
from django.utils import timezone
from django.db.models import Q

from apps.jobs.models import NormalizedJob, JobStatus


class JobFreshnessService:
    @staticmethod
    def mark_stale_and_expired(now=None) -> dict:
        if now is None:
            now = timezone.now()

        stale_threshold = now - timedelta(hours=24)
        removed_threshold = now - timedelta(hours=72)

        results = {
            "expired_count": 0,
            "removed_count": 0,
            "stale_count": 0,
            "active_count": 0,
        }

        # 1. Expired jobs: expires_at is past
        expired_qs = NormalizedJob.objects.filter(
            expires_at__lt=now
        ).exclude(status__in=[JobStatus.EXPIRED.value, JobStatus.ARCHIVED.value])
        results["expired_count"] = expired_qs.update(status=JobStatus.EXPIRED.value)

        # 2. Removed jobs: last_seen_at older than 72h
        # We only consider jobs that are not already EXPIRED, REMOVED or ARCHIVED
        removed_qs = NormalizedJob.objects.filter(
            last_seen_at__lt=removed_threshold
        ).exclude(status__in=[JobStatus.EXPIRED.value, JobStatus.REMOVED.value, JobStatus.ARCHIVED.value])
        results["removed_count"] = removed_qs.update(status=JobStatus.REMOVED.value)

        # 3. Stale jobs: last_seen_at older than 24h but newer than 72h
        stale_qs = NormalizedJob.objects.filter(
            last_seen_at__lt=stale_threshold,
            last_seen_at__gte=removed_threshold
        ).exclude(status__in=[JobStatus.EXPIRED.value, JobStatus.REMOVED.value, JobStatus.STALE.value, JobStatus.ARCHIVED.value])
        results["stale_count"] = stale_qs.update(status=JobStatus.STALE.value)

        # 4. Active jobs: last_seen_at newer than 24h, and expires_at is in future or null
        active_qs = NormalizedJob.objects.filter(
            last_seen_at__gte=stale_threshold
        ).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gte=now)
        ).exclude(status__in=[JobStatus.ACTIVE.value, JobStatus.ARCHIVED.value])
        results["active_count"] = active_qs.update(status=JobStatus.ACTIVE.value)

        return results
