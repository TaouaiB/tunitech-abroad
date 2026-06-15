from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.cvs.forms import CVUploadForm
from apps.cvs.services.upload import CVUploadService
from apps.cvs.services.deletion import CVDeletionService
from apps.cvs.models import CVUpload
from apps.profiles.services.profile_update import ProfileUpdateService
from apps.recommendations.services.query import RecommendationQueryService
from apps.recommendations.services.saved_jobs import SavedJobService

@login_required
def dashboard_recommendations(request):
    result = RecommendationQueryService.get_dashboard_recommendations(request.user)
    return render(request, "dashboard/recommendations.html", {"result": result})

@login_required
def dashboard_saved_jobs(request):
    saved_jobs = SavedJobService.get_saved_jobs(request.user)
    return render(request, "dashboard/saved_jobs.html", {"saved_jobs": saved_jobs})

@login_required
def dashboard_home(request):
    return render(request, "dashboard/home.html")

@login_required
def dashboard_profile(request):
    user = request.user
    profile = getattr(user, 'candidate_profile', None)
    
    if request.method == "POST":
        from apps.profiles.forms import ProfileForm
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            ProfileUpdateService.update_profile(user, form.cleaned_data)
            messages.success(request, "Profile updated successfully.")
            return redirect("dashboard:profile")
    else:
        from apps.profiles.forms import ProfileForm
        form = ProfileForm(instance=profile)
        
    return render(request, "dashboard/profile.html", {
        "form": form,
        "profile": profile
    })

@login_required
def dashboard_cv(request):
    user = request.user
    
    if request.method == "POST":
        if "delete_cv_id" in request.POST:
            cv_public_id = request.POST.get("delete_cv_id")
            result = CVDeletionService.delete_cv(user, cv_public_id)
            if result.get("success"):
                messages.success(request, "CV deleted successfully.")
            else:
                messages.error(request, str(result.get("error", "Error deleting CV.")))
            return redirect("dashboard:cv")
            
        form = CVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                CVUploadService.upload_cv(
                    user, 
                    form.cleaned_data['file'], 
                    consent_accepted=form.cleaned_data['consent_accepted']
                )
                messages.success(request, "CV uploaded successfully. It is now being parsed.")
                return redirect("dashboard:cv")
            except ValueError as e:
                messages.error(request, str(e))
    else:
        form = CVUploadForm()
        
    active_cv = CVUpload.objects.filter(user=user, is_active=True).first()
    
    return render(request, "dashboard/cv_manage.html", {
        "form": form,
        "active_cv": active_cv
    })

@login_required
def dashboard_cv_status(request, public_id):
    cv_upload = get_object_or_404(CVUpload.objects, user=request.user, public_id=public_id)
    return render(request, "cvs/partials/cv_status.html", {
        "cv": cv_upload
    })
