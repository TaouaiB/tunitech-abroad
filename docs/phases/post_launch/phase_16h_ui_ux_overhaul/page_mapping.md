# Phase 16H Page Mapping — Prototype to Django

## Purpose

This document maps the approved v16 prototype files to the existing Django routes/templates. It is binding for Phase 16H batch planning.

Prototype source:

```text
docs/design/phase_16h/prototype/
```

## High-level mapping

| Prototype file | Purpose | Django target | Notes |
|---|---|---|---|
| `index.html` | Jobs landing/search page | `templates/jobs/job_list.html`, `templates/jobs/partials/job_card.html`, filter/result partials | Jobs/search is public entry. Do not create separate visible dashboard landing. |
| `job-detail.html` | Job detail | `templates/jobs/job_detail.html`, matching partials if needed | CTA must be dynamic by auth/profile/match state. |
| `match-score.html` | Match score/detail | `templates/matching/match_detail.html`, possibly history/card partials | Preserve deterministic scoring. No algorithm changes. |
| `recommendations.html` | Recommendations | `templates/dashboard/recommendations.html`, `templates/recommendations/partials/recommendation_list.html`, `recommendation_card.html` | Login required. Logged-out nav points to auth with next. |
| `saved-jobs.html` | Saved jobs | `templates/dashboard/saved_jobs.html`, job card/save partial reuse | Login required. Hidden from anonymous navigation. |
| `profile-setup.html` | Setup/profile/CV flow | `templates/dashboard/profile.html`, `templates/dashboard/cv_manage.html`, `templates/dashboard/account.html`, CV partials | Password step uses `not user.has_usable_password()`. |
| `settings.html` | Account/settings/preferences/connections | `templates/dashboard/account.html`, `templates/dashboard/connections.html`, `templates/dashboard/email_preferences.html`, delete-account templates | No separate fake settings backend if existing split pages work. |
| `auth.html` | Login/signup/auth visuals | allauth templates under `templates/account/` and `templates/socialaccount/` | Preserve allauth behavior and security. |
| `about.html` | About/contact | new or existing core/about template and route | Requires real contact backend: DB record first, Celery email. |
| `404.html` | Not found | `templates/404.html` | Visual port only. |
| `500.html` | Server error | `templates/500.html` | Visual port only; no secret leakage. |
| `empty-states.html` | Component reference | Reusable partials/classes across real pages | Not a route. |
| `loading-states.html` | Component reference | Reusable skeleton/loading states | Not a route. |
| `failure-states.html` | Component reference | Reusable error/failure states | Not a route. |
| `notifications.html` | Toast/alert/state reference | `base.html`, toast/banner/state components | Not a notification page. No notification system. |
| `README.md` | Prototype notes | Reference only | Rules lock overrides conflicts. |

## Existing route facts to preserve

### Public routes

- `/` currently exists as `core:home`.
- `/jobs/` is public.
- `/jobs/<uuid>/` is public.
- `/privacy/`, `/terms/`, `/health/`, `/robots.txt`, `/sitemap.xml` exist.

Phase 16H may redirect or visually minimize old home if jobs become entry, but must not create route churn unless explicitly scoped.

### Auth/allauth routes

Existing allauth routes must continue to work:

- login
- signup
- logout
- confirm email
- password change/reset/set
- email management
- social login Google/GitHub

Do not replace allauth logic with custom auth logic.

### Dashboard/backend routes

Existing dashboard routes may remain:

- profile
- CV
- recommendations
- saved jobs
- account
- connections
- email preferences
- delete account

No visible dashboard homepage is required as a product feature, but backend routes may remain.

### Saved jobs

Existing save/unsave endpoints are login-required and HTMX-aware.

Templates must hide save UI for anonymous users instead of showing buttons that redirect.

### Recommendations

Existing recommendation routes are login-required.

Logged-out navigation may point to login/signup with a `next` value.

### Matching

Full matching is authenticated and stored per user/job.

Quick match is currently anonymous-capable in backend. Phase 16H may hide the anonymous quick-match UI, but must not delete backend quick-match behavior.

### Notifications

Existing notification backend is email preferences/unsubscribe only.

There is no in-app notification feed, and Phase 16H must not add one.

## Missing backend pieces for Phase 16H

Known missing backend pieces:

1. Public About/contact route and backend.
2. Global email verification banner context.
3. Optional resend email confirmation UI/action if not adequately handled by existing allauth email management.
4. Dynamic job-detail CTA state context if current view/template lacks it.
5. Possibly minor context additions for profile setup/password state.
6. Reusable state/toast/empty/failure patterns.

## Target templates by batch

### Batch 1 — global shell

Likely files:

- `templates/base.html`
- `static/src/css/app.css`
- possible `apps/core/context_processors.py`
- possible settings update for context processor
- account/banner partial if created
- related tests

### Batch 2 — jobs

Likely files:

- `templates/jobs/job_list.html`
- `templates/jobs/job_detail.html`
- `templates/jobs/partials/job_card.html`
- `templates/jobs/partials/job_filter_panel.html`
- `templates/jobs/partials/job_results.html`
- `templates/jobs/partials/save_button.html`
- job/matching view/service context only if needed
- tests

### Batch 3 — auth/profile/settings

Likely files:

- `templates/account/login.html`
- `templates/account/signup.html`
- `templates/account/email_verification_sent.html`
- `templates/account/verification_sent.html`
- `templates/account/email_confirm.html`
- `templates/account/password_set.html`
- `templates/account/password_change.html`
- `templates/dashboard/profile.html`
- `templates/dashboard/cv_manage.html`
- `templates/dashboard/account.html`
- `templates/dashboard/connections.html`
- `templates/dashboard/email_preferences.html`
- CV/profile partials
- tests

### Batch 4 — recommendations/saved/match/states

Likely files:

- `templates/dashboard/recommendations.html`
- `templates/recommendations/partials/recommendation_list.html`
- `templates/recommendations/partials/recommendation_card.html`
- `templates/dashboard/saved_jobs.html`
- `templates/matching/match_detail.html`
- `templates/matching/match_history.html`
- `templates/matching/partials/quick_match_form.html`
- `templates/matching/partials/quick_match_result.html`
- reusable state partials if introduced
- tests

### Batch 5 — About/contact backend

Likely files:

- `apps/core/models.py` or a focused app model location
- migration
- `apps/core/forms.py`
- `apps/core/services/contact.py`
- `apps/core/tasks.py` or existing task module
- `apps/core/views.py` or URL route location
- `config/urls.py` or `apps/core/urls.py`
- `templates/core/about.html` or `templates/about.html`
- `.env.example` if recipient setting added
- tests

### Batch 6 — final responsive polish

Likely files depend on prior batches.

Do not add new backend features in Batch 6.
