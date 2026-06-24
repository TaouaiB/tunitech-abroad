from apps.jobs.models import JobStatus, NormalizedJob


class JobAdminOperationsService:
    @staticmethod
    def mark_selected_jobs_status(job_ids, status: JobStatus) -> int:
        return NormalizedJob.objects.filter(id__in=job_ids).update(status=status)

    @staticmethod
    def queue_selected_eligible_enrichments(job_ids) -> int:
        from apps.llm.services.job_enrichment import queue_selected_eligible_enrichments

        return queue_selected_eligible_enrichments(job_ids=job_ids)

    @staticmethod
    def re_extract_skills(job_ids) -> int:
        from apps.jobs.services.skill_extraction import JobSkillExtractionService
        jobs = NormalizedJob.objects.filter(id__in=job_ids)
        count = 0
        for job in jobs:
            JobSkillExtractionService.extract_for_job(job)
            count += 1
        return count

    @staticmethod
    def rematerialize_from_enrichment(job_ids) -> int:
        from apps.jobs.services.skill_materialization import JobSkillMaterializationService
        from apps.llm.models import JobEnrichment

        jobs = NormalizedJob.objects.filter(id__in=job_ids)
        count = 0
        for job in jobs:
            enrichment = JobEnrichment.objects.filter(
                job=job,
                status=JobEnrichment.Status.SUCCESS,
            ).first()
            if not enrichment:
                continue
            JobSkillMaterializationService.materialize_for_job(
                job=job,
                source="llm",
                enrichment=enrichment,
            )
            count += 1
        return count
