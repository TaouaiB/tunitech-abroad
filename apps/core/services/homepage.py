from django.db.models import F

from apps.jobs.models import JobStatus, NormalizedJob


class HomepageService:
    @staticmethod
    def latest_public_jobs(limit: int = 3):
        return (
            NormalizedJob.objects.filter(status=JobStatus.ACTIVE)
            .select_related("source")
            .order_by(F("published_at").desc(nulls_last=True), F("first_seen_at").desc(nulls_last=True))
        )[:limit]
