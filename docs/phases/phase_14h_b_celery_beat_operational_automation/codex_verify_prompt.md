# Codex Verification Prompt — Phase 14H-B

Verify Phase 14H-B thoroughly.

Do not commit.
Do not deploy.
Do not start Tailwind build.
Do not start Phase 14H-C or 14I.

Read:

- `docs/phases/phase_14h_b_celery_beat_operational_automation/acceptance.md`
- `docs/phases/phase_14h_b_celery_beat_operational_automation/boundaries.md`
- `docs/phases/phase_14h_b_celery_beat_operational_automation/regression_security_checks.md`
- `config/settings/base.py`
- `config/celery.py`
- `apps/jobs/tasks.py`
- `apps/recommendations/tasks.py`
- `apps/privacy/tasks.py`
- relevant tests

Verification checklist:

1. `CELERY_BEAT_SCHEDULE` is populated and no longer `{}`.
2. Every scheduled task name exists in the Celery app registry or is an importable task.
3. Scheduled tasks call services only and do not contain new heavy business logic.
4. Public job search still reads only PostgreSQL.
5. No OpenRouter or France Travail calls from Django views/templates.
6. No CV file URL or raw CV text leaks.
7. Ingestion/enrichment schedule respects config and budgets.
8. No email digest is scheduled unless proven opt-in/idempotent.
9. No Tailwind/deployment changes were made.

Run:

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test apps.core apps.jobs apps.recommendations apps.privacy --settings=config.settings.local
python manage.py test --settings=config.settings.local --parallel 1
git diff --check
git diff -- . ':!.env' | grep -iE "OPENROUTER_API_KEY|FRANCE_TRAVAIL_CLIENT_SECRET|client_secret|access_token|password|secret" || echo "OK: no obvious secrets in diff"
grep -R "FranceTravailClient\|france_travail" apps/*/views.py templates -n 2>/dev/null || true
grep -R "OpenRouterClient\|OPENROUTER\|run_llm\|llm" apps/*/views.py templates -n 2>/dev/null || true
grep -R "file.url\|cv.file.url\|upload.file.url\|raw_text\|extracted_text" templates apps -n 2>/dev/null || true
grep -R "CELERY_BEAT_SCHEDULE = {}" config -n || true
```

If issues are found, fix Phase 14H-B only, then rerun checks.

Final verdict must be exactly:

- `FINAL_VERDICT: FAIL`
- `FINAL_VERDICT: BLOCKED_HUMAN_VISUAL_SIGNOFF`
