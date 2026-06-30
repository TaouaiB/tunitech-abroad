import logging
from typing import Any, Dict
from django.utils import timezone
from django.db.models import Count
from apps.jobs.models import SearchQueryLog

logger = logging.getLogger(__name__)

class JobSearchAuditService:
    @classmethod
    def audit(cls) -> Dict[str, Any]:
        now = timezone.now()
        
        total_searches = SearchQueryLog.objects.count()
        zero_result_searches = SearchQueryLog.objects.filter(result_count=0).count()
        whitespace_searches = SearchQueryLog.objects.filter(was_whitespace_only=True).count()
        invalid_filter_searches = SearchQueryLog.objects.filter(had_invalid_filters=True).count()
        
        # Top searches
        top_queries = list(
            SearchQueryLog.objects.exclude(normalized_query="")
            .values("normalized_query")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )
        
        # Company filters
        top_companies = list(
            SearchQueryLog.objects.exclude(company="")
            .values("normalized_company")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )

        top_zero_result_queries = list(
            SearchQueryLog.objects.filter(result_count=0)
            .exclude(normalized_query="")
            .values("normalized_query")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )

        top_skill_queries = list(
            SearchQueryLog.objects.exclude(skill="")
            .values("skill")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )
        
        diagnostics = {
            "ok": True,
            "service": "job_search_audit",
            "generated_at": now.isoformat(),
            "scope": {},
            "counts": {
                "total_searches": total_searches,
                "zero_result_searches": zero_result_searches,
                "whitespace_only_searches": whitespace_searches,
                "invalid_filter_searches": invalid_filter_searches,
            },
            "statuses": {},
            "reasons": {},
            "top_items": {
                "top_queries": top_queries,
                "top_zero_result_queries": top_zero_result_queries,
                "top_companies": top_companies,
                "top_skill_queries": top_skill_queries,
            },
            "warnings": [],
            "errors": [],
            "recommended_actions": [],
            "artifacts": {},
        }
        
        return diagnostics
