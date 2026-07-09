# Phase 16H-R2 Auth Exact Port Report

## Prototype Files Inspected
- `docs/design/phase_16h/prototype_full_v16/auth.html` (Primary auth layout source)

## Exact Files Changed
- `config/urls.py` (Added `signup_redirect_wrapper` for GET/HEAD routing on `/accounts/signup/`)
- `templates/account/login.html` (Overwritten with complete prototype layout)
- `templates/account/signup.html` (Overwritten with complete prototype layout, default ordered for signup context)
- `apps/accounts/tests.py` (Updated `test_signup_page_status_code` to expect 302 instead of 200)

## Auth Route Behavior
- **`/accounts/login/` (GET)**: Renders the unified auth layout. Both login and signup forms are present. The login panel is visually primary.
- **`/accounts/login/?panel=signup` (GET)**: Renders the unified auth layout. The signup panel is visually primary using `style="order: 1"`.
- **`/accounts/signup/` (GET)**: Redirects via 302 to `/accounts/login/?panel=signup`.
- **`/accounts/signup/` (POST)**: Handled directly by allauth view. If validation fails, it renders the unified auth layout using `signup.html` with the signup form and its errors, making the signup panel primary.

## Template Mapping Table

| Prototype Structure | Django Template Structure (`login.html` & `signup.html`) |
| :--- | :--- |
| `<div class="hero-card">` (Login Form) | Login Card, includes allauth `provider_login_url` tags for OAuth. |
| `<form class="grid">` (Login fields) | Uses `name="login"` and `name="password"` as expected by allauth. Field validation binds `form.login.errors` and `form.password.errors`. |
| `<div class="hero-card soft">` (Signup Form) | Signup Card, injected with inline order style to swap visual priority depending on `request.GET.panel` or fallback context. |
| `<form class="grid">` (Signup fields) | Uses `name="first_name"`, `name="last_name"`, `name="email"`, `name="password1"`, and `name="password2"`. Binds `form.email.errors`, etc., explicitly for robust rendering. |
| Server-side errors | Hooked `form.non_field_errors` directly into the prototype's `.error` and `.has-error` class logic. |

## Intentional Differences from Prototype
- Added Django Template conditionals (`{% if request.GET.panel == 'signup' %}`) and `style="order: 2;"` / `style="order: 1;"` inline attributes. The prototype did not support query param routing out of the box, so we implemented this inline to ensure the correct form is visually primary without altering CSS classes permanently.
- Added `name` attributes to input fields (e.g., `name="email"`, `name="password1"`) that match allauth validation requirements.
- Hardcoded `value="{{ form.field.value }}"` in inputs so user submissions persist during validation failures instead of clearing the fields.

## Screenshots
Screenshots captured using Playwright and saved in `phase_16h_r2_screenshots/`:
- `prototype_auth_desktop_1440.png`
- `django_login_desktop_1440.png`
- `django_login_mobile_390.png`
- `django_signup_panel_desktop_1440.png`
- `django_signup_panel_mobile_390.png`
- `django_login_en_desktop_1440.png`
- `django_login_invalid_desktop_1440.png`
- `auth_contact_sheet.png`
- `signup_get_redirect_proof.txt`

## Tests and Checks Results
- `python manage.py check`: Passed cleanly (0 silenced).
- `python manage.py makemigrations --check --dry-run`: No changes detected.
- `python manage.py test apps.accounts apps.core`: Passed successfully (102 tests).
- `npm run css:build`: No new custom classes needed.
- `git diff --check`: Clean.

## Confirmations
- [x] **Allauth login/signup/social preserved**: Yes, original form logic, CSRF tokens, and `provider_login_url` logic are preserved.
- [x] **One header auth CTA only**: Checked `base.html` and verified it only has "Connexion".
- [x] **No CV consent reintroduced**: Confirmed no `consent_accepted` inputs were added back into the template.
- [x] **No backend scope creep**: Only updated `config/urls.py` with a lightweight, method-aware redirect. No models, tasks, or views were modified.

## Remaining Issues Deferred
- Social Auth provider API keys/configuration handling is still bound to the base `.env` configuration.
- Auth validation feedback relies mostly on standard allauth POST validation. Client-side JS validation logic (`data-validate`) from `v16_ui.js` operates gracefully alongside the server validation.
