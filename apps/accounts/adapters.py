from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib import messages
from django.shortcuts import redirect

from apps.accounts.services.account_provisioning import AccountProvisioningService
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


from django.urls import reverse
from allauth.account.adapter import DefaultAccountAdapter


class TuniTechAccountAdapter(DefaultAccountAdapter):
    """
    Redirect users without a usable password to the password set page after login.
    Otherwise, respect the standard LOGIN_REDIRECT_URL.
    """

    def get_login_redirect_url(self, request):
        user = getattr(request, "user", None)
        if user is not None and not user.has_usable_password():
            return reverse("account_set_password")
        return super().get_login_redirect_url(request)
