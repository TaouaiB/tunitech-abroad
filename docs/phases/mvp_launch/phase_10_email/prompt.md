# Gemini / Antigravity Prompt — Phase 10 Email

You are implementing **Phase 10 — Email** for TuniTech Abroad.

Read this file fully before editing code.

## Work mode

Implement all Phase 10 tickets automatically.

Do not ask for approval between tickets inside this phase.

Use the existing codebase conventions.

Run tests, inspect failures, fix root causes, and keep working until Phase 10 acceptance is clean or until the repair limit is reached.

## Required reading before coding

From the repository root, read:

```text
AGENTS.md
docs/phases/phase_10_email/README.md
docs/phases/phase_10_email/tasks.md
docs/phases/phase_10_email/acceptance.md
docs/planning/Implementation_Roadmap_v1.pdf
docs/planning/Service_Contracts_v1.pdf
docs/planning/PRD_v1.pdf
docs/planning/Database_Schema_v1.pdf
docs/planning/Page_URL_View_Map_v1.pdf
```

If the PDFs are not present under exactly those names, inspect `docs/planning/` and use the equivalent TuniTech Abroad planning PDFs.

## Current phase

Phase 10 only:

```text
Phase 10 — Email
```

Expected folder:

```text
docs/phases/phase_10_email/
```

## Stack

Use only:

- Django
- Django ORM
- PostgreSQL
- Redis
- Celery
- Celery Beat only if already configured and not enabling live schedule prematurely
- django-allauth
- Django templates
- HTMX if useful and already used
- Tailwind CSS

Forbidden:

- React
- Next.js
- Angular
- FastAPI
- MongoDB
- SQLAlchemy
- SPA architecture
- new external provider SDKs for email
- real SMTP credential requirements in tests

## Architecture rules

Views stay thin.

Business logic goes in services.

Celery tasks call services only.

Models store data and do not call external APIs.

No OpenRouter calls from views or models.

No France Travail live API calls during normal user search.

No scoring logic changes.

No recommendation algorithm rewrite except minimal reading/querying needed for digest content.

Public URLs use UUID `public_id`, never internal integer IDs.

CV files remain private.

`CVUpload.objects` excludes soft-deleted CVs.

`CVUpload.all_objects` is only for admin/privacy/deletion/internal tasks.

LLM can extract, explain, and suggest, but cannot decide final fit score.

No real secrets in code, tests, logs, prompts, or reports.

## Phase 10 scope

Implement email-related MVP scope only:

- `EmailBatch`
- `EmailEvent`
- `EmailUnsubscribeToken`
- `EmailSenderService`
- `EmailPreferenceService`
- `WeeklyDigestService`
- email preference page
- unsubscribe route
- weekly digest task
- weekly digest templates
- tests

Use existing `apps.notifications`.

Do not create `apps.email`.

If `apps.notifications` is already installed, extend it. If it exists but is not installed, fix registration. If it does not exist, that would be a Phase 2 violation; create it only if truly absent and document why.

## Specific implementation requirements

### Models

Add missing notification models in `apps.notifications.models` or an equivalent existing model module:

- `EmailBatch`
- `EmailEvent`
- `EmailUnsubscribeToken`

Preserve existing `EmailPreference`.

Add migrations.

Required idempotency:

- `EmailEvent.idempotency_key` must be unique.

Recommended statuses:

```text
EmailBatch.status: pending, running, completed, failed, partial_success
EmailEvent.status: queued, sent, failed, skipped, duplicate
```

### Services

Implement or update:

```text
apps/notifications/services/email_sender.py
apps/notifications/services/preferences.py
apps/notifications/services/weekly_digest.py
```

Required contracts:

```python
EmailSenderService.send(
    to: str,
    subject: str,
    template_name: str,
    context: dict,
    idempotency_key: str,
    user=None,
    batch=None,
    email_type: str = "system",
)
```

```python
EmailPreferenceService.update_preferences(user, cleaned_data)
EmailPreferenceService.unsubscribe(token)
```

```python
WeeklyDigestService.send_weekly_digest(period_start, period_end)
```

Use existing shared service result classes if they exist. Otherwise use simple dataclasses or stable result dictionaries consistent with the codebase.

### Email sending

Use Django email utilities.

Use configured Django email backend.

Tests must use locmem email backend or a safe local backend.

Do not require real SMTP.

Do not print email credentials.

Do not log full email bodies, CV text, or secrets.

### Weekly digest eligibility

Send only to users who are all of:

