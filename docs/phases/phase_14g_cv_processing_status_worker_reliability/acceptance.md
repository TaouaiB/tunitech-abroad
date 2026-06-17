# Acceptance Criteria — Phase 14G

Phase 14G is acceptable only if all criteria pass.

## Product behavior

- A user uploading a CV sees a clear upload/queued/processing/result flow.
- The page does not stay on a vague `pending` label without explanation.
- The status UI updates automatically while queued/processing.
- Completed CV processing shows a success state.
- Failed CV processing shows a safe user-friendly failure state.
- Local dev guidance explains that Celery worker must be running.

## Architecture

- Upload/status views remain thin.
- Business/parsing logic stays in services/tasks.
- Celery task calls services only.
- No LLM/OpenRouter calls from views.
- No new matching/recommendation scoring behavior.
- No live France Travail user-search behavior.

## Privacy/security

- CV files remain private.
- No direct `cv.file.url` usage in templates.
- No raw CV text leak in templates.
- User cannot access another user’s CV status.
- Public/user-facing CV routes use UUID `public_id`, not integer IDs.
- `CVUpload.objects` excludes soft-deleted rows in user-facing views.

## Tests

The following must pass:

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test apps.cvs apps.profiles apps.matching apps.recommendations --settings=config.settings.local
python manage.py test --settings=config.settings.local
python manage.py test --settings=config.settings.local --parallel 1
# parallel 1 is optional if the normal full suite is already stable locally; report if skipped and why.
git diff --check
```

## Manual proof

With Redis and Celery running locally:

1. Upload a PDF CV.
2. See queued state immediately.
3. See processing/progress state while task runs, if visible.
4. See completed state without page refresh, or via HTMX polling.
5. Stop Celery, upload another CV, and verify UI clearly says queued/still waiting and gives local-dev hint without crashing.
