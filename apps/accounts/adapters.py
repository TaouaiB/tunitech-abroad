from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

from apps.accounts.services.account_provisioning import AccountProvisioningService


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
