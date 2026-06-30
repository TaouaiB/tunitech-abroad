# Tasks — Phase 14G

## Ticket 14G-01 — Audit current CV upload/status flow

Inspect:

- `apps/cvs/models.py`
- `apps/cvs/tasks.py`
- `apps/cvs/services/`
- CV upload view(s)
- CV status view(s), especially `/dashboard/cv/status/<public_id>/`
- related templates
- tests

Document the current statuses and where they are set.

Do not refactor yet until the current flow is understood.

## Ticket 14G-02 — Define user-facing status map

Map internal statuses to user-facing messages:

- `uploaded` / `pending`: “Queued for analysis”
- `processing`: “Analyzing your CV”
- `completed` / `parsed`: “CV analyzed successfully”
- `failed`: “CV analysis failed”
- `deleted`: never shown in normal user list

Use whatever real enum/status names already exist in code, but make the UI wording friendly.

## Ticket 14G-03 — Improve upload page feedback

After upload:

- Show “Upload complete”.
- Show “Queued for analysis”.
- Show clear instruction: “Keep this page open or come back later.”
- Show that local processing requires the background worker.
- Keep this message non-technical for normal users.

For local development only, a small help text may say:

```text
If this stays queued in local development, start the Celery worker.
```

Do not show raw Celery internals to public users.

## Ticket 14G-04 — Improve status polling

If the app already has HTMX polling, harden it.
If not, add HTMX polling on the CV status component.

Requirements:

- Poll every 3–5 seconds while queued/processing.
- Stop polling after completed/failed/deleted/not found.
- Render a clear visual stepper/status card.
- Show timestamp if available: uploaded_at, processed_at/updated_at.
- Show a generic timeout hint if still queued after a reasonable local window.

Do not implement WebSockets.

## Ticket 14G-05 — Failure and retry behavior

If CV parsing fails:

- Show a user-friendly error.
- Do not expose stack traces.
- Show “Try again” or “Upload another CV” if safe.
- Add admin visibility for failure reason.

Optional if already supported safely:

- Admin action to retry failed CV parse by enqueueing the parse task.

Do not build a full user retry workflow unless existing service boundaries make it small and safe.

## Ticket 14G-06 — Worker health helper

Add a local/admin helper that makes it easier to know whether the worker is running.

Acceptable options:

- Management command: `python manage.py cv_worker_check --settings=config.settings.local`
- Or admin/dashboard local-only diagnostic card.
- Or documentation plus tests if a command is overkill.

Preferred: a small management command that checks Redis/Celery broker connectivity and recent stuck CVs without requiring external services beyond configured Redis.

Do not add production monitoring vendors.

## Ticket 14G-07 — Stuck CV handling

Add safe detection for stuck CVs:

- Queued/processing CV older than a configured threshold.
- Display user-friendly hint.
- Admin list filter/action if appropriate.

Do not auto-delete or auto-retry blindly unless already safe and tested.

## Ticket 14G-08 — Tests

Add or update tests for:

- CV upload enqueues parse task.
- Status endpoint uses `public_id` and rejects internal integer IDs.
- User cannot view another user's CV status.
- Soft-deleted CVs are excluded from user-facing queries.
- Status card renders queued/processing/completed/failed states.
- No `cv.file.url` or raw private file path in templates.
- No raw CV text leak in templates.
- Celery task calls service only, not parsing logic in view.

## Ticket 14G-09 — Documentation

Add/update docs for local dev:

```bash
# Terminal 1
python manage.py runserver --settings=config.settings.local

# Terminal 2
celery -A config worker --loglevel=info --concurrency=2

# Terminal 3, if needed
podman compose up -d redis
# or docker compose up -d redis
```

Include troubleshooting:

- CV stuck queued: worker not running.
- Redis connection refused: start Redis.
- Failed parse: check admin/logs, do not expose stack trace to users.
