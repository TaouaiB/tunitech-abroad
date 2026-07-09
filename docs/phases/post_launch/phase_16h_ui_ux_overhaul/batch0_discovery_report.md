# Phase 16H Batch 0 Discovery Report

## Status
CORRECTED / READY AFTER CODEX ISSUES ADDRESSED

## Codex Corrections Applied
- Acknowledged that anonymous Save UI is currently exposed on job-list cards via unconditional template inclusion (`templates/jobs/partials/job_card.html` including `save_button.html`).
- Acknowledged that job detail CTA logic needs explicit backend context support, not just template changes.
- Added omitted routes and templates for connections, account deletion, cv status, and feedback endpoints.
- Added omitted Batch 3 files including delete account and social connections tests.
- Expanded the risky tests list to include UI, copy, and auth-focused test modules that are likely to fail during UI overhaul.

## Files inspected
- `docs/phases/post_launch/phase_16h_ui_ux_overhaul/rules_lock.md`
- `docs/phases/post_launch/phase_16h_ui_ux_overhaul/page_mapping.md`
- `docs/phases/post_launch/phase_16h_ui_ux_overhaul/batch_plan.md`
- `docs/phases/post_launch/phase_16h_ui_ux_overhaul/review_checklist.md`
- `static/src/css/app.css`
- `templates/base.html`
- `templates/dashboard/saved_jobs.html`
- `templates/jobs/job_detail.html`
- `config/settings/base.py`
- App routing (`apps/core/urls.py`, `apps/jobs/urls.py`, `apps/dashboard/urls.py`, etc.)

## Route map
- **Core:** `/` (home)
- **Jobs:** `/jobs/` (list), `/jobs/<uuid>/` (detail), `/jobs/<uuid>/save|unsave/`
- **Dashboard:** `/dashboard/`, `/dashboard/profile/`, `/dashboard/cv/`, `/dashboard/cv/status/<uuid>/`, `/dashboard/recommendations/`, `/dashboard/saved-jobs/`, `/dashboard/account/`, `/dashboard/account/connections/`, `/dashboard/settings/delete-account/`, `/dashboard/settings/delete-account/done/`
- **Matching:** `/jobs/<uuid>/match/`, `/jobs/<uuid>/quick-match/`, `/dashboard/matches/`, `/dashboard/matches/<uuid>/`, `/dashboard/matches/<uuid>/feedback/`
- **Recommendations:** `/dashboard/recommendations/`, `/dashboard/recommendations/<uuid>/feedback/`
- **Notifications:** `/dashboard/email-preferences/`, `/email/unsubscribe/<token>/`
- **Privacy:** `/privacy/`, `/terms/`
- **Auth:** `/accounts/*` (django-allauth)

## Template map
- **Global:** `templates/base.html`, `templates/404.html`, `templates/500.html`
- **Core:** `templates/core/home.html`
- **Auth:** `templates/account/*.html`, `templates/socialaccount/*.html`
- **Jobs:** `templates/jobs/job_list.html`, `templates/jobs/job_detail.html`, `templates/jobs/partials/*.html`
- **Dashboard:** `templates/dashboard/*.html` (including `connections.html`, `delete_account.html`, `delete_account_done.html`)
- **Matching/Recommendations:** `templates/matching/*.html`, `templates/recommendations/*.html`

## Prototype-to-Django page mapping
- `index.html` -> `templates/jobs/job_list.html`
- `job-detail.html` -> `templates/jobs/job_detail.html`
- `match-score.html` -> `templates/matching/match_detail.html`
- `recommendations.html` -> `templates/dashboard/recommendations.html`
- `saved-jobs.html` -> `templates/dashboard/saved_jobs.html`
- `profile-setup.html` -> `templates/dashboard/profile.html`, `templates/dashboard/cv_manage.html`, `templates/cvs/partials/cv_status.html`
- `settings.html` -> `templates/dashboard/account.html`, `templates/dashboard/email_preferences.html`, `templates/dashboard/connections.html`, `templates/dashboard/delete_account.html`
- `auth.html` -> `templates/account/*.html`
- `about.html` -> `templates/core/about.html` (to be created)

