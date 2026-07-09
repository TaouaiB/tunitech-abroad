from dataclasses import dataclass

from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model


@dataclass(frozen=True)
class OAuthLinkDecision:
    user: object | None = None
    unsafe_reason: str = ""

    @property
    def should_link(self) -> bool:
        return self.user is not None and not self.unsafe_reason

    @property
    def is_unsafe_collision(self) -> bool:
        return bool(self.unsafe_reason)


class OAuthAccountLinkingService:
    @classmethod
    def decide_verified_email_link(cls, *, email: str, provider_email_verified: bool) -> OAuthLinkDecision:
        normalized_email = (email or "").strip()
        if not normalized_email:
            return OAuthLinkDecision()

        User = get_user_model()
        try:
            user = User.objects.get(email__iexact=normalized_email)
        except User.DoesNotExist:
            return OAuthLinkDecision()

        if not provider_email_verified:
            return OAuthLinkDecision(unsafe_reason="provider_email_unverified")

        local_email_verified = EmailAddress.objects.filter(
            user=user,
            email__iexact=normalized_email,
            verified=True,
        ).exists()
        if not local_email_verified:
            return OAuthLinkDecision(unsafe_reason="local_email_unverified")

        return OAuthLinkDecision(user=user)
