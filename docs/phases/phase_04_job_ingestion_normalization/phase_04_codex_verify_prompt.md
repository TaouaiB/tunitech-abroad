# Codex verification/fix prompt - Phase 4

Read AGENTS.md first.

You are not the implementation agent. You are the strict verification/fix agent after Gemini implemented Phase 4.

Your job:
Review Phase 4 implementation for architectural compliance, test quality, phase boundaries, typing cleanliness, migrations, and security. Fix only Phase 4 defects. Do not start Phase 5.

Current phase:
Phase 4 - Job Ingestion and Normalization.

Hard boundaries:
- Do not create public `/jobs/` views, URLs, templates, filters, pagination, or user-facing search pages.
- Do not create CV upload/parsing.
- Do not create matching, quick match, recommendations, saved jobs.
- Do not add OpenRouter/LLM calls.
- Do not add email digest/unsubscribe.
- Do not add privacy deletion.
- Do not commit, merge, or push.

Review checklist:

1. Phase scope
- Check `git status --short` and `git diff --stat`.
- Confirm changed files are limited to `apps/jobs`, necessary settings, docs/phases/phase_04, and only justified compatibility tests.
- Reject unrelated template/profile/account changes unless clearly required.

2. Architecture
- Models must not call external APIs.
- Celery tasks must call services only.
- Business logic must be in services.
- FranceTravailClient must not be used by user-facing requests.
- Tests must not call live network.

3. Models/migrations
- Verify JobSource, IngestionRun, RawJobRecord, NormalizedJob, NormalizedJobSkill fields match Phase 4 docs.
- Verify UUID `public_id` on NormalizedJob.
- Verify uniqueness constraints.
- Verify PROTECT/CASCADE/SET_NULL behavior.
- Verify JSONField defaults use callable `dict`/`list`, not mutable literals.
- Verify SearchVectorField and GIN index work on PostgreSQL.
- Verify no bad migration noise or destructive migration.

4. Services
- Fixture ingestion idempotent.
- Payload hash deterministic.
- Classification handles stage/PFE/alternance/CDI/remote/hybrid/on-site/languages.
- Normalization handles missing optional fields and stores failure errors.
- Job skill extraction uses SkillNormalizerService and no LLM.
- Freshness does not let stale logic shadow removed logic.

5. Tests
Run:

source .venv/bin/activate
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py migrate --settings=config.settings.local
python manage.py seed_job_sources --settings=config.settings.local
python manage.py ingest_job_fixtures apps/jobs/fixtures/france_travail_sample_jobs.json --settings=config.settings.local
python manage.py test apps.jobs --settings=config.settings.local
python manage.py test --settings=config.settings.local
python manage.py seed_skills --settings=config.settings.local
python manage.py seed_job_sources --settings=config.settings.local
python manage.py ingest_job_fixtures apps/jobs/fixtures/france_travail_sample_jobs.json --settings=config.settings.local

6. Static diagnostics
Open changed Python files or run the configured type/static checker if available.
Fix red diagnostics properly. Do not hide them with broad `# type: ignore`.

7. Junk check

find . -type d -name "__pycache__" -print
find . -name "*.pyc" -print
find . -maxdepth 3 -name "task.md" -print
find . -maxdepth 3 -name "*.sqlite3" -print
find . -maxdepth 3 -name "celerybeat-schedule*" -print
git status --short
git diff --stat

Remove junk if found.

Allowed fixes:
- Phase 4 models/services/tests/tasks/admin/fixtures/docs.
- Minimal settings changes needed for jobs/django.contrib.postgres.
- Minimal compatibility test update only if an older phase boundary test incorrectly rejects the legal Phase 4 jobs app.

Forbidden fixes:
- Do not implement Phase 5.
- Do not add public pages/URLs/templates.
- Do not solve failures by deleting meaningful tests.
- Do not edit unrelated apps to hide failures.

Final response/report:
- List defects found.
- List fixes made.
- Paste final test results.
- Paste final `git status --short` and `git diff --stat`.
- Confirm no Phase 5 work.
- Confirm no red diagnostics remain or list exact remaining diagnostics.
