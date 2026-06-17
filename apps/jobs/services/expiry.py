from datetime import timedelta
from django.utils import timezone
from apps.jobs.models import NormalizedJob, JobStatus, RawJobRecord

class JobExpiryService:
    @classmethod
    def mark_stale_jobs(cls, expire_after_days=21):
        """
        Marks active jobs that haven't been seen recently as stale/expired.
        Does not hard delete records.
        """
        cutoff_date = timezone.now() - timedelta(days=expire_after_days)
        
        # We find active jobs that haven't been seen since the cutoff date.
        # This relies on ingestion service updating `last_seen_at` for RawJobRecord and Normalization
        stale_jobs = NormalizedJob.objects.filter(
            status=JobStatus.ACTIVE,
            last_seen_at__lt=cutoff_date
        )
        
        count = stale_jobs.count()
        stale_jobs.update(status=JobStatus.STALE)
        
        return count
