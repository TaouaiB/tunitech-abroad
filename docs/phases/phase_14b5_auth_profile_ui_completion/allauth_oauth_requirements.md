# Allauth and OAuth Requirements

## Required URL/page coverage

The agent must audit and style every user-facing route under `/accounts/`, especially:

- `/accounts/login/`
- `/accounts/signup/`
- `/accounts/logout/`
- `/accounts/password/reset/`
- `/accounts/password/reset/done/`
- password reset from key templates
- password reset from key done templates
- `/accounts/password/change/`
- `/accounts/password/set/`
- `/accounts/email/`
- `/accounts/confirm-email/`
- email confirmation with token template
- `/accounts/3rdparty/`
- social login confirmation page if present
- social signup page if present
- social account authentication error page
- provider connection/disconnection pages if present

The exact allauth URL names and template names may vary by installed django-allauth version. Discover them instead of guessing.

## Discovery commands

Run:

```bash
python manage.py shell --settings=config.settings.local -c "
from django.urls import get_resolver
for p in get_resolver().url_patterns:
    print(p)
"
```

Also inspect installed templates if needed:

```bash
python - <<'PY'
import allauth, pathlib
root = pathlib.Path(allauth.__file__).parent
for path in sorted(root.rglob('templates/**/*.html')):
    if 'account' in str(path) or 'socialaccount' in str(path):
        print(path)
PY
```

Override the relevant templates under:

```text
templates/account/
templates/socialaccount/
```

## Email templates

Customize the installed allauth email templates so emails never say `example.test`.

Required behavior:

- Product name: `TuniTech Abroad`
- Local development domain must use configured Site/domain, not default `example.test`.
- Verification email must contain a real confirmation link when it is actually a verification email.
- Duplicate-account email must not pretend it is a confirmation email.
- Copy must be clear in French or simple bilingual French-first copy.
- Do not include secrets or OAuth tokens.

Template names differ by allauth version. Discover and override the exact installed templates. Likely candidates include:

```text
account/email/email_confirmation_message.txt
account/email/email_confirmation_subject.txt
account/email/password_reset_key_message.txt
account/email/password_reset_key_subject.txt
account/email/account_already_exists_message.txt
account/email/account_already_exists_subject.txt
```

If the project uses older allauth template names, override those instead.

## Social provider connection UX

Add account settings section or page:

```text
/dashboard/account/connections/
```

It must show:

- Google connected/disconnected
- GitHub connected/disconnected
- connect button for missing provider
- disconnect button only if safe and user has another login method/provider
- set password CTA if user has unusable password
- explanation when provider is already connected

## Provider account switching

Important UX truth:

OAuth providers may reuse the currently logged-in provider browser session. The app cannot always force GitHub to show an account chooser.

Required UX:

- On connect buttons, label clearly:
  - `Connecter Google`
  - `Connecter GitHub`
  - `Changer de compte GitHub ? Déconnectez-vous de GitHub dans ce navigateur ou utilisez une fenêtre privée.`
- For Google, use account chooser behavior if supported by allauth/provider settings.
- For GitHub, do not promise account chooser if the provider does not support it reliably.
- After OAuth redirects back, show a Django message explaining whether the provider was connected, already connected, or refused.

## Provider data provisioning

Where available from provider extra data:

Google:
- email
- name
- given_name/family_name if useful
- picture URL

GitHub:
- email if provided/verified by allauth
- name
- login/username
- avatar_url
- html_url/profile URL

Apply through service layer, not in templates.

Suggested service location:

```text
apps/accounts/services/account_provisioning.py
```

Data rules:

- Do not overwrite user-confirmed full name silently.
- Fill empty profile fields from provider data.
- Store avatar as URL only if adding `avatar_url`; do not download external image.
- Never store access tokens in CandidateProfile.
- Add tests for Google-like and GitHub-like provider payloads.
