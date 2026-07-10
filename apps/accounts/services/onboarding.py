from django.shortcuts import resolve_url
from django.urls import reverse


ONBOARDING_REQUIRED_SESSION_KEY = "tuniatlas_onboarding_required"


class OnboardingRedirectService:
    @classmethod
    def mark_required(cls, request) -> None:
        if request is not None and hasattr(request, "session"):
            request.session[ONBOARDING_REQUIRED_SESSION_KEY] = True

    @classmethod
    def clear_if_complete(cls, request) -> None:
        if request is None or not hasattr(request, "session"):
            return
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated and cls._has_active_cv(user) and cls._profile_complete(user):
            request.session.pop(ONBOARDING_REQUIRED_SESSION_KEY, None)

    @classmethod
    def get_login_redirect_url(cls, request, default_url: str | None = None) -> str:
        user = getattr(request, "user", None)
        if user is None or not user.is_authenticated:
            return resolve_url(default_url or "/jobs/")

        if not user.has_usable_password():
            return reverse("account_set_password")

        if request.session.get(ONBOARDING_REQUIRED_SESSION_KEY):
            return cls.get_next_onboarding_url(user)

        return resolve_url(default_url or "/jobs/")

    @classmethod
    def get_signup_redirect_url(cls, request) -> str:
        cls.mark_required(request)
        return cls.get_login_redirect_url(request, default_url=reverse("dashboard:cv"))

    @classmethod
    def get_password_set_redirect_url(cls, request) -> str:
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated and request.session.get(ONBOARDING_REQUIRED_SESSION_KEY):
            return cls.get_next_onboarding_url(user)
        return reverse("jobs:list")

    @classmethod
    def get_next_onboarding_url(cls, user) -> str:
        if not cls._has_active_cv(user):
            return reverse("dashboard:cv")
        if not cls._profile_complete(user):
            return reverse("dashboard:profile")
        return reverse("jobs:list")

    @classmethod
    def should_redirect_request(cls, request) -> str | None:
        user = getattr(request, "user", None)
        if user is None or not user.is_authenticated:
            return None

        path = request.path
        account_allowed_prefixes = (
            "/accounts/password/set/",
            "/accounts/logout/",
            "/accounts/password/change/",
            "/accounts/password/reset/",
            "/accounts/password/reset/done/",
            "/accounts/password/reset/key/",
            "/accounts/confirm-email/",
        )
        if any(path.startswith(prefix) for prefix in account_allowed_prefixes):
            return None

        if not user.has_usable_password():
            return reverse("account_set_password")

        onboarding_allowed_prefixes = (
            "/dashboard/cv/",
            "/dashboard/profile/",
        )
        if any(path.startswith(prefix) for prefix in onboarding_allowed_prefixes):
            return None

        if request.session.get(ONBOARDING_REQUIRED_SESSION_KEY):
            target = cls.get_next_onboarding_url(user)
            if target != reverse("jobs:list"):
                return target
            request.session.pop(ONBOARDING_REQUIRED_SESSION_KEY, None)
        return None

    @staticmethod
    def _has_active_cv(user) -> bool:
        from apps.cvs.models import CVUpload

        return CVUpload.objects.filter(user=user, is_active=True).exists()

    @staticmethod
    def _profile_complete(user) -> bool:
        from apps.profiles.services.completeness import ProfileCompletenessService

        profile = getattr(user, "candidate_profile", None)
        if not profile:
            return False
        report = ProfileCompletenessService.get_report(profile)
        score = report.get("score", 0)
        return isinstance(score, int) and score >= 50
