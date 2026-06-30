# Phase 10 — Email Tasks

## Phase goal

Add transactional email infrastructure and an opt-in weekly recommendation digest without crossing into Phase 11 privacy deletion, Phase 12 admin/observability, Phase 13 polish, or Phase 14 deployment.

Phase 10 must stay inside email-related scope.

## Existing context

Completed:

- Phase 1 auth foundation with django-allauth.
- Phase 2 core models/admin with `apps.notifications` and `EmailPreference`.
- Phase 8 recommendations and saved jobs.
- Phase 9 controlled LLM support.

Use the existing project patterns.

Do not replace architecture.

Do not rename existing apps unless tests prove a real conflict.

---

## TTA-1001 — Email logging models

### Type

model / migration / admin shell if already consistent with current notifications admin

### Scope

Implement the email-support models inside `apps.notifications`.

Expected models:

1. `EmailBatch`
2. `EmailEvent`
3. `EmailUnsubscribeToken`

Keep the existing `EmailPreference` model. Add fields to it only if required for Phase 10.

### Required model behavior

#### EmailBatch

Purpose: group a digest run or other bulk email operation.

Recommended fields:

- `id`
- `public_id` UUID, unique, indexed, not editable
- `batch_type` choices:
  - `weekly_digest`
  - `transactional`
  - `system`
- `status` choices:
  - `pending`
  - `running`
  - `completed`
  - `failed`
  - `partial_success`
- `period_start`
- `period_end`
- `started_at`
- `finished_at`
- `total_recipients`
- `sent_count`
- `failed_count`
- `skipped_count`
- `error_message`
- `created_at`
- `updated_at`

#### EmailEvent

Purpose: record every attempted/sent/skipped/failed email.

Recommended fields:

- `id`
- `public_id` UUID, unique, indexed, not editable
- `user` nullable FK to user
- `batch` nullable FK to `EmailBatch`
- `email_type` choices:
  - `system`
  - `verification`
  - `password_reset`
  - `weekly_digest`
  - `cv_analysis_completed`
  - `product_update`
- `to_email`
- `subject`
- `template_name`
- `status` choices:
  - `queued`
  - `sent`
  - `failed`
  - `skipped`
  - `duplicate`
- `idempotency_key` unique
- `provider_message_id` optional
- `error_message`
- `metadata_json`
- `queued_at`
- `sent_at`
- `failed_at`
- `created_at`
- `updated_at`

Required constraint:

- unique `idempotency_key`

#### EmailUnsubscribeToken

Purpose: unsubscribe without login.

Recommended fields:

- `id`
- `public_id` UUID, unique, indexed, not editable
- `user` FK to user
- `token` UUID, unique, indexed, not editable
- `email_type` choices:
  - `weekly_digest`
  - `product_update`
  - `all`
- `created_at`
- `used_at`
- `expires_at` nullable

Required behavior:

- token can be used without login
- token use is idempotent
- used token should not crash or re-enable anything
- unsubscribe disables the matching preference

### Tests

Add tests for:

- models can be created
- idempotency key uniqueness prevents duplicate events
- unsubscribe token uniqueness
- token use marks `used_at`
- migrations are generated and clean

---

## TTA-1002 — EmailSenderService

### Type

service / test

### Location

```text
apps/notifications/services/email_sender.py
```

### Contract

```python
EmailSenderService.send(
    to: str,
    subject: str,
    template_name: str,
    context: dict,
    idempotency_key: str,
    user: User | None = None,
    batch: EmailBatch | None = None,
    email_type: str = "system",
) -> EmailEvent
```

### Required behavior

- Check `idempotency_key` before sending.
- If an `EmailEvent` with the same `idempotency_key` already exists, return it and do not send another email.
- Create `EmailEvent(status="queued")`.
- Render text and/or HTML templates.
- Send using Django email utilities only.
- Update `EmailEvent(status="sent")` on success.
- Update `EmailEvent(status="failed")` and `error_message` on failure.
- Do not send email inside a long database transaction.
- Do not log email body, full profile data, full CV text, or secrets.
- Do not call external provider SDKs directly in Phase 10.
- Use Django configured email backend. Tests must use locmem/override settings.

### Template convention

Use one of these stable conventions:

```text
templates/notifications/email/<template_name>_subject.txt
templates/notifications/email/<template_name>.txt
templates/notifications/email/<template_name>.html
```

or clearly document the chosen convention in code and tests.

### Tests

Add tests for:

- first send creates event and sends one message
- duplicate idempotency key returns existing event and sends no duplicate
- failed send records failed status
- HTML/text template rendering works
- no real SMTP needed for tests

---

## TTA-1003 — Email preferences page and unsubscribe flow

### Type

service / form / view / template / urls / test

### Locations

Preferred:

```text
apps/notifications/forms.py
apps/notifications/services/preferences.py
apps/notifications/urls.py
apps/notifications/views.py
templates/dashboard/email_preferences.html
templates/notifications/unsubscribe_success.html
```

Reuse existing dashboard URL patterns if the project already has dashboard routing. Keep routes consistent with current code.

### Required route behavior

Authenticated page:

```text
/dashboard/email-preferences/
```

Public unsubscribe route, exact route may be chosen by the agent but must be stable and tested:

```text
/email/unsubscribe/<uuid:token>/
```

or

```text
/unsubscribe/<uuid:token>/
```

