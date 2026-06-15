from django.views.generic import View, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render

from apps.jobs.services.query import JobQueryService
from apps.matching.services.match_result import MatchResultService
from apps.matching.services.quick_match import QuickMatchService, QuickMatchRateLimitExceeded
from apps.matching.forms import QuickMatchForm
from apps.matching.models import MatchResult

class CreateMatchView(LoginRequiredMixin, View):
    def post(self, request, public_id):
        job = JobQueryService.get_public_job(public_id)
        match_result = MatchResultService.create_match_result(user=request.user, job=job)
        return redirect("matching:detail", public_id=match_result.public_id)

class QuickMatchView(View):
    def post(self, request, public_id):
        job = JobQueryService.get_public_job(public_id)
        form = QuickMatchForm(request.POST)
        
        if form.is_valid():
            try:
                session_key = request.session.session_key
                if not session_key:
                    request.session.create()
                    session_key = request.session.session_key

                ip_address = request.META.get('REMOTE_ADDR')

                session = QuickMatchService.run_quick_match(
                    session_key=session_key,
                    job=job,
                    entered_skills=form.cleaned_data['skills'],
                    experience_level=form.cleaned_data['experience_level'],
                    french_level=form.cleaned_data['french_level'],
                    ip_address=ip_address
                )
                return render(request, "matching/partials/quick_match_result.html", {"session": session, "job": job})
            except QuickMatchRateLimitExceeded:
                return render(request, "matching/partials/quick_match_result.html", {
                    "error": "Rate limit exceeded. Please try again later.",
                    "job": job
                })
        
        # If form invalid, re-render the job detail partial or something
        return render(request, "matching/partials/quick_match_form.html", {"form": form, "job": job})

class MatchHistoryView(LoginRequiredMixin, ListView):
    model = MatchResult
    template_name = "matching/match_history.html"
    context_object_name = "matches"
    
    def get_queryset(self):
        return MatchResultService.list_user_matches(self.request.user)

class MatchDetailView(LoginRequiredMixin, DetailView):
    model = MatchResult
    template_name = "matching/match_detail.html"
    context_object_name = "match"
    
    def get_object(self, queryset=None):
        return MatchResultService.get_user_match(self.request.user, self.kwargs['public_id'])
