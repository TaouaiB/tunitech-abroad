# Test Plan — Phase 14G

## Automated tests

Run:

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test apps.cvs apps.profiles apps.matching apps.recommendations --settings=config.settings.local
python manage.py test --settings=config.settings.local
git diff --check
```

## Focused tests to add or confirm

- CV upload creates `CVUpload` with correct owner.
- CV upload enqueues `apps.cvs.tasks.parse_cv`.
- Status endpoint requires login.
- Status endpoint uses UUID `public_id`.
- Integer ID URL does not expose CV status.
- User A cannot access User B CV status.
- Soft-deleted CVs are not visible through normal manager/views.
- Status component renders queued/pending.
- Status component renders processing.
- Status component renders completed.
- Status component renders failed safely.
- HTMX polling stops on terminal state.
- No direct CV file URL in templates.
- No raw CV text in templates.

## Manual browser test

Use three terminals.

Terminal 1:

```bash
python manage.py runserver --settings=config.settings.local
```

Terminal 2:

```bash
celery -A config worker --loglevel=info --concurrency=2
```

Terminal 3:

```bash
redis-cli -p 6380 ping
```

Manual flow:

1. Login as candidate.
2. Upload a test PDF CV.
3. Confirm queued state appears.
4. Confirm processing/completed state appears without manual refresh.
5. Confirm profile/CV parsed data updates if existing behavior supports it.
6. Stop Celery and upload another CV.
7. Confirm UI explains queued/waiting state and local worker hint.

## Regression checks

Run commands from `regression_security_checks.md`.