Route name should be stable, for example:

```text
notifications:unsubscribe
```

### EmailPreferenceService contract

```python
EmailPreferenceService.update_preferences(user: User, cleaned_data: dict) -> EmailPreference
EmailPreferenceService.unsubscribe(token: str) -> ServiceResult
```

### Required preference behavior

The page must allow the authenticated user to:

- enable/disable weekly digest
- enable/disable product updates if the field already exists or is added cleanly
- see that instant alerts are not available in MVP, if such a field exists

When the user enables weekly digest:

- record `ConsentRecord` with `consent_type="email_digest"`
- do not record duplicate consent on every save if the digest was already enabled before and remains enabled
- no real email needs to be sent when merely updating preferences

When the user disables weekly digest:

- no consent should be recorded
- future digest eligibility should exclude the user

Unsubscribe behavior:

- unsubscribe works without login
- valid token disables the matching email preference
- invalid token returns controlled 404 or controlled safe page, not 500
- reused token remains safe/idempotent
- unsubscribe does not delete account or CV
- unsubscribe does not implement Phase 11 deletion

### View architecture

Views stay thin:

- load form
- validate access
- call service
- render/redirect

No business logic in templates.

### Tests

Add tests for:

- anonymous user cannot access `/dashboard/email-preferences/`
- authenticated user can access preference page
- enabling weekly digest updates preference and records consent
- disabling weekly digest updates preference
- enabling an already-enabled digest does not create duplicate consent
- unsubscribe works without login
- unsubscribe disables digest/product updates according to token type
- invalid token does not produce HTTP 500
- route names used in templates resolve

---

## TTA-1004 — WeeklyDigestService and Celery task

### Type

service / task / templates / test

### Locations

Preferred:

```text
apps/notifications/services/weekly_digest.py
apps/notifications/tasks.py
templates/notifications/email/weekly_digest_subject.txt
templates/notifications/email/weekly_digest.txt
templates/notifications/email/weekly_digest.html
```

### Contract

```python
WeeklyDigestService.send_weekly_digest(period_start, period_end) -> EmailBatch
```

Celery task:

```python
send_weekly_digest(period_start=None, period_end=None)
```

### Eligibility rules

Send digest only to users who meet all requirements:

- active user
- email is verified through django-allauth `EmailAddress`
- `EmailPreference.weekly_digest_enabled=True`
- active within last 14 days
- usable profile
- has new or relevant recommendations
- has at least one recommendation worth including

Exclude:

- unverified email users
- inactive users
- users with disabled digest
- users with incomplete/unusable profile
- users with no recommendations
- users with stale-only/empty recommendations if current recommendation service has a way to distinguish useful rows

### Digest contents

Minimal acceptable digest:

- greeting
- period label
- top recommended jobs
- fit/ranking score where available
- job title/company/location
- link to dashboard recommendations or job detail
- unsubscribe link
- no guarantee of employment, visa, relocation, or legal outcome

### Idempotency

Per recipient idempotency key:

```text
weekly_digest:{user_id}:{year}-W{week}
```

The same weekly digest run must not send duplicate messages for the same user/week.

Batch can be rerun safely.

### Scheduling

Add task only.

Do not enable production Celery Beat schedule unless it is already the project's pattern and guarded. The stop/go gate is: do not enable scheduled digest until idempotency test passes.

### Tests

Add tests for:

- digest sends only to opted-in verified active eligible user
- unverified email user excluded
- digest disabled user excluded
- inactive user excluded
- incomplete profile user excluded
- no recommendation user excluded
- one email event is logged per sent digest
- duplicate run does not duplicate email due to idempotency
- batch counts sent/skipped/failed correctly
- task calls service only

---

## TTA-1005 — Email templates and allauth baseline verification

### Type

template / settings check / test

### Scope

Verify, not overbuild.

### Required behavior

- allauth email verification still works with local email backend
- password reset email still works with local email backend
- Phase 10 weekly digest templates render correctly
- templates do not contain raw internal IDs in public links
- templates include unsubscribe/preferences link for recommendation digest
- templates avoid guarantees:
  - no guaranteed job
  - no guaranteed visa
  - no guaranteed relocation
  - no legal advice

### Tests

Add tests for:

- password reset route can send email using local backend, if route exists and test setup supports it
- allauth signup/verification flow still sends verification email, if existing Phase 1 test pattern supports it
- weekly digest template renders expected job title and unsubscribe URL
- no template reverse errors

If existing allauth tests are brittle, document the limitation in `agent_report.md` and at minimum prove Django email backend integration through `EmailSenderService` tests.

---

## Required final checks inside the phase

The agent must create or update:

```text
docs/phases/phase_10_email/agent_report.md
```

The report must be fresh and reflect final test results.

Do not leave stale report text saying blocked/failed after successful repair.

Do not leave accidental files:

- `task.md`
- `__pycache__/`
- `*.pyc`
- SQLite files
- celerybeat schedule files
- review zips

---

## Phase boundary denylist

Do not implement:

- account deletion
- CV deletion hardening
- privacy export
- production deployment
- SMTP provider-specific integration dashboard
- admin observability phase
- UI polish phase
- high-match instant alerts
- recruiter/employer dashboards
- paid reports
- new LLM behavior
- live France Travail calls from user search
- any scoring change
- any recommendation algorithm rewrite unless needed only to read existing recommendations for digest
