from dataclasses import dataclass
from typing import Any

from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.core.paginator import InvalidPage, Paginator
from django.db.models import Q, QuerySet, TextField
from django.db.models.functions import Cast
from django.utils import timezone

from apps.jobs.models import JobStatus, NormalizedJob


@dataclass(frozen=True)
class PaginatedJobResult:
    page_obj: Any
    paginator: Paginator
    filters: dict[str, str]
    total_count: int
    sort: str


class JobSearchService:
    @classmethod
    def search(cls, filters: dict, user=None) -> PaginatedJobResult:
        filters = cls._clean_filters(filters)
        qs = cls._public_queryset()

        q = filters.get("q", "")
        location = filters.get("location", "")
        contract_type = filters.get("contract_type", "")
        job_type = filters.get("job_type", "")
        remote_type = filters.get("remote_type", "")
        experience_level = filters.get("experience_level", "")
        skill = filters.get("skill", "")

        if contract_type:
            qs = qs.filter(contract_type=contract_type)
        if job_type:
            qs = qs.filter(job_type=job_type)
        if remote_type:
            qs = qs.filter(remote_type=remote_type)
        if experience_level:
            qs = qs.filter(experience_level=experience_level)
        if location:
            qs = qs.filter(
                Q(city__icontains=location)
                | Q(department__icontains=location)
                | Q(region__icontains=location)
                | Q(location__icontains=location)
            )

        if skill:
            qs = qs.filter(
                Q(required_skills_json__contains=[skill])
                | Q(optional_skills_json__contains=[skill])
                | Q(required_skills_json__icontains=skill)
                | Q(optional_skills_json__icontains=skill)
            )

        has_query = False
        if q:
            search_query = SearchQuery(q, config="french")
            search_document = cls._search_document()
            qs = qs.annotate(search_document=search_document)
            qs = qs.filter(search_document=search_query)
            qs = qs.annotate(rank=SearchRank(search_document, search_query))
            has_query = True

        sort = filters.get("sort", "")
        if not sort:
            sort = "relevance" if has_query else "newest"

        if sort == "relevance" and has_query:
            qs = qs.order_by("-rank", "-published_at", "-created_at")
        elif sort == "company":
            qs = qs.order_by("company_name", "-published_at")
        else:
            sort = "newest"
            qs = qs.order_by("-published_at", "-created_at")

        page = cls._positive_int(filters.get("page"), default=1, maximum=None)
        page_size = cls._positive_int(filters.get("page_size"), default=20, maximum=100)
        paginator = Paginator(qs, page_size)

        try:
            page_obj = paginator.page(page)
        except InvalidPage:
            page_obj = paginator.page(paginator.num_pages)

        return PaginatedJobResult(
            page_obj=page_obj,
            paginator=paginator,
            filters=filters,
            total_count=paginator.count,
            sort=sort,
        )

    @staticmethod
    def _public_queryset() -> QuerySet[NormalizedJob]:
        now = timezone.now()
        return (
            NormalizedJob.objects.select_related("source")
            .filter(status=JobStatus.ACTIVE, source__is_active=True)
            .filter(Q(expires_at__isnull=True) | Q(expires_at__gte=now))
        )

    @staticmethod
    def _search_document() -> Any:
        return (
            SearchVector("title", weight="A", config="french")
            + SearchVector(Cast("required_skills_json", TextField()), weight="A", config="french")
            + SearchVector(Cast("optional_skills_json", TextField()), weight="B", config="french")
            + SearchVector("company_name", weight="B", config="french")
            + SearchVector("location", weight="C", config="french")
            + SearchVector("city", weight="C", config="french")
            + SearchVector("region", weight="C", config="french")
            + SearchVector("description", weight="D", config="french")
        )

    @staticmethod
    def _clean_filters(filters: dict) -> dict[str, str]:
        return {
            str(key): str(value).strip()
            for key, value in filters.items()
            if value is not None and str(value).strip()
        }

    @staticmethod
    def _positive_int(value: str | None, *, default: int, maximum: int | None) -> int:
        try:
            parsed = int(value or default)
        except (TypeError, ValueError):
            return default

        if parsed < 1:
            return default
        if maximum is not None and parsed > maximum:
            return maximum
        return parsed
