# Phase 14J Manual Django Admin Signoff

Baha must complete this after Gemini/Codex automated checks pass.

Create final signoff file:

```text
docs/admin/manual_admin_signoff_14j.md
```

## Browser setup

```bash
cd ~/Projects/tunitech-abroad
source .venv/bin/activate
python manage.py runserver --settings=config.settings.local
```

Open Chrome.

## Checks

### Access boundary

- Logged out user cannot access `/admin/`.
- Normal authenticated user cannot access `/admin/`.
- Staff/superuser can access `/admin/`.
- Anonymous/normal users cannot access admin operations page if added.

### Admin model screens

Inspect list and detail pages for:

- users
- profiles
- CV uploads
- CV parsed data
- jobs and ingestion runs
- skills/unmatched skills
- matches/recommendations/saved jobs
- LLM usage/cache/prompt logs
- email preferences/batches/events/unsubscribe tokens
- privacy deletion/consent records
- analytics events

Confirm:

- no raw CV text in list views
- no direct public CV file URL in list views
- no raw unsubscribe token in list views
- no secrets/API keys/OAuth tokens in list/detail views
- no raw LLM request/response payloads in high-volume list views
- status, timestamps, counts, and errors are visible enough for operations

### Admin operations dashboard if added

Confirm:

- metrics load for staff/superuser
- no secrets or raw personal data displayed
- numbers are plausible
- failed ingestion/CV parse/recommendation/email/deletion visibility exists or is documented as unavailable

### Admin actions

For actions added in this phase:

- action appears only for admin users
- action does not expose secrets
- action delegates to service/task
- action gives a clear success/failure message
- action does not call OpenRouter or France Travail directly

## Signoff template

```markdown
# Phase 14J Manual Admin Signoff

Date: YYYY-MM-DD
Reviewer: Baha

## Result

Manual Django Admin signoff completed.

## Checked

- Anonymous user blocked from admin.
- Normal user blocked from admin.
- Staff/superuser can access admin.
- Admin operations page checked if present.
- CV admin screens do not expose raw CV text or public CV file URLs casually.
- Unsubscribe token raw value not visible in list views.
- LLM/admin screens do not expose secrets/API keys/raw payloads casually.
- Jobs/ingestion admin provides useful status/error/count visibility.
- CV parsing failures/stuck states are visible.
- Recommendation/LLM/email/privacy operational states are visible or documented.
- Admin actions are safe and service/task delegated.

## Verdict

Phase 14J accepted after automated checks and manual Django Admin signoff.
```
