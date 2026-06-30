# Phase 4 - Job Ingestion and Normalization - acceptance.md

Phase 4 is accepted only when all checks below pass.

## 1. Phase boundary acceptance

Approved changes are limited to Phase 4 scope:

Allowed:

- `apps/jobs/**`
- `config/settings/base.py` only for adding `apps.jobs` / `django.contrib.postgres` if needed
- `docs/phases/phase_04_job_ingestion_normalization/**`
- tests directly needed for Phase 4 compatibility

Not allowed:

- public jobs views, URLs, templates, filters, or pagination
- CV upload/parsing
- matching/quick match
- recommendations/saved jobs
- OpenRouter/LLM
- email digest/unsubscribe
- privacy deletion
- React/Next.js/FastAPI/SQLAlchemy/MongoDB
- real secrets
- live network dependency in tests

## 2. Model acceptance

The following models exist and migrate cleanly:

- `JobSource`
- `IngestionRun`
- `RawJobRecord`
- `NormalizedJob`
- `NormalizedJobSkill`

Required model behavior:

- `JobSource.slug` is unique.
- `RawJobRecord` enforces unique `(source, source_job_id)`.
- `NormalizedJob.public_id` is UUID, unique, non-editable, and indexed.
- `NormalizedJob` enforces unique `(source, source_job_id)` and one normalized job per raw record.
- `NormalizedJobSkill` enforces unique `(job, skill, requirement_type)`.
- `source` deletion is protected where required.
- `skill` deletion is protected when used by `NormalizedJobSkill`.
- `search_vector` exists and has a GIN index.

## 3. Ingestion acceptance

- `seed_job_sources` creates/updates the `france_travail` source idempotently.
- `JobFixtureIngestionService.load_fixture_file(...)` creates an `IngestionRun`.
- Fixture ingestion creates `RawJobRecord` rows.
- Running the same fixture twice does not duplicate records.
- Changed payloads update payload hash and mark records pending for normalization.
- Ingestion counts are accurate enough for operations.
- Synthetic fixture file exists and is France IT-focused.

## 4. Classification acceptance

`JobClassificationService` detects:

- stage/PFE/internship
- alternance/apprentissage
- CDI/CDD/contract where possible
- remote/hybrid/on-site
- internship/junior/mid/senior where possible
- French and English requirement/preference signals

## 5. Normalization acceptance

- Valid raw job normalizes into `NormalizedJob`.
- Missing optional fields do not crash.
- Unusable payload fails gracefully and stores `normalization_error`.
- Re-normalizing the same raw job updates existing `NormalizedJob`, not duplicate.
- `RawJobRecord.normalization_status` updates correctly.
- `NormalizedJob.search_vector` is populated.
- No user-facing search is implemented in this phase.

## 6. Skill extraction acceptance

- Minimal rule-based `JobSkillExtractionService` exists.
- It uses `SkillNormalizerService` from Phase 3.
- It creates/updates `NormalizedJobSkill` rows for known aliases.
- Unknown candidates create/update `UnmatchedSkillCandidate`.
- It is idempotent.
- It does not import or call OpenRouter/LLM.

## 7. Freshness acceptance

`JobFreshnessService.mark_stale_and_expired()` correctly marks:

- expired jobs when `expires_at` is past
- removed jobs when unseen longer than removed threshold
- stale jobs when unseen longer than stale threshold
- active jobs remain active

Removed threshold must not be accidentally shadowed by stale logic.

## 8. Celery task acceptance

- `normalize_raw_job_record(raw_record_id)` exists.
- `mark_stale_and_expired_jobs()` exists.
- Tasks call services only.
- Missing raw IDs are handled safely.
- Tasks do not contain business logic.

## 9. France Travail client acceptance

- `apps/jobs/services/france_travail/client.py` exists.
- It defines the client boundary for future live API calls.
- It can be imported/instantiated without real credentials.
- Tests do not call live France Travail API.
- It does not log secrets.

## 10. Admin acceptance

Admin registrations exist for:

- JobSource
- IngestionRun
- RawJobRecord
- NormalizedJob
- NormalizedJobSkill

Admin import must not trigger external API calls.

## 11. Test acceptance

All commands must pass:

```bash
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
```

## 12. Static/IDE acceptance

Before reporting done:

- Open changed Phase 4 Python files in the IDE.
- No red Pyright diagnostics may remain in changed files.
- Do not silence diagnostics with broad `# type: ignore` unless justified in the report.

## 13. Cleanup acceptance

The following must return no problematic files:

```bash
find . -type d -name "__pycache__" -print
find . -name "*.pyc" -print
find . -maxdepth 3 -name "task.md" -print
find . -maxdepth 3 -name "*.sqlite3" -print
find . -maxdepth 3 -name "celerybeat-schedule*" -print
```

`git status --short` must show only expected Phase 4 changes.

## 14. Stop/Go gate

Do not start Phase 5 until this phase is reviewed and approved by the project owner.
