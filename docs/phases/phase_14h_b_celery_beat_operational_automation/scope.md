# Scope

## In scope

- Populate `CELERY_BEAT_SCHEDULE` with existing safe Celery task names.
- Add/import Celery schedule helpers such as `crontab` if needed.
- Add tests proving the Beat schedule is registered and references existing task names.
- Add a small management command or test helper only if useful for local verification.
- Add or update docs for running local worker + beat.
- Confirm task implementation still delegates to services.
- Keep schedules conservative to avoid runaway LLM/API/cost usage.

## Suggested scheduled tasks

Use existing tasks if present:

- `apps.jobs.tasks.run_it_job_ingestion`
  - Every 4 hours or nightly, depending current `JobIngestionConfig.frequency_minutes` design.
  - Must respect `JobIngestionConfig.enabled`, `max_total_per_run`, `nightly_max_total`, and enrichment limits.

- `apps.jobs.tasks.mark_stale_and_expired_jobs`
  - Daily.
  - Must not call France Travail.

- `apps.recommendations.tasks.refresh_active_users_recommendations`
  - Nightly.
  - Must read local DB only.

- `apps.privacy.tasks.cleanup_expired_quick_matches`
  - Daily.

- `apps.privacy.tasks.delete_orphaned_cv_files`
  - Weekly.
  - Must use private media safety rules.

- `apps.notifications.tasks.send_weekly_digest`
  - Only schedule if already safe, opt-in, idempotent, and tested.
  - If uncertain, document as deferred rather than adding risky email automation.

## Out of scope

- Tailwind build pipeline.
- Deployment scripts/Procfile.
- Render/Hetzner production setup.
- New recommendation algorithms.
- New LLM prompts.
- New France Travail client behavior.
- New public API.
- UI redesign.
- Multi-country support.
