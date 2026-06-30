from dataclasses import dataclass
from typing import Any

from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.core.paginator import InvalidPage, Paginator
from django.db.models import F, Q, QuerySet, TextField
from django.db.models.functions import Cast
from django.utils.dateparse import parse_date
from django.utils.timezone import make_aware

from apps.jobs.models import NormalizedJob
from apps.jobs.services.eligibility import JobEligibilityService


@dataclass(frozen=True)
class PaginatedJobResult:
    page_obj: Any
    paginator: Paginator
    filters: dict[str, str]
    total_count: int
    sort: str


class JobSearchService:
    @classmethod
    def search(cls, filters: dict, request=None) -> PaginatedJobResult:
        filters = cls._clean_filters(filters)
        qs = cls._public_queryset()

        q = filters.get("q", "")
        location = filters.get("location", "")
        contract_type = filters.get("contract_type", "")
        job_type = filters.get("job_type", "")
        remote_type = filters.get("remote_type", "")
        experience_level = filters.get("experience_level", "")
        skill = filters.get("skill", "")
        company = filters.get("company", "")
        published_exact = filters.get("published_exact", "")
        published_from = filters.get("published_from", "")
        published_to = filters.get("published_to", "")
        invalid_filters = dict(filters.get("_invalid_filters", {}))

        if contract_type:
            qs = qs.filter(contract_type=contract_type)
        if job_type:
            qs = qs.filter(job_type=job_type)
        if remote_type:
            qs = qs.filter(remote_type=remote_type)
        if experience_level:
            qs = qs.filter(experience_level=experience_level)
        if company:
            qs = qs.filter(company_name__icontains=company)
        if location:
            qs = qs.filter(
                Q(city__icontains=location)
                | Q(department__icontains=location)
                | Q(region__icontains=location)
                | Q(location__icontains=location)
            )

        if skill:
            skill_names = cls._skill_search_terms(skill)
            skill_query = Q()
            for skill_name in skill_names:
                skill_query |= (
                    Q(required_skills_json__contains=[skill_name])
                    | Q(optional_skills_json__contains=[skill_name])
                    | Q(required_skills_json__icontains=skill_name)
                    | Q(optional_skills_json__icontains=skill_name)
                    | Q(job_skills__skill__canonical_name__iexact=skill_name)
                )
            qs = qs.filter(skill_query).distinct()

        if published_exact:
            date_range = cls._date_range(published_exact, end_of_day=True)
            if date_range:
                qs = qs.filter(published_at__range=date_range)
            else:
                invalid_filters["published_exact"] = published_exact
        else:
            if published_from:
                date_range = cls._date_range(published_from, end_of_day=False)
                if date_range:
                    qs = qs.filter(published_at__gte=date_range[0])
                else:
                    invalid_filters["published_from"] = published_from
            if published_to:
                date_range = cls._date_range(published_to, end_of_day=True)
                if date_range:
                    qs = qs.filter(published_at__lte=date_range[1])
                else:
                    invalid_filters["published_to"] = published_to

        has_query = False
        if q:
            search_query = SearchQuery(q, config="french")
            qs = qs.filter(search_vector=search_query)
            qs = qs.annotate(rank=SearchRank(F("search_vector"), search_query))
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
            page_obj = paginator.page(max(1, paginator.num_pages))

        result = PaginatedJobResult(
            page_obj=page_obj,
            paginator=paginator,
            filters={key: value for key, value in filters.items() if not key.startswith("_")},
            total_count=paginator.count,
            sort=sort,
        )

        cls._log_search_safely(request, filters, q, company, skill, invalid_filters, paginator.count)

        return result

    @staticmethod
    def _log_search_safely(
        request,
        filters: dict,
        raw_q: str,
        company: str,
        skill: str,
        invalid_filters: dict,
        result_count: int,
        ):
        if not request:
            return

        import hashlib
        from apps.jobs.models import SearchQueryLog
        import logging
        logger = logging.getLogger(__name__)

        try:
            user = getattr(request, "user", None)
            user_hash = ""
            if user and user.is_authenticated:
                user_hash = hashlib.sha256(str(user.id).encode()).hexdigest()

            session_key = getattr(request.session, "session_key", "")
            session_hash = ""
            if session_key:
                session_hash = hashlib.sha256(str(session_key).encode()).hexdigest()

            SearchQueryLog.objects.create(
                query=raw_q,
                normalized_query=raw_q.strip().lower(),
                company=company,
                normalized_company=company.strip().lower(),
                skill=skill,
                filters_json=filters,
                result_count=result_count,
                user_hash=user_hash,
                session_hash=session_hash,
                had_invalid_filters=bool(invalid_filters),
                was_whitespace_only=bool(filters.get("_was_whitespace_only")),
            )
        except Exception as e:
            logger.warning("Failed to log search query: %s", e)

    @staticmethod
    def _public_queryset() -> QuerySet[NormalizedJob]:
        return JobEligibilityService.filter_publicly_visible(
            NormalizedJob.objects.select_related("source")
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
        cleaned = {
            str(key): str(value).strip()
            for key, value in filters.items()
            if value is not None and str(value).strip()
        }
        raw_q = filters.get("q")
        if raw_q is not None and str(raw_q) and not str(raw_q).strip():
            cleaned["_was_whitespace_only"] = True
        cleaned["_invalid_filters"] = {}
        return cleaned

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

    @staticmethod
    def _date_range(value: str, *, end_of_day: bool):
        import datetime

        date_val = parse_date(value)
        if not date_val:
            return None
        start_datetime = make_aware(datetime.datetime.combine(date_val, datetime.time.min))
        end_datetime = make_aware(datetime.datetime.combine(date_val, datetime.time.max))
        return start_datetime, end_datetime

    @staticmethod
    def _skill_search_terms(skill: str) -> set[str]:
        terms = {skill}
        try:
            from apps.skills.models import SkillAlias

            alias = (
                SkillAlias.objects.select_related("skill")
                .filter(normalized_alias=skill.strip().lower(), skill__is_active=True)
                .first()
            )
            if alias:
                terms.add(alias.alias)
                terms.add(alias.skill.canonical_name)
        except Exception:
            pass
        return {term for term in terms if term}
