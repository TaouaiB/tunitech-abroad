from uuid import UUID
from django.http import Http404
from apps.recommendations.models import SavedJob
from apps.jobs.services.query import JobQueryService
from apps.analytics.services.user_event import UserEventService
from apps.jobs.models import NormalizedJob
import logging

logger = logging.getLogger(__name__)


class SavedJobService:
    @classmethod
    def save_job(cls, user, job_public_id: UUID) -> SavedJob:
        job = JobQueryService.get_public_job(job_public_id)

        saved_job, created = SavedJob.objects.get_or_create(user=user, job=job)
        
        if created:
            try:
                UserEventService.record_event(
                    event_type="saved_job_created",
                    user=user,
                    metadata={"job_public_id": str(job_public_id)},
                )
            except Exception as e:
                logger.warning(f"Failed to record saved_job_created event: {e}", exc_info=True)

        return saved_job

    @classmethod
    def remove_saved_job(cls, user, job_public_id: UUID) -> bool:
        # Use get_or_none pattern or handle DoesNotExist safely, job might be inactive
        try:
            job = NormalizedJob.objects.get(public_id=job_public_id)
            deleted, _ = SavedJob.objects.filter(user=user, job=job).delete()
            return deleted > 0
        except NormalizedJob.DoesNotExist:
            return False

    @classmethod
    def get_saved_jobs(cls, user):
        return SavedJob.objects.filter(user=user).select_related("job", "job__source").order_by("-saved_at")

    @classmethod
    def is_saved(cls, user, job_public_id: UUID) -> bool:
        if not user.is_authenticated:
            return False
        return SavedJob.objects.filter(user=user, job__public_id=job_public_id).exists()
