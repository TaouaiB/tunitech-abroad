# Phase 14J Acceptance Criteria

## Automated acceptance

All must pass:

```bash
source .venv/bin/activate

python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test --settings=config.settings.local --parallel 1
git diff --check
```

If templates/static changed:

```bash
npm run css:build
python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
```

## Required docs

These files must exist and be specific, not placeholders:

```text
docs/admin/admin_operations_14j.md
docs/admin/admin_analytics_14j.md
```

They must document:

- admin model coverage
- sensitive fields reviewed
- admin actions and delegation target
- metrics available
- metrics not available yet
- manual admin signoff requirements

## Required admin safety

- normal authenticated user cannot access Django Admin or admin operations page
- anonymous user cannot access Django Admin or admin operations page
- staff/superuser can access admin operations page
- CV raw text is not in list displays
- CV file direct URL is not exposed as a public clickable URL
- unsubscribe token raw value is not in list displays
- LLM payloads/secrets/API keys are not in list displays
- admin actions do not directly call OpenRouter or France Travail client
- admin actions delegate to services/tasks
- admin operations metrics do not expose secrets or raw personal data

## Required operational visibility

Admin must be able to inspect or infer:

- latest ingestion status
- ingestion failures
- active/stale/expired jobs
- failed/stuck CV parses
- recommendation run failures/staleness
- LLM usage/failures/cost if model supports it
- email send failures if model supports it
- pending deletion requests
- basic user/profile/CV counts

## Required tests

Add or verify tests for:

- admin access boundary
- admin operations page access boundary if added
- metrics service stable keys if added
- sensitive field exclusion in admin classes
- admin action delegation where actions are added
- docs existence
- no external client calls from views/admin actions except service/task references where documented

## Manual browser signoff

Baha must manually inspect Django Admin in Chrome before final PASS.

Required manual signoff file after completion:

```text
docs/admin/manual_admin_signoff_14j.md
```

Until then the final verdict remains:

```text
FINAL_VERDICT: BLOCKED_HUMAN_ADMIN_SIGNOFF
```
