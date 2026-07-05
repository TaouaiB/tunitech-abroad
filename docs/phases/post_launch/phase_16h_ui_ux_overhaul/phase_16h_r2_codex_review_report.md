# Phase 16H-R2 Codex Review Report

Verdict: **APPROVED**

## Files Reviewed
- `docs/design/phase_16h/prototype_full_v16/auth.html`
- `docs/design/phase_16h/prototype_full_v16/notifications.html`
- `docs/design/phase_16h/prototype_full_v16/failure-states.html`
- `templates/account/login.html`
- `templates/account/signup.html`
- `templates/base.html`
- `config/urls.py`
- `static/js/v16_ui.js`
- `apps/accounts/tests.py`
- `docs/phases/post_launch/phase_16h_ui_ux_overhaul/phase_16h_r2_screenshots/`

## Scope Verdict
Approved. Changed files are inside the R2 allowed list:

- `apps/accounts/tests.py`
- `config/urls.py`
- `static/js/v16_ui.js`
- `templates/account/login.html`
- `templates/account/signup.html`
- `docs/phases/post_launch/phase_16h_ui_ux_overhaul/phase_16h_r2_screenshots/django_login_invalid_desktop_1440.png`

No unrelated page bodies or backend domains were changed.

## Route Behavior Verdict
Approved.

Manual Django client probe with `SERVER_NAME='localhost'`:

```text
GET /accounts/login/ -> 200
GET /accounts/login/?panel=signup -> 200
GET /accounts/signup/ -> 302 /accounts/login/?panel=signup
POST /accounts/signup/ -> 200
```

The method-aware signup wrapper redirects only GET/HEAD and delegates POST to allauth, so signup POST is not blocked by the redirect.

## Visual Fidelity Verdict
Approved.

The auth templates use the prototype auth DOM/classes as the base:

- `.auth-v16`
- `.section`
- `.shell.hero-grid`
- `.hero-card`
- `.hero-card.soft`
- `.page-title.small`
- `.h2`
- `.grid`
- `.grid.grid-2`
- `.field`
- `.input`
- `.btn.primary.full`
- `.btn.secondary.full`

Login and signup are both present on canonical `/accounts/login/`. `?panel=signup` visually prioritizes the signup panel by swapping card order and softness. Mobile stacking is covered by the existing `.hero-grid` responsive CSS and verified in the screenshot set.

## Allauth Preservation Verdict
Approved.

- Provider buttons use `{% provider_login_url 'google' process='login' %}` and `{% provider_login_url 'github' process='login' %}`.
- Login form posts to `{% url 'account_login' %}`.
- Signup form posts to `{% url 'account_signup' %}`.
- CSRF tokens are present.
- Redirect hidden field is preserved.
- Server-side form errors render in `.field.has-error` / `.error` blocks.
- Signup failure rendering is preserved through `templates/account/signup.html`.

## Header Behavior Verdict
Approved.

Anonymous header has one auth CTA only: `Connexion`. No separate `Create account` / `Créer un compte` header button is present.

## JS/CSS Verdict
Approved after tiny R2 repair.

Repairs made during review:

- `static/js/v16_ui.js`: valid real POST forms now submit normally instead of being intercepted by a success toast.
- `static/js/v16_ui.js`: `form.noValidate = true` is set for `data-validate` forms so the prototype validator can show red fields and toast for empty required fields.
- `templates/account/login.html` and `templates/account/signup.html`: trailing whitespace removed.
- `docs/.../django_login_invalid_desktop_1440.png`: regenerated after the validator repair; it now shows red validation text and the bad toast.

Language toggle behavior remains supported through `data-i18n` hooks and the R1 `applyLanguage` path. Auth headings, buttons, validation copy, and placeholders participate in the EN/FR toggle.

## Consent Verdict
Approved.

Consent grep returned clean:

```bash
grep -RInE 'consent_accepted|CVConsentForm|Consentement au traitement|I accept private CV analysis|J.accepte l.analyse' apps templates || true
```

No CV consent UI or form code was reintroduced.

## Architecture Safety Verdict
Approved.

Architecture greps returned no relevant hits:

```bash
git diff --name-only | grep -E 'models.py|migrations/|services/|tasks.py|views.py|config/settings|forms.py|\.env$' || true
git diff | grep -Ei 'OpenRouter|francetravail|France Travail|requests\.|httpx|notification feed|websocket|score.*=|algorithm|formula' || true
git diff | grep -Ei 'cv\.file\.url|file\.url|MEDIA_URL|private_media|CVUpload\.all_objects' || true
```

No model, migration, service, task, settings, form, CV media, LLM, France Travail, notification feed, websocket, or scoring changes were introduced.

## Screenshot Review Verdict
Approved after repair.

Required screenshot artifacts exist:

- `auth_contact_sheet.png`
- `prototype_auth_desktop_1440.png`
- `django_login_desktop_1440.png`
- `django_login_mobile_390.png`
- `django_signup_panel_desktop_1440.png`
- `django_signup_panel_mobile_390.png`
- `django_login_en_desktop_1440.png`
- `django_login_invalid_desktop_1440.png`

The invalid-form screenshot was recaptured during review because the original proof did not show a true invalid required-field state.

## Tests and Checks Result
Passed.

```text
python manage.py check --settings=config.settings.local
System check identified no issues (0 silenced).

python manage.py makemigrations --check --dry-run --settings=config.settings.local
No changes detected

python manage.py test apps.accounts apps.core --settings=config.settings.local
Ran 102 tests in 33.032s
OK

python manage.py test --settings=config.settings.local
Ran 643 tests in 227.249s
OK

npm run css:build
Done in 1913ms

git diff --check
Clean
```

Note: `npm run css:build` emitted the existing Browserslist `caniuse-lite is outdated` advisory, but the build completed successfully.

## Required Repairs
None remaining.
