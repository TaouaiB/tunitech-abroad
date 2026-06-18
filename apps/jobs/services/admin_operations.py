from apps.jobs.models import JobStatus, NormalizedJob


class JobAdminOperationsService:
    @staticmethod
    def mark_selected_jobs_status(job_ids, status: JobStatus) -> int:
        return NormalizedJob.objects.filter(id__in=job_ids).update(status=status)