- verified email user through django-allauth `EmailAddress`
- `EmailPreference.weekly_digest_enabled=True`
- active within last 14 days
- usable profile
- has new/relevant recommendations
- has at least one recommendation to include

Exclude:

- unverified email users
- inactive users
- disabled digest users
- incomplete/unusable profile users
- users with no recommendations

Use existing `ActiveUserRecommendationService` if available.

Use existing recommendation query/model APIs where possible.

Do not compute heavy recommendations synchronously in the digest service.

### Idempotency

Per-user weekly digest idempotency key:

```text
weekly_digest:{user_id}:{year}-W{week}
```

A duplicate run for the same user/week must not send a duplicate email.

### Views and routes

Implement or wire:

```text
/dashboard/email-preferences/
```

Add public unsubscribe route. Choose one stable route and test it:

```text
/email/unsubscribe/<uuid:token>/
```

or:

```text
/unsubscribe/<uuid:token>/
```

Views must call services.

Views must not contain preference business logic beyond form handling and service call.

### Templates

Create/modify templates:

```text
templates/dashboard/email_preferences.html
templates/notifications/unsubscribe_success.html
templates/notifications/email/weekly_digest_subject.txt
templates/notifications/email/weekly_digest.txt
templates/notifications/email/weekly_digest.html
```

The digest email must include an unsubscribe link.

Do not include employment, visa, relocation, or legal guarantees.

Do not expose internal integer IDs in links.

### Celery task

Add:

```python
send_weekly_digest(period_start=None, period_end=None)
```

Task must call `WeeklyDigestService` only.

No business logic in Celery task.

Do not enable a live production schedule unless the project already has a safe pattern and tests prove idempotency.

### Tests

Add strong Phase 10 tests under `apps.notifications`.

At minimum cover:

- model creation
- `EmailEvent.idempotency_key` uniqueness
- `EmailSenderService` sends once
- duplicate idempotency key does not send twice
- failed email send logs failed status
- preference page auth guard
- authenticated preference page loads
- enable digest updates preference and records consent once
- disabling digest updates preference
- unsubscribe works without login
- invalid unsubscribe does not 500
- weekly digest sends only to eligible opted-in verified active user
- unverified user excluded
- inactive user excluded
- disabled preference user excluded
- incomplete profile user excluded
- no recommendation user excluded
- duplicate weekly digest run does not send duplicate
- `EmailEvent` logs sent status
- batch counts are correct
- Celery task calls service only
- route/template reverse errors are caught

Also keep cross-phase regression tests passing:

- `apps.cvs`
- `apps.jobs`
- `apps.matching`
- `apps.recommendations`
- `apps.llm`
- full suite

## Autonomous repair loop

After implementation, run the full acceptance commands from `acceptance.md`.

If any command fails:

1. Read the exact error.
2. Identify the real root cause.
3. Fix only the cause.
4. Add or update a regression test for that failure.
5. Re-run the failed command.
6. Re-run the full acceptance set.
7. Repeat until all acceptance commands pass.

Maximum repair loops: 8.

If still failing after 8 repair loops, stop and report:

- exact failing command
- traceback/error
- files changed
- what was attempted
- remaining blocker

Do not keep coding blindly.

## Failure conditions

Treat these as failure even if some tests pass:

- `Found 0 test(s)`
- current phase tests do not run
- migrations missing
- `makemigrations --check --dry-run` fails
- app created but not registered in `INSTALLED_APPS`
- URL used in template but not wired
- view exists but no route
- template partial exists but is never included
- service exists but is not called by view/task
- hidden HTTP 500 in logs or tests
- stale `agent_report.md`
- DB tests blocked but report claims success
- SQLite-only validation when PostgreSQL local settings are required
- `.env` committed or printed
- real secrets printed or committed
- accidental `__pycache__`, `.pyc`, sqlite, celerybeat, or review zip files left in repo
- Phase 11 privacy deletion work implemented
- Phase 12 admin observability implemented
- Phase 13 polish implemented
- Phase 14 deployment implemented

## Final report

Create or update:

```text
docs/phases/phase_10_email/agent_report.md
```

Use `agent_report_template.md`.

The report must include:

- completed tickets
- files changed
- migrations created
- routes added
- templates added
- services added
- commands run
- final command outputs
- exact test counts
- remaining risks/manual steps
- confirmation that Phase 11 was not started
- confirmation that no real secrets were printed or committed
- confirmation that `Found 0 test(s)` did not occur
- confirmation that `git status --short` was reviewed

## Stop condition

Stop after Phase 10 acceptance is clean.

Do not start Phase 11.
