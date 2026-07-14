from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from allauth.account.views import EmailView

from apps.accounts.services.email_identity import EmailIdentityService


class SafeEmailView(EmailView):
    """Keep allauth's ownership rules while normalizing integrity failures."""

    def form_valid(self, form):
        try:
            with EmailIdentityService.locked_available_identity(
                form.cleaned_data["email"],
                current_user=self.request.user,
            ):
                return super().form_valid(form)
        except (IntegrityError, ValidationError):
            form.add_error("email", EmailIdentityService.ERROR_MESSAGE)
            return self.form_invalid(form)

    def _action_primary(self, request, *args, **kwargs):
        email_address = self._get_email_address(request)
        if not email_address:
            return None
        try:
            with EmailIdentityService.locked_available_identity(
                email_address.email,
                current_user=request.user,
            ):
                return super()._action_primary(request, *args, **kwargs)
        except (IntegrityError, ValidationError):
            messages.error(request, EmailIdentityService.ERROR_MESSAGE)
            return None

# Create your views here.
