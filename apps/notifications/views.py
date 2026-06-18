from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import Http404
from .forms import EmailPreferenceForm
from .services.preferences import EmailPreferenceService
from .models import EmailPreference

@login_required
def email_preferences_view(request):
    pref, _ = EmailPreference.objects.get_or_create(user=request.user)
    
    if request.method == "POST":
        form = EmailPreferenceForm(request.POST)
        if form.is_valid():
            EmailPreferenceService.update_preferences(request.user, form.cleaned_data)
            messages.success(request, "Email preferences updated successfully.")
            return redirect("dashboard:email_preferences")
    else:
        form = EmailPreferenceForm(initial={
            "weekly_digest_enabled": pref.weekly_digest_enabled,
            "product_updates_enabled": pref.product_updates_enabled,
            "cv_analysis_email_enabled": pref.cv_analysis_email_enabled,
        })
        
    return render(request, "dashboard/email_preferences.html", {"form": form})

def unsubscribe_view(request, token):
    token = str(token)

    if request.method != "POST":
        if not EmailPreferenceService.token_exists(token):
            raise Http404("Invalid unsubscribe token")
        return render(request, "notifications/unsubscribe_confirm.html", {"token": token})

    result = EmailPreferenceService.unsubscribe(token)
    
    if not result.success:
        if result.error == "Invalid token" or result.error == "Invalid token format":
            raise Http404("Invalid unsubscribe token")
        else:
            raise Http404("Invalid request")
            
    return render(request, "notifications/unsubscribe_success.html")
