from django.contrib.postgres.search import SearchVector

from apps.jobs.models import NormalizedJob


class JobSearchVectorService:
    @staticmethod
    def update_search_vector(job: NormalizedJob) -> None:
        from django.db import models
        from django.db.models.functions import Cast

        vector = SearchVector("title", weight="A")
        vector += SearchVector(Cast("required_skills_json", output_field=models.TextField()), weight="B")
        vector += SearchVector("company_name", weight="C")
        vector += SearchVector("location", weight="C")
        vector += SearchVector(Cast("optional_skills_json", output_field=models.TextField()), weight="C")
        vector += SearchVector("description", weight="D")

        NormalizedJob.objects.filter(id=job.id).update(search_vector=vector)
