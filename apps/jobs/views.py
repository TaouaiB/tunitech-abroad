import logging

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from apps.jobs.forms import JobSearchForm
from apps.jobs.services.search import JobSearchService
from apps.jobs.services.query import JobQueryService
from apps.jobs.services.revalidation import JobRevalidationService
from apps.recommendations.services.saved_jobs import SavedJobService
from apps.jobs.services.presentation import JobPresentationService

try:
    from apps.analytics.services.user_event import UserEventService
except ImportError:
    UserEventService = None

logger = logging.getLogger(__name__)


def safe_record_event(event_type, user, metadata=None):
    if UserEventService is None:
        return
    try:
        UserEventService.record_event(
            event_type=event_type,
            user=user if user and user.is_authenticated else None,
            metadata=metadata
        )
    except Exception as exc:
        logger.warning("Failed to record event %s: %s", event_type, exc)


def job_list(request):
    form = JobSearchForm(request.GET)
    filters = {}
    if form.is_valid():
        filters = form.cleaned_data

    result = JobSearchService.search(filters, user=request.user)

    safe_record_event("job_search", request.user, metadata={"q": filters.get("q", "")})

    return render(request, "jobs/job_list.html", {
        "form": form,
        "page_obj": result.page_obj,
        "paginator": result.paginator,
        "filters": result.filters,
        "total_count": result.total_count,
        "sort": result.sort,
    })


def job_detail(request, public_id):
    job = JobQueryService.get_public_job(public_id)
    from apps.jobs.services.eligibility import JobEligibilityService
    if not request.user.is_staff and not JobEligibilityService.is_publicly_visible(job):
        from django.http import Http404
        raise Http404("Job is not publicly visible")

    try:
        job = JobRevalidationService.revalidate_if_needed(job)
    except Exception as exc:
        logger.warning("Job revalidation failed for %s: %s", public_id, exc)

    safe_record_event("job_detail_view", request.user, metadata={"public_id": str(public_id)})

    is_saved = False
    if request.user.is_authenticated:
        is_saved = SavedJobService.is_saved(request.user, public_id)

    valid_languages = JobPresentationService.get_valid_languages(job)

    return render(request, "jobs/job_detail.html", {
        "job": job,
        "is_saved": is_saved,
        "valid_languages": valid_languages,
    })

@login_required
@require_POST
def save_job(request, public_id):
    SavedJobService.save_job(request.user, public_id)
    if request.headers.get("HX-Request") == "true":
        job = JobQueryService.get_public_job(public_id)
        return render(request, "jobs/partials/save_button.html", {"job": job, "is_saved": True})
    return redirect("jobs:detail", public_id=public_id)

@login_required
@require_POST
def unsave_job(request, public_id):
    SavedJobService.remove_saved_job(request.user, public_id)
    if request.headers.get("HX-Request") == "true":
        job = JobQueryService.get_public_job(public_id)
        return render(request, "jobs/partials/save_button.html", {"job": job, "is_saved": False})
    return redirect("jobs:detail", public_id=public_id)
