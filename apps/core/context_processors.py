from allauth.account.models import EmailAddress


def email_verification_banner(request):
    """
    Returns {'show_email_verification_banner': True} if the user is authenticated
    but their primary email is not verified.
    Returns False for anonymous users or fully verified users.
    """
    if not request.user.is_authenticated:
        return {"show_email_verification_banner": False}

    has_verified_primary = EmailAddress.objects.filter(
        user=request.user, primary=True, verified=True
    ).exists()

    return {"show_email_verification_banner": not has_verified_primary}


def onboarding_status(request):
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return {
            "has_active_cv": False,
            "profile_complete": False,
            "has_usable_password": False,
        }

    from apps.accounts.services.onboarding import OnboardingRedirectService

    return {
        "has_active_cv": OnboardingRedirectService._has_active_cv(user),
        "profile_complete": OnboardingRedirectService._profile_complete(user),
        "has_usable_password": user.has_usable_password(),
    }
