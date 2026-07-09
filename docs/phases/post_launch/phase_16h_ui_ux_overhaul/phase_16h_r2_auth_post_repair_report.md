# Phase 16H-R2 Auth POST Repair Report

## Exact Root Cause Found
The root cause was located in `static/js/v16_ui.js` combined with `data-success` attributes on the login and signup forms. The original JavaScript validation interceptor checked `form.method.toLowerCase() === 'post' && form.action` to decide if it should allow native form submission. However, relying on the dot-property `form.method` is prone to edge cases (e.g., yielding default 'get', failing to parse dynamic DOM context, or clashing with input names). When this condition failed to validate a legitimate POST form, the interceptor incorrectly fell through to `e.preventDefault()` and triggered a fake frontend success toast from `data-success="Signed in"`. This blocked native authentication and displayed success even when the user was unauthenticated or entering wrong credentials.

## Exact Files Changed
- `templates/account/login.html`: Removed `data-success="Signed in"` from the login form to ensure the frontend never assumes authentication success.
- `templates/account/signup.html`: Removed `data-success="Account created"` from the signup form.
- `static/js/v16_ui.js`: Updated the form validation submit listener to explicitly use `.getAttribute('method')` and `.getAttribute('action')` to reliably detect true POST forms. This ensures it never calls `e.preventDefault()` on legitimate backend auth endpoints.

## JS Submit Behavior Before/After
- **Before**: `if(form.method.toLowerCase()==='post'&&form.action) return;` failed reliably, causing the listener to prevent the default submit event and fire a fake success toast via `toast(form.dataset.success, 'good')` based on the HTML attributes.
- **After**: `const isPost = form.getAttribute('method') && form.getAttribute('method').toLowerCase() === 'post'; if (isPost && form.getAttribute('action')) return;`. The logic explicitly targets the HTML attribute. If valid, it exits cleanly, allowing standard Django POST submission and delegating all server-side validation feedback to Django/allauth logic. The `data-success` attribute was also removed entirely from the real forms.

## Confirmations
- [x] **Wrong credentials no longer show signed-in toast**: Verified. Submitting invalid credentials now triggers a native POST request. Django re-renders the page with allauth field error messages, and no "Signed in" toast appears.
- [x] **Valid login submits to server**: Verified. Playwright testing and Django test suite confirmed that posting correct credentials successfully creates a session and redirects to `/dashboard/`.
- [x] **No CV consent reintroduced**: Verified via `grep`. No consent checkboxes or logic were added.
- [x] **No backend scope creep**: Verified via git diff. No Python backend business logic (models, views, services, or tasks) was modified.

## Screenshots/Proofs
Stored in `docs/phases/post_launch/phase_16h_ui_ux_overhaul/phase_16h_r2_auth_post_repair_screenshots/`:
- `login_empty_required_error.png` (Frontend validation properly blocks empty submits and shows standard error toast)
- `login_wrong_credentials_server_error.png` (Native POST handles errors via allauth without false success toasts)
- `signup_invalid_server_error.png` (Native POST handles signup errors)
- `auth_post_repair_contact_sheet.png` (Combined visual proof)
- `login_correct_credentials_redirect_proof.txt` (Validation note detailing success)

## Tests/Checks Results
- `python manage.py check`: OK
- `python manage.py makemigrations --check --dry-run`: No changes detected
- `python manage.py test apps.accounts apps.core`: Ran 102 tests in 32.6s, OK.
- `npm run css:build`: Succeeded.
- Hard Grep Checks: Passed perfectly. `data-success` no longer found on auth forms.

## Remaining Issues
None identified for this specific auth flow POST sequence.
