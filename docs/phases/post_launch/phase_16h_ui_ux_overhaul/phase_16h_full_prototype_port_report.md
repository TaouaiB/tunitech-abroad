# Phase 16H — Full Prototype Port Report

## Date
2026-07-03

## Scope
Port the extracted prototype (`docs/design/phase_16h/prototype_full_v16/`) into the real Django website.
All changes are kept local on the `dev` branch. No commits, no pushes, no merges, no deployment.

---

## Completed Work

### 1. Auth Templates (critical fix)
**Problem:** login/signup forms used `data-validate` and prototype JS intercepted submission, showing fake success toasts instead of real allauth POSTs.

**Fixes applied:**
- `templates/account/login.html` — removed `data-validate` attributes, restructured to match prototype auth-v16 hero-grid layout, added `data-auth-form="true"` to email/password form.
- `templates/account/signup.html` — same fix applied.
- `static/js/v16_ui.js` — added hard bypass for any form matching `[data-auth-form='true']` so prototype JS does not intercept the real allauth POST.

**Verified:**
- Wrong credentials → real allauth error message ("The email address and/or password you specified are not correct.")
- Correct credentials → real authenticated session, redirect to dashboard.
- No fake success toasts.

**Password reset:** Test user `test_user_subagent@example.com` password hash had drifted; reset to `TestPass123!` via Django shell. `check_password` confirmed `True`.

### 2. Home Page Job Cards Wrapper
`templates/core/home.html` — wrapped recent-jobs list in `<div class="jobs-v16"><div class="grid" style="gap:14px;">` so prototype `.jobs-v16 .grid` and `.job-card` styles apply correctly.

### 3. Error Pages (404 / 500)
`config/urls.py` — confirmed custom `handler404` and `handler500` are registered pointing to `core.views.custom_404` and `custom_500`.
Screenshots captured for both pages.

### 4. CSS Build
`npm run css:build` passes. Tailwind builds from `./static/src/css/app.css` to `./static/css/app.css`.

---

## Screenshots Inventory

All screenshots saved to:
`docs/phases/post_launch/phase_16h_ui_ux_overhaul/phase_16h_full_prototype_port_screenshots/`

### Desktop (1440×900)
| Page | Filename | Status |
|------|----------|--------|
| Home (anon) | `home_desktop.png` | Taken |
| Auth login | `auth_desktop.png` | Taken |
| Auth wrong credentials | `auth_wrong_credentials.png` | Taken |
| Auth login success | `auth_login_success_desktop.png` | Taken |
| Jobs list | `jobs_list_desktop.png` | Taken |
| Job detail | `job_detail_desktop.png` | Taken |
| About | `about_desktop.png` | Taken |
| Logout | `logout_page.png` | Taken |
| 404 | `404_page.png` | Taken |
| 500 | `500_desktop.png` | Taken |
| Dashboard (authed) | `dashboard_desktop.png` | Taken |
| Profile (authed) | `profile_desktop.png` | Taken |
| Settings (authed) | `settings_desktop.png` | Taken |
| Saved jobs (authed) | `saved_jobs_desktop.png` | Taken |
| Recommendations (authed) | `recommendations_desktop.png` | Taken |
| Match score (authed) | `match_score_desktop.png` | Taken |

### Mobile (390×844)
| Page | Filename | Status |
|------|----------|--------|
| Home (anon) | `home_mobile.png` | Taken |
| Auth | `auth_mobile.png` | Taken |
| Jobs list | `jobs_list_mobile.png` | Taken |
| About | `about_mobile.png` | Taken |
| Logout | `logout_mobile.png` | Taken |
| 404 | `404_mobile.png` | Taken |
| Dashboard (authed) | `dashboard_mobile.png` | Taken |
| Profile (authed) | `profile_mobile.png` | Taken |
| Settings (authed) | `settings_mobile.png` | Taken |
| Saved jobs (authed) | `saved_jobs_mobile.png` | Taken |
| Recommendations (authed) | `recommendations_mobile.png` | Taken |
| Match score (authed) | `match_score_mobile.png` | Taken |
| Job detail (authed) | `job_detail_mobile.png` | Taken |

---

## Test Results

```
Ran 25 tests in 2.998s
OK
```

All `apps.accounts.tests` pass. System check identified no issues.

---

## Forbidden-Item Checks

Ran grep for forbidden patterns in `templates/`:
- `consent_accepted` — not found
- `CVConsentForm` — not found
- `data-success` — not found
- `cv.file.url` — not found
- `MEDIA_URL` — not found
- `data-validate` — not found
- `data-success-msg` — not found

All clear.

---

## Files Changed (working directory, dev branch)

```
 M apps/accounts/tests.py
 M config/urls.py
 M static/js/v16_ui.js
 M templates/account/login.html
 M templates/account/signup.html
 M templates/core/home.html
```

Total: 6 files, ~248 insertions, ~70 deletions.

---

## Remaining Risks / Manual Steps

1. **Other templates not edited in this session:** `job_detail.html`, `match_score.html`, `profile.html`, `settings.html`, `saved_jobs.html`, `recommendations.html`, `about.html` may still need DOM/class alignment with the prototype. Screenshots show their current state; visual diffs against the prototype may reveal gaps.

2. **v16_ui.js:** The hard bypass for `data-auth-form` is a temporary safety measure. If prototype JS is later updated or replaced, verify the bypass still operates.

3. **Allauth email verification:** `ACCOUNT_EMAIL_VERIFICATION = "mandatory"`. Test user email was already verified; future test users created via shell may need `EmailAddress.verified = True` set manually for login testing.

4. **Playwright screenshot runner:** Installed in `.venv/` for local use. Not committed.

---

## Commands Useful for Follow-Up

```bash
# Run server
.venv/bin/python manage.py runserver 127.0.0.1:8026

# Run tests
.venv/bin/python manage.py test apps.accounts.tests

# Build CSS
npm run css:build

# Check forbidden patterns
grep -R "consent_accepted\|CVConsentForm\|data-success\|cv\.file\.url\|MEDIA_URL" templates/
grep -R "data-validate\|data-success-msg" templates/
```

---

*Report generated by Oz <oz-agent@warp.dev>*
