# Phase 13 — MVP Polish and Deployment Preparation Tasks

## Goal

Prepare the MVP for first controlled external use without deploying it yet.

Phase 13 is polish and deployment preparation only. It must improve usability, safety, production readiness, documentation, and critical-flow reliability. It must not add new product features or start Phase 14 deployment.

## Hard Boundaries

Do not:

- deploy anything
- add a hosting provider
- configure real domain/HTTPS
- enable scheduled live France Travail ingestion in production
- add new external SaaS monitoring
- add React/Next/Angular/SPAs
- add Meilisearch or new search engines
- add payment/recruiter/multi-country features
- add LinkedIn/Facebook login
- expose CV files through public media
- call OpenRouter from views/admin/templates
- call France Travail live during normal user job search
- use internal integer IDs in public URLs
- print, store, or commit secrets

## Required Tickets

### TTA-1301 — Phase 13 preflight and audit

- Confirm branch is `dev`.
- Confirm Phase 12 is committed.
- Inspect current routes/templates for public pages, jobs, dashboard, CV, matching, recommendations, email preferences, privacy, admin, and health.
- List critical pages and flows already implemented.
- Identify obvious broken routes, missing templates, hidden 500 risks, bad redirects, missing URL names, stale docs, and copy inconsistencies.

### TTA-1302 — Error pages and safe error UX

- Add or improve custom 404 and 500 templates using the existing base layout.
- Ensure 404/500 templates do not leak stack traces, settings, paths, internal IDs, secrets, tokens, or CV file names.
- Add tests for handler routes where practical, or direct template/view tests if handlers are hard to test under Django test mode.
- Keep design simple and consistent.

### TTA-1303 — Empty states across MVP pages

Add useful empty states for:

- no jobs found
- no CV uploaded
- no parsed CV/profile data yet
- no saved jobs
- no recommendations yet
- no match history yet
- no email digest history/events visible to the user if applicable

Rules:

- Empty states must guide the user to the next existing action.
- Do not create new feature flows.
- Use existing routes only.
- Do not expose private data or internal IDs.

### TTA-1304 — Loading states and HTMX/user feedback polish

- Add loading indicators for existing HTMX forms/actions where the app already uses HTMX.
- Add disabled/processing state where practical for existing submit buttons.
- Do not convert pages to SPA.
- Do not add heavy JavaScript.
- Alpine.js only if already present and clearly useful.

### TTA-1305 — Form validation polish

Review and improve user-facing validation messages for critical forms:

- signup/login if custom templates exist
- CV upload
- profile edit
- email preferences
- delete account confirmation
- quick match / matching forms if applicable

Rules:

- Validation logic stays in forms/services, not templates.
- Views remain thin.
- Errors must be understandable in French where user-facing.

### TTA-1306 — Responsive layout pass

- Improve Tailwind layout for mobile/tablet/desktop on key pages.
- Avoid major redesign.
- Use existing design patterns.
- Check navigation, forms, job cards, match score cards, dashboard panels, and admin-independent public pages.

### TTA-1307 — French UI wording pass

- Review visible user-facing copy for French consistency.
- Do not rewrite internal technical docs into marketing fluff.
- Keep claims conservative: no guaranteed employment, no visa/legal advice, no AI promise.
- Keep product positioning: France-first job intelligence for Tunisian IT profiles.

### TTA-1308 — Security and production settings preparation

Add or harden production-prep settings using environment variables only:

- `DEBUG`
- `ALLOWED_HOSTS`
- `CSRF_TRUSTED_ORIGINS`
- `SITE_URL` or equivalent existing setting
- secure cookie settings for production
- HTTPS/security header settings for production
- static/media roots
- private media rules
- email/OAuth/France Travail/OpenRouter variables already defined where relevant

Rules:

- Do not place real secrets in code or docs.
- Do not break local settings.
- Do not force production-only HTTPS behavior in local development.
- Add `.env.example` placeholders only if missing.

Potential placeholders, only if project conventions support them:

```env
DEBUG=False
ALLOWED_HOSTS=your-domain.example
CSRF_TRUSTED_ORIGINS=https://your-domain.example
SITE_URL=https://your-domain.example
DJANGO_SECRET_KEY=change-me-in-real-env
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

Do not require Baha to create real values in Phase 13.

### TTA-1309 — Static files and private media readiness

- Confirm staticfiles config is ready for collection.
- Add docs/commands for `collectstatic`.
- Ensure private CV media is not served through public URL patterns.
- Add tests or greps to prove CV file fields are not rendered as public links on user/admin pages.
- Do not expose `PRIVATE_MEDIA_ROOT` content through `urlpatterns`.

### TTA-1310 — Seed and fixture command polish

- Review existing seed/fixture commands.
- Improve command help text and idempotency where needed.
- Add or update a lightweight demo/test-data command only if it fits current structure and does not overbuild.
- Fixture commands must not require real France Travail credentials.
- No live API calls unless command name makes it explicit and is already part of ingestion architecture.

### TTA-1311 — Deployment checklist documentation

Create or update:

- `docs/deployment/checklist.md`
- `docs/deployment/environment.md`
- `docs/deployment/manual_test_plan.md`

Must include:

- env vars required for Phase 14
- migrations
- collectstatic
- admin account
- OAuth redirect URL update
- email provider check
- health endpoint check
- worker/beat commands
- private media verification
- rollback note
- backup note

Do not include real secrets.

### TTA-1312 — Critical manual flow checklist

Document and, where possible, test:

- landing page
- signup/login/logout
- Google/GitHub login route availability
- job search from PostgreSQL
- job detail by UUID public_id
- CV upload page access
- profile page
- match result / quick match
- recommendations
- saved jobs
- email preferences
- privacy/terms
- delete account confirmation
- admin login
- health endpoint healthy/unhealthy behavior

### TTA-1313 — Tests and regression protection

Add focused tests only where there is value:

- error pages/rendering
- critical route rendering
- production settings parsing if safe
- no public integer ID routes added
- no public CV file exposure
- health endpoint remains thin/service-based
- seed command idempotency if touched

Do not add brittle snapshot tests of every template.

### TTA-1314 — Final cleanup and report

- Remove `__pycache__`, `.pyc`, accidental sqlite DBs, celerybeat files, `task.md`, stale report saves.
- Run acceptance commands.
- Fill `agent_report.md` from the template.
- Stop after Phase 13. Do not start Phase 14.

## Required Architecture Checks

- Views stay thin.
- Services own business logic.
- Celery tasks call services only.
- No models call external APIs.
- No OpenRouter calls from views/admin/templates.
- No France Travail live calls during normal user search.
- Public URLs use `public_id` UUIDs.
- CV files remain private.
- `CVUpload.objects` excludes soft-deleted CVs.
- `CVUpload.all_objects` only in admin/privacy/deletion/internal tasks.

## Secrets

No new real secrets are required for Phase 13.

Agents may update `.env.example` with missing variable names only. Baha will fill real production values in Phase 14.
