from django.shortcuts import render, redirect
from django.contrib import messages
from apps.core.services.homepage import HomepageService
from apps.core.forms import ContactForm
from apps.core.services.contact import ContactService

def home(request):
    latest_jobs = HomepageService.latest_public_jobs()
    return render(request, "core/home.html", {"latest_jobs": latest_jobs})

def about(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            ContactService.submit_contact_message(
                form=form,
                user=request.user if request.user.is_authenticated else None,
                request=request
            )
            messages.success(request, "Message envoyé avec succès. Nous vous répondrons bientôt.")
            return redirect("core:about")
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = ContactForm()

    return render(request, "core/about.html", {"form": form})
