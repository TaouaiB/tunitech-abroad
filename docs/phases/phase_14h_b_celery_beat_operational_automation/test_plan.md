# Test Plan

## Unit/config tests

Add or update tests similar to:

- `test_celery_beat_schedule_is_not_empty`
- `test_celery_beat_schedule_contains_job_ingestion`
- `test_celery_beat_schedule_contains_stale_job_cleanup`
- `test_celery_beat_schedule_contains_recommendation_refresh`
- `test_celery_beat_schedule_contains_privacy_cleanup`
- `test_celery_beat_task_names_are_registered`

## Architecture regression tests

Add tests or grep checks for:

- No France Travail usage in public views.
- No OpenRouter usage in views.
- No CV private file leak in templates.
- Scheduled task names map to existing Celery tasks.

## Manual local smoke

Use four terminals if needed:

1. Redis
2. Django runserver
3. Celery worker
4. Celery Beat foreground process

Command examples are in `worker_beat_playbook.md`.
