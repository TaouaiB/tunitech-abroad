from django.shortcuts import render

def privacy_policy_view(request):
    return render(request, "privacy/privacy_policy.html")

def terms_view(request):
    return render(request, "privacy/terms.html")
