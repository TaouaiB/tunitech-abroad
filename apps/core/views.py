from django.shortcuts import render

from apps.core.services.homepage import HomepageService

def home(request):
    latest_jobs = HomepageService.latest_public_jobs()
    return render(request, "core/home.html", {"latest_jobs": latest_jobs})
