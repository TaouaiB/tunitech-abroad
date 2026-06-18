from apps.jobs.models import JobStatus, NormalizedJob


class JobAdminOperationsService:
    @staticmethod
    def mark_selected_jobs_status(job_ids, status: JobStatus) -> int:
        return NormalizedJob.objects.filter(id__in=job_ids).update(status=status)

    @staticmethod
    def queue_selected_eligible_enrichments(job_ids) -> int:
        from apps.llm.services.job_enrichment import queue_selected_eligible_enrichments

        return queue_selected_eligible_enrichments(job_ids=job_ids)
