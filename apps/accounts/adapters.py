from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib import messages
from django.shortcuts import redirect
from django.shortcuts import resolve_url
from allauth.account.adapter import DefaultAccountAdapter

from apps.accounts.services.account_provisioning import AccountProvisioningService
from apps.accounts.services.onboarding import OnboardingRedirectService
from apps.accounts.services.oauth_linking import OAuthAccountLinkingService


class TuniTechSocialAccountAdapter(DefaultSocialAccountAdapter):
    TRUSTED_EMAIL_AUTH_PROVIDERS = {"google", "github"}

    def can_authenticate_by_email(self, login, email: str) -> bool:
        provider_id = getattr(getattr(login, "account", None), "provider", "")
        return provider_id in self.TRUSTED_EMAIL_AUTH_PROVIDERS

    def is_email_verified(self, provider, email) -> bool:
        provider_id = getattr(provider, "id", "")
        if provider_id in self.TRUSTED_EMAIL_AUTH_PROVIDERS:
            return True
        return super().is_email_verified(provider, email)

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form=form)
        AccountProvisioningService.provision_new_user(user)
        OnboardingRedirectService.mark_required(request)
        return user

    def pre_social_login(self, request, sociallogin):
        if sociallogin.is_existing:
            return

        if not sociallogin.email_addresses:
            return

        email_address = sociallogin.email_addresses[0]
        decision = OAuthAccountLinkingService.decide_verified_email_link(
            email=email_address.email,
            provider_email_verified=email_address.verified,
        )

        if decision.should_link:
            sociallogin.connect(request, decision.user)
            return

        if decision.is_unsafe_collision:
            messages.error(
                request,
                "Connexion sociale non liée automatiquement : vérifiez d'abord votre adresse email locale.",
            )
            raise ImmediateHttpResponse(redirect("account_login"))


class TuniTechAccountAdapter(DefaultAccountAdapter):
    """Centralize post-auth onboarding redirects."""

    def save_user(self, request, user, form, commit=True):
        user = super().save_user(request, user, form, commit=commit)
        AccountProvisioningService.provision_new_user(user)
        OnboardingRedirectService.mark_required(request)
        return user

    def get_login_redirect_url(self, request):
        return OnboardingRedirectService.get_login_redirect_url(
            request,
            default_url=resolve_url(super().get_login_redirect_url(request)),
        )

    def get_signup_redirect_url(self, request):
        return OnboardingRedirectService.get_signup_redirect_url(request)

    def get_password_change_redirect_url(self, request):
        if request.session.get("tuniatlas_onboarding_required"):
            return OnboardingRedirectService.get_password_set_redirect_url(request)
        return super().get_password_change_redirect_url(request)
