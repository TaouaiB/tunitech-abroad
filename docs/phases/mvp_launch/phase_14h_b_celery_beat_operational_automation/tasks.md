# Tasks

## Task 1 — Inspect existing Celery tasks

Review:

- `config/celery.py`
- `config/settings/base.py`
- `apps/jobs/tasks.py`
- `apps/recommendations/tasks.py`
- `apps/privacy/tasks.py`
- `apps/notifications/tasks.py`

Confirm exact task names registered by Celery.

## Task 2 — Populate Celery Beat schedule

Update `config/settings/base.py` or an appropriate settings module so `CELERY_BEAT_SCHEDULE` contains safe periodic entries.

Recommended initial schedule:

- Broad IT ingestion: every 4 hours.
- Stale/expired job cleanup: daily around 02:30.
- Active-user recommendation refresh: daily around 03:30.
- Expired quick-match cleanup: daily around 04:00.
- Orphaned CV file cleanup: weekly, Sunday around 04:30.

Use Celery's `crontab` or interval schedule. Prefer clear names.

## Task 3 — Ensure scheduled tasks are safe

For each scheduled task, confirm:

- It calls services only.
- It does not perform external work from views.
- It respects config/limits.
- It is idempotent enough for repeated Beat execution.
- It logs enough information for local debugging.

Do not rewrite existing task logic unless a clear bug is found.

## Task 4 — Tests

Add tests proving:

- `CELERY_BEAT_SCHEDULE` is non-empty.
- Required task names are present.
- No scheduled task points to a missing/unregistered task name.
- The job ingestion task is scheduled.
- Cleanup tasks are scheduled.
- Public job search still does not import/call France Travail.
- LLM is still not called from views.

Prefer small settings/config tests and architecture regression tests.

## Task 5 — Local operations documentation

Add or update `docs/phases/phase_14h_b_celery_beat_operational_automation/worker_beat_playbook.md` explaining how to run locally:

- Redis
- Django
- Celery worker
- Celery Beat
- How to inspect logs
- How to stop tasks safely

## Task 6 — Verification

Run the required checks and produce an agent report.
