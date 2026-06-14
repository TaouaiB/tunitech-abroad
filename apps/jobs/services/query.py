from django.http import Http404
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils import timezone

from apps.jobs.models import NormalizedJob, JobStatus


class JobQueryService:
    @classmethod
    def get_public_job(cls, public_id) -> NormalizedJob:
        """
        Retrieve a job for public display by its UUID public_id.
        Raises Http404 if the job does not exist, is private, or has an invalid UUID.
        """
        try:
            job = NormalizedJob.objects.select_related("source").get(
                Q(expires_at__isnull=True) | Q(expires_at__gte=timezone.now()),
                public_id=public_id,
                status=JobStatus.ACTIVE,
                source__is_active=True,
            )
            return job
        except (NormalizedJob.DoesNotExist, TypeError, ValidationError, ValueError):
            raise Http404("Job not found or not active")
