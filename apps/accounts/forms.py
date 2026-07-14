from allauth.account.forms import AddEmailForm
from django import forms

from apps.accounts.services.email_identity import EmailIdentityService


class AccountNameForm(forms.Form):
    first_name = forms.CharField(max_length=150, required=False, strip=True)
    last_name = forms.CharField(max_length=150, required=False, strip=True)

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields["first_name"].widget.attrs.update({"class": "input", "autocomplete": "given-name"})
        self.fields["last_name"].widget.attrs.update({"class": "input", "autocomplete": "family-name"})


class SafeAddEmailForm(AddEmailForm):
    def clean_email(self):
        email = super().clean_email()
        EmailIdentityService.validate_available(email, current_user=self.user)
        return email
