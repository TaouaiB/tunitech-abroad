from django.shortcuts import redirect, resolve_url
from django.urls import reverse


class NoPasswordRedirectMiddleware:
    """
    Redirect authenticated users without a usable password to the password set page.
    Skip the redirect if the user is on an allowed page (password set, logout, password reset flow).
    """
    ALLOWED_URLS = {
        "/accounts/password/set/",
        "/accounts/logout/",
        "/accounts/password/change/",
        "/accounts/password/reset/",
        "/accounts/password/reset/done/",
        "/accounts/password/reset/key/",
        "/accounts/confirm-email/",
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated and not user.has_usable_password():
            path = request.path
            if not any(path.startswith(prefix) for prefix in self.ALLOWED_URLS):
                return redirect(reverse("account_set_password"))
        return self.get_response(request)
