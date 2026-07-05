# Phase 16H-R2 Auth POST Repair Codex Review Report

Verdict: **APPROVED**

## Root Cause Confirmation
Confirmed.

The blocker was a client-side auth form interception issue:

- Real login/signup forms used `data-validate`.
- The prototype submit handler could prevent valid POST submission.
- Auth forms previously carried fake success strings through `data-success`, allowing a success toast to appear without verified authentication.

Current repair state:

- Login/signup forms no longer include fake auth `data-success`.
- Empty required fields are still handled by the prototype validator with red fields and a bad toast.
- Valid POST forms with `method="post"` and `action` now submit naturally to allauth.
- Wrong credentials reach allauth, render server errors, and do not show signed-in/success toast.

## Files Reviewed
- `templates/account/login.html`
- `templates/account/signup.html`
- `static/js/v16_ui.js`
- `apps/accounts/tests.py`
- `docs/phases/post_launch/phase_16h_ui_ux_overhaul/phase_16h_r2_auth_post_repair_report.md`
- `docs/phases/post_launch/phase_16h_ui_ux_overhaul/phase_16h_r2_auth_post_repair_screenshots/`

Note: `config/urls.py` remains in the active R2 working diff from the original method-aware signup GET redirect. It was not part of the post-repair JS/template fix, but it supports the required signup route behavior verified in this review.

## Auth POST Behavior Verdict
Approved.

Verified by diff inspection, screenshots, and tests:

- No fake auth `data-success` remains on login/signup forms.
- Valid POST forms are not prevented by JS.
- Wrong login credentials produce allauth server errors and do not authenticate the user.
- Correct login credentials still redirect to `/dashboard/`.
- Invalid signup POST reaches allauth and renders errors instead of a fake account-created success.
- Signup GET still redirects to `/accounts/login/?panel=signup`.

Regression tests added in `apps/accounts/tests.py`:

- `test_auth_templates_do_not_include_fake_success_toasts`
- `test_wrong_email_password_login_does_not_authenticate`
- `test_invalid_signup_post_reaches_allauth_without_fake_success`

## Browser Proof Verdict
Approved.

Inspected proof directory:

```text
docs/phases/post_launch/phase_16h_ui_ux_overhaul/phase_16h_r2_auth_post_repair_screenshots/
```

Required artifacts exist:

- `auth_post_repair_contact_sheet.png`
- `login_empty_required_error.png`
- `login_wrong_credentials_server_error.png`
- `signup_invalid_server_error.png`
- `login_correct_credentials_redirect_proof.txt`

Visual findings:

- Empty login fields show red validation copy and a bad toast.
- Wrong credentials show the allauth server error with no signed-in/success toast.
- Signup invalid proof shows error handling and no fake account-created success.

## Tests and Checks Result
Passed.

```text
python manage.py check --settings=config.settings.local
System check identified no issues (0 silenced).

python manage.py makemigrations --check --dry-run --settings=config.settings.local
No changes detected

python manage.py test apps.accounts apps.core --settings=config.settings.local
Ran 105 tests in 35.499s
OK

python manage.py test --settings=config.settings.local
Ran 646 tests in 107.070s
OK

npm run css:build
Done in 979ms

git diff --check
Clean
```

Hard grep checks:

```text
No model/migration/service/task/view/settings/form/env hits.
No OpenRouter, France Travail live API, HTTP client, notification feed, websocket, or scoring hits.
No CV consent reintroduction hits.
No auth fake success data-success hits in templates/account or static/js.
```

Note: `npm run css:build` emitted the existing Browserslist `caniuse-lite is outdated` advisory. The build completed successfully.

## Required Repairs
None remaining.
