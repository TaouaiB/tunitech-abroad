import logging

from apps.jobs.models import NormalizedJob

logger = logging.getLogger(__name__)


class JobRevalidationService:
    @classmethod
    def revalidate_if_needed(cls, job: NormalizedJob) -> NormalizedJob:
        """
        Shell for future high-intent job detail refresh.
        Currently safely returns the job without making external API calls.
        """
        # In the future, we would check job freshness/expiration here 
        # and potentially call the source API to revalidate.
        # For Phase 5, this is a safe no-op.
        
        return job
