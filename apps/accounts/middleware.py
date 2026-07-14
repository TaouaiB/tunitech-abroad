from django.shortcuts import redirect

from apps.accounts.services.onboarding import OnboardingRedirectService


class NoPasswordRedirectMiddleware:
    """
    Redirect authenticated users without a usable password to the password set page.
    Skip the redirect if the user is on an allowed page (password set, logout, password reset flow).
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        redirect_url = OnboardingRedirectService.should_redirect_request(request)
        if redirect_url:
            return redirect(redirect_url)
        return self.get_response(request)
