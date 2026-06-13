# Phase 1 — Acceptance Checklist

Place this file at:

```text
docs/phases/phase_01_auth_foundation/acceptance.md
```

Phase 1 is accepted only when all checks below pass.

## Scope acceptance

- [ ] Phase 1 implements authentication foundation only.
- [ ] No Phase 2 models are created.
- [ ] No jobs/CV/skills/matching/recommendations/LLM/email-digest/privacy-deletion features are created.
- [ ] No React, Next.js, Angular, FastAPI, MongoDB, SQLAlchemy, or SPA architecture is introduced.
- [ ] Views stay thin.
- [ ] Account provisioning logic is in a service.
- [ ] No business logic is placed in templates.
- [ ] No external API calls are made from models or views.
- [ ] No real OAuth/email/OpenRouter/France Travail secrets are committed or printed.

## Required files and structure

Expected files/apps may include:

```text
apps/accounts/
apps/accounts/__init__.py
apps/accounts/apps.py
apps/accounts/models.py
apps/accounts/admin.py
apps/accounts/services/account_provisioning.py
apps/accounts/tests.py
apps/core/
apps/core/views.py
apps/core/urls.py
apps/core/tests.py
apps/dashboard/
apps/dashboard/views.py
apps/dashboard/urls.py
apps/dashboard/tests.py
templates/base.html
templates/core/home.html
templates/dashboard/home.html
templates/account/login.html
templates/account/signup.html
templates/account/logout.html
```

The exact split can differ if clean, but the architecture must remain understandable.

## Dependency checks

- [ ] `django-allauth` is added to runtime requirements.
- [ ] No package is installed globally.
- [ ] No `pip --user` is used.
- [ ] `.venv` is used.
- [ ] `django-stubs` remains dev-only if present.

## Settings checks

- [ ] `AUTH_USER_MODEL = "accounts.User"` is set before auth migrations are applied.
- [ ] Required Django auth/admin/session/messages/staticfiles apps are configured.
- [ ] Required allauth apps and middleware are configured.
- [ ] Email backend is console in local settings.
- [ ] OAuth provider settings read from environment variables or placeholders only.
- [ ] `.env.example` contains variable names only, no real secrets.
- [ ] `.env` remains ignored and uncommitted.

## Database/migration checks

Run:

```bash
source .venv/bin/activate
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py check --settings=config.settings.local
python manage.py migrate --settings=config.settings.local
```

Expected:

- [ ] Migrations are present and committed for Phase 1 apps.
- [ ] `python manage.py check` passes.
- [ ] `python manage.py migrate` passes.
- [ ] `accounts_user` table exists.
- [ ] `auth_user` table does not exist.

Verify table names:

```bash
source .venv/bin/activate
python manage.py shell --settings=config.settings.local -c "from django.db import connection; c=connection.cursor(); c.execute(\"SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name;\"); print([r[0] for r in c.fetchall()])"
```

## Auth flow checks

Run server:

```bash
source .venv/bin/activate
python manage.py runserver --settings=config.settings.local
```

Manual/browser checks:

- [ ] `GET /` returns 200.
- [ ] `GET /health/` still returns JSON 200.
- [ ] `GET /accounts/login/` returns 200.
- [ ] `GET /accounts/signup/` returns 200.
- [ ] Email/password signup works locally.
- [ ] Verification email appears in console output.
- [ ] Login works after valid local verification flow/test setup.
- [ ] Logout works.
- [ ] `GET /dashboard/` as anonymous redirects to login.
- [ ] `GET /dashboard/` as authenticated returns 200.

## Automated tests

Run:

```bash
source .venv/bin/activate
python manage.py test --settings=config.settings.local
```

Expected minimum coverage:

- [ ] User creation test passes.
- [ ] Unique email test passes.
- [ ] Custom user model setting test passes.
- [ ] No default `auth_user` table test passes.
- [ ] Login page view test passes.
- [ ] Signup page view test passes.
- [ ] Homepage view test passes.
- [ ] Dashboard anonymous redirect test passes.
- [ ] Dashboard authenticated access test passes.
- [ ] AccountProvisioningService idempotency test passes.
- [ ] Phase boundary test confirms CandidateProfile and EmailPreference are not created in Phase 1.

## Security checks

Run:

```bash
git status --short
git ls-files | grep -E "\.env$|celerybeat|__pycache__" || true
grep -R "DJANGO_SECRET_KEY=.*[^=]" . --exclude-dir=.git --exclude=.env --exclude=.env.example || true
grep -R "GOOGLE_CLIENT_SECRET=.*[^=]" . --exclude-dir=.git --exclude=.env --exclude=.env.example || true
grep -R "GITHUB_CLIENT_SECRET=.*[^=]" . --exclude-dir=.git --exclude=.env --exclude=.env.example || true
```

Expected:

- [ ] `.env` is not tracked.
- [ ] runtime files are not tracked.
- [ ] no real secret appears in tracked files.
- [ ] no secret is printed in report.

## Git behavior

- [ ] Agent did not commit.
- [ ] Agent did not merge.
- [ ] Agent did not push.
- [ ] Final report includes changed files, commands, results, risks, and no-Phase-2 confirmation.

## Stop/Go gate

Do not start Phase 2 until:

- all acceptance checks pass
- Baha sends the report/diff/test output for review
- ChatGPT reviews and approves or provides fixes
