# Phase 1 — Django Foundation and Authentication

## Phase folder

Place this file at:

```text
docs/phases/phase_01_auth_foundation/tasks.md
```

## Goal

Implement the authentication and base web foundation for TuniTech Abroad.

This phase turns the Phase 0 skeleton into a minimal working Django application with:

- custom user model
- Django auth/admin enabled safely
- django-allauth configured
- email/password signup and verification
- Google/GitHub OAuth placeholders
- login/signup/logout pages
- base layout and homepage shell
- authenticated dashboard placeholder
- post-signup provisioning hook shell

## Phase boundary

Phase 1 is authentication foundation only.

Do not implement Phase 2 models yet.

Specifically, do not create real implementations of:

- CandidateProfile
- ProfileSkill
- EmailPreference
- ConsentRecord
- UserEvent database model
- SystemSetting
- skills/jobs/CV/matching/recommendation/LLM/email-digest/privacy-deletion models

### Important boundary resolution

The roadmap mentions `AccountProvisioningService` in Phase 1 and also says CandidateProfile and EmailPreference should exist after signup. The roadmap also defines Phase 2 as the phase that creates CandidateProfile and EmailPreference.

For this implementation, preserve the phase boundary:

- In Phase 1, create the provisioning service and wire it into signup/login flow.
- The service must be idempotent.
- The service must not create CandidateProfile or EmailPreference yet because those models belong to Phase 2.
- Add clear TODO comments/tests showing Phase 2 will extend the service once those models exist.
- Do not create placeholder database tables for Phase 2 models.

## Tickets

## TTA-0101 — Create custom User model

Priority: P0  
Type: model/backend

### Description

Create the custom User model before enabling normal auth migrations.

### Required work

- Create `apps/accounts/` Django app.
- Create `apps/accounts/apps.py`.
- Create `apps/accounts/models.py`.
- Implement `User` as the project user model.
- Email must be unique.
- Configure `AUTH_USER_MODEL = "accounts.User"`.
- Add `apps.accounts` to `INSTALLED_APPS` before migrations are generated.
- Enable required Django auth/admin apps.
- Register the custom User in admin using a safe `UserAdmin` implementation.
- Keep username support compatible with Django/allauth, but email must be the primary login identifier for users.
- Add tests for user creation and unique email enforcement.

### Acceptance

- `accounts.User` exists.
- `AUTH_USER_MODEL` points to `accounts.User`.
- `accounts_user` table exists after migrations.
- `auth_user` table does not exist.
- Email uniqueness is enforced.
- Superuser creation works.
- Admin can manage users.

## TTA-0102 — Install and configure django-allauth

Priority: P0  
Type: integration

### Description

Add django-allauth for email/password login, email verification, Google OAuth, and GitHub OAuth placeholders.

### Required work

- Add `django-allauth` to runtime requirements.
- Install dependency through the project virtual environment only.
- Add required allauth apps/middleware/settings.
- Add `django.contrib.sites` if required by allauth.
- Set `SITE_ID` if required.
- Configure email/password signup and login.
- Configure email verification for email/password users.
- Configure local console email backend.
- Configure Google OAuth provider placeholders using environment variables.
- Configure GitHub OAuth provider placeholders using environment variables.
- Do not put OAuth secrets in source code.
- Do not require real OAuth credentials for local checks.
- Include allauth URLs under `/accounts/`.
- Add or override minimal allauth templates:
  - `templates/account/login.html`
  - `templates/account/signup.html`
  - `templates/account/logout.html`
  - `templates/account/email_verification_sent.html`
  - other required minimal templates if allauth needs them

### Acceptance

- `/accounts/login/` loads.
- `/accounts/signup/` loads.
- `/accounts/logout/` is available to authenticated users.
- Email/password signup works locally.
- Verification email is printed to console in local dev.
- Login/logout works.
- Google/GitHub provider config exists without real secrets.
- No real secret is committed or printed.

## TTA-0103 — Implement AccountProvisioningService shell

Priority: P0  
Type: service

### Description

Create and wire a post-signup/post-login provisioning service.

### Required work

- Create `apps/accounts/services/account_provisioning.py`.
- Implement `AccountProvisioningService.provision_new_user(user, provider=None)`.
- The service must be idempotent.
- The service must not create Phase 2 models yet.
- Wire the service through a safe allauth adapter or signal.
- Ensure the hook runs after signup/login where appropriate.
- Add tests proving repeated calls are safe.
- Add explicit comments stating CandidateProfile and EmailPreference creation is added in Phase 2.

### Acceptance

- Service exists.
- Service can be called repeatedly without duplicate side effects.
- Signup flow calls the service.
- The service does not import or create missing Phase 2 models.
- Tests document that real profile/preference row creation is deferred to Phase 2.

## TTA-0104 — Create base templates and homepage shell

Priority: P0  
Type: frontend

### Description

Create the minimum public web shell.

### Required work

- Create a no-model `apps/core/` app if needed for homepage/health/base views.
- Keep existing `/health/` working.
- Add root URL `/`.
- Create `templates/base.html`.
- Create `templates/core/home.html`.
- Add minimal navigation:
  - Home
  - Login
  - Signup
  - Dashboard when authenticated
  - Logout when authenticated
- Use Django templates.
- Use simple Tailwind-compatible classes, but do not spend time on polish.
- No React, SPA, Next.js, Angular, or frontend build complexity.

### Acceptance

- `GET /` returns 200.
- Homepage communicates TuniTech Abroad positioning.
- Login/signup links exist for anonymous users.
- Dashboard/logout links exist for authenticated users.
- Base template exists and is reused.

## TTA-0105 — Create dashboard access guard

Priority: P0  
Type: backend/frontend

### Description

Create an authenticated dashboard placeholder.

### Required work

- Create a no-model `apps/dashboard/` app if needed.
- Create `/dashboard/` route.
- Require authentication.
- Anonymous users must redirect to login.
- Authenticated users must receive 200.
- Render a minimal dashboard placeholder template.
- Do not implement recommendations, CV status, profile completeness, saved jobs, or match history yet.

### Acceptance

- Anonymous `GET /dashboard/` redirects to login.
- Authenticated `GET /dashboard/` returns 200.
- Dashboard template clearly says real dashboard widgets come in future phases.

## Required tests

Use Django's built-in test runner unless there is already a different approved test framework.

Required minimum tests:

- User can be created with unique email.
- Duplicate email is rejected.
- `AUTH_USER_MODEL` is `accounts.User`.
- Database has no `auth_user` table after migrations.
- Login page returns 200.
- Signup page returns 200.
- Homepage returns 200.
- Dashboard redirects anonymous user.
- Dashboard returns 200 for authenticated user.
- AccountProvisioningService is idempotent.
- No Phase 2 models are created in Phase 1.

## Explicit non-goals

Do not implement:

- CandidateProfile model
- EmailPreference model
- ProfileCompletenessService
- SystemSetting
- ConsentRecord
- UserEvent database model
- job ingestion
- job search
- CV upload/parsing
- matching
- recommendations
- OpenRouter/LLM
- real email provider integration
- weekly digest
- delete account
- delete CV
- public job URLs
- Tailwind build pipeline beyond minimal template usage

## Final phase output

At the end, the agent must provide a report using:

```text
docs/phases/phase_01_auth_foundation/agent_report_template.md
```

The agent must not commit, merge, or push.
