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
from apps.privacy.services.account_deletion import AccountDeletionService
from allauth.socialaccount.models import SocialAccount

@login_required
def dashboard_recommendations(request):
    result = RecommendationQueryService.get_dashboard_recommendations(request.user)
    if request.headers.get("HX-Request"):
        return render(request, "recommendations/partials/recommendation_list.html", {"result": result})
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

    active_cv = CVUpload.objects.filter(user=user, is_active=True).first()
    cv_data = {}
    if active_cv and hasattr(active_cv, 'parsed_data'):
        pd = active_cv.parsed_data
        cv_data = {
            'full_name': pd.extracted_name,
            'phone': pd.extracted_phone,
            'location': pd.extracted_location,
            'linkedin_url': pd.extracted_linkedin_url,
            'github_url': pd.extracted_github_url,
            'portfolio_url': pd.extracted_portfolio_url,
            'years_experience': pd.estimated_years_experience,
        }

    initial_data = {}
    for key, val in cv_data.items():
        if val and not getattr(profile, key, None):
            initial_data[key] = val

    if request.method == "POST":
        from apps.profiles.forms import ProfileForm
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            ProfileUpdateService.update_profile(user, form.cleaned_data)
            messages.success(request, "Profile updated successfully.")
            return redirect("dashboard:profile")
    else:
        from apps.profiles.forms import ProfileForm
        form = ProfileForm(instance=profile, initial=initial_data)

    # Make cv_data accessible by field name in template
    suggestions = {}
    for key, val in cv_data.items():
        if val and getattr(profile, key, None) != val:
            suggestions[key] = val

    from apps.profiles.services.completeness import ProfileCompletenessService
    missing_fields = []
    if profile:
        completeness_report = ProfileCompletenessService.get_report(profile)
        missing_fields = completeness_report["missing"] + completeness_report["invalid"]

    return render(request, "dashboard/profile.html", {
        "form": form,
        "profile": profile,
        "suggestions": suggestions,
        "missing_fields": missing_fields
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

@login_required
def dashboard_account(request):
    try:
        deletion_request = request.user.deletion_requests.filter(status__in=['pending', 'processing']).first()
    except Exception:
        deletion_request = None

    return render(request, "dashboard/account.html", {
        "deletion_request": deletion_request,
        "has_usable_password": request.user.has_usable_password(),
    })

@login_required
def dashboard_delete_account(request):
    if request.method == "POST":
        confirmation = request.POST.get("confirmation", "")
        if confirmation.strip().upper() == "DELETE":
            AccountDeletionService.request_deletion(request.user)
            from django.contrib.auth import logout
            logout(request)
            return redirect("core:home")
        else:
            messages.error(request, "Please type DELETE to confirm.")
            return redirect("dashboard:delete_account")

    return render(request, "dashboard/delete_account.html")

@login_required
def dashboard_connections(request):
    if request.method == "POST" and "disconnect_id" in request.POST:
        account_id = request.POST.get("disconnect_id")
        # Ensure it belongs to the user
        account_to_delete = SocialAccount.objects.filter(id=account_id, user=request.user).first()
        if account_to_delete:
            account_to_delete.delete()
            messages.success(request, f"Compte {account_to_delete.provider.capitalize()} déconnecté.")
        return redirect("dashboard:connections")

    social_accounts = SocialAccount.objects.filter(user=request.user)
    providers = {acc.provider: acc for acc in social_accounts}
    
    return render(request, "dashboard/connections.html", {
        "providers": providers
    })