## Batch-by-batch likely touched files
- **Batch 1 (Global shell):** `templates/base.html`, `static/src/css/app.css`, `apps/core/context_processors.py` (new), `config/settings/base.py` (to register context processor), basic `tests.py`.
- **Batch 2 (Jobs):** `templates/jobs/job_list.html`, `templates/jobs/job_detail.html`, `templates/jobs/partials/*.html` (explicitly hiding anonymous Save UI in templates), `apps/jobs/tests/test_views.py`, plus explicit service/view/template context logic to support the locked CTA matrix.
- **Batch 3 (Auth/Profile):** `templates/account/*.html`, `templates/dashboard/profile.html`, `templates/dashboard/cv_manage.html`, `templates/dashboard/account.html`, `templates/dashboard/connections.html`, `templates/dashboard/delete_account.html`, `templates/dashboard/delete_account_done.html`, `apps/dashboard/test_social_connections.py`.
- **Batch 4 (Recommendations/Saved/Match):** `templates/dashboard/recommendations.html`, `templates/dashboard/saved_jobs.html`, `templates/matching/match_detail.html`, `templates/matching/partials/*.html`.
- **Batch 5 (About/Contact):** `apps/core/models.py`, `apps/core/forms.py`, `apps/core/services/contact.py`, `apps/core/tasks.py`, `apps/core/urls.py`, `apps/core/views.py`, `templates/core/about.html`, `apps/core/tests/test_contact.py`.
- **Batch 6 (Polish):** Minor CSS adjustments across `static/src/css/app.css` and template layout tweaks.

## Existing backend capabilities to reuse
- `django-allauth` provides robust email verification (`ACCOUNT_EMAIL_VERIFICATION = "mandatory"`) and OAuth capabilities.
- HTMX save/unsave endpoint logic is mature and usable as-is.
- Matching pipeline (full & quick) is deterministic and accessible via existing URLs.
- Existing dashboard context variables for recommendations and saved jobs.

## Missing backend pieces
- `/about/` route, contact form validation, `ContactMessage` model, and async Celery email task.
- Global context processor to quickly expose the user's email verification state (`user.emailaddress_set.filter(primary=True, verified=True).exists()`) without excessive DB queries in templates.
- Explicit service/context support for the job detail CTA (anonymous, no profile/CV, no match, existing match, failed/stale/refresh states) based on existing data.

## State/CTA rules verified against current code
- **Anonymous Save:** The `login_required` endpoint protection exists, but current job-list cards expose the Save UI to anonymous users via `templates/jobs/partials/job_card.html` including `jobs/partials/save_button.html` unconditionally. Batch 2 must hide Save UI in templates for anonymous users.
- **Job Detail CTA:** The current job detail does not have enough context for the locked CTA matrix. Batch 2 needs explicit service/view/template context for all states (anonymous sign-in, logged-in no profile/CV, logged-in no match, logged-in existing match, failed/stale/refresh). We must not invent new MatchResult status fields unless later approved.
- **Set Password State:** `request.user.has_usable_password()` natively supported in Django and ready for use in template conditionals.

## CSS/static strategy
- Maintain and append to `static/src/css/app.css`.
- Use the established `.tta-*` component class conventions instead of inline utility bloat where repetitive.
- Keep Alpine.js scoped strictly to UI interactivity (modals, dropdowns) without expanding it into a SPA framework.

## Tests likely affected
- `apps/jobs/tests/test_views.py`
- `apps/core/test_home_cta.py`
- `apps/core/tests/test_ui.py`
- `apps/dashboard/tests.py`
- `apps/dashboard/test_social_connections.py`
- `apps/cvs/tests/test_views.py`
- `apps/accounts/tests.py`
- `apps/matching/tests.py` view assertions

## Risks
- **Tailwind Building:** Changes to `app.css` or additions of utility classes in templates will require the local Tailwind watcher to recompile.
- **Context Pollution:** Care must be taken not to trigger N+1 queries when building the global context processor for the email verification banner.
- **Allauth Template Overrides:** Customizing forms in `templates/account/*.html` can break allauth's built-in validation rendering if variables aren't matched properly.

## Decisions still needed
- Should contact emails in Batch 5 use a specific queue (e.g., `celery` vs default), and what is the designated admin recipient email address (`.env` vs settings)?
- Does the `Set Password` step immediately redirect into the CV Upload flow, or back to a general dashboard landing?

## Batch 1 readiness
READY AFTER CODEX ISSUES ADDRESSED.

Batch 1 may start only after the corrected report is reviewed.
Batch 1 scope remains global shell only: base.html, nav, footer, email verification banner, toast/state shell, CSS source.
No jobs CTA work in Batch 1.
