# Phase 4 - Job Ingestion and Normalization - prompt.md

You are implementing Phase 4 for TuniTech Abroad.

## Read first

Read these files before coding:

```text
AGENTS.md
docs/phases/phase_04_job_ingestion_normalization/tasks.md
docs/phases/phase_04_job_ingestion_normalization/acceptance.md
docs/phases/phase_04_job_ingestion_normalization/agent_report_template.md
```

Also respect the project PDFs as source of truth, especially:

- Database Schema v1
- Service Contracts v1
- Data Flow / Sequence Diagrams v1
- Implementation Roadmap v1
- MVP Backlog v1

## Current phase

Phase 4 - Job Source, Raw Jobs, Fixtures, Normalization.

Phase 4 is allowed to create the `jobs` app and job ingestion/normalization foundation.

## Non-negotiable architecture rules

- Use Django, Django ORM, PostgreSQL, Redis/Celery.
- Do not use React, Next.js, Angular, FastAPI, SQLAlchemy, MongoDB, or SPA architecture.
- Business logic goes in services.
- Celery tasks call services only.
- Models do not call external APIs.
- No OpenRouter/LLM calls in Phase 4.
- No live France Travail API calls from user-facing requests.
- Public URLs must use UUID `public_id`, never integer IDs. Phase 4 should not create public job URLs yet.
- No secrets in code, tests, logs, or docs.

## Hard boundary

Do **not** start Phase 5.

Do not implement:

- public `/jobs/` list/detail views
- URL routes for jobs
- public templates/job cards/search filters/pagination
- user-facing PostgreSQL search service beyond preparing `search_vector`
- CV upload/parsing
- matching/quick match
- recommendations/saved jobs
- OpenRouter/LLM
- email digest
- privacy deletion

## Implementation plan

Work through all tickets in `tasks.md` automatically, in order:

1. Create `apps/jobs` structure.
2. Add `JobSource`, `IngestionRun`, `RawJobRecord`, `NormalizedJob`, `NormalizedJobSkill` models.
3. Add migrations.
4. Add source seeding command.
5. Add fixture ingestion service and fixture command.
6. Add synthetic France Travail-like sample fixture data.
7. Add classification service.
8. Add normalization service.
9. Add minimal rule-based job skill extraction service using Phase 3 SkillNormalizerService only. No LLM.
10. Add freshness service.
11. Add Celery tasks that call services only.
12. Add FranceTravailClient skeleton, no required credentials, no live network in tests.
13. Add admin registrations.
14. Add tests.
15. Run final checks and fill the agent report.

## Model details

Follow field names and constraints from `tasks.md` and Database Schema v1.

Important choices:

- Use `BigAutoField` project default.
- Use UUID `public_id` on `NormalizedJob`.
- Use `models.PROTECT` for source and skill relations where specified.
- Use `JSONField(default=dict)` or `JSONField(default=list)` safely; never use mutable `{}` or `[]` directly.
- Use `SearchVectorField` for `NormalizedJob.search_vector` and a GIN index.
- Use deterministic SHA256 canonical JSON hashing for raw payloads.

## Fixture rules

Create `apps/jobs/fixtures/france_travail_sample_jobs.json`.

The fixture must be synthetic and France IT-focused. Include around 8-12 jobs covering:

- PFE / stage
- alternance / apprentissage
- junior CDI
- CDD or mission contract
- remote
- hybrid
- on-site
- Python/Django/PostgreSQL
- Java/Spring
- JavaScript/TypeScript/React
- DevOps/Docker/Linux
- data/AI basics if useful

Do not copy real job descriptions.

## Services

### Fixture ingestion

`JobFixtureIngestionService.load_fixture_file(path: str, source_slug: str = "france_travail") -> IngestionRun`

Must be idempotent.

### Classification

`JobClassificationService.classify(payload: dict, description: str, title: str) -> dict`

Must detect job type, remote type, experience level, and French/English requirements from robust keyword rules.

### Normalization

`JobNormalizationService.normalize(raw_record: RawJobRecord) -> NormalizedJob`

Must update raw normalization status and errors.

### Job skill extraction

`JobSkillExtractionService.extract_for_job(job: NormalizedJob) -> SkillExtractionResult`

Use rule-based extraction and SkillNormalizerService. No LLM.

### Freshness

`JobFreshnessService.mark_stale_and_expired(now=None) -> dict`

Must handle expired, removed, stale, active correctly.

## France Travail client skeleton

Create:

```text
apps/jobs/services/france_travail/client.py
```

The skeleton may define methods and safe exceptions. It must not require credentials for test runs. Tests must not perform network calls.

## Celery tasks

Create tasks in `apps/jobs/tasks.py`:

- `normalize_raw_job_record(raw_record_id: int)`
- `mark_stale_and_expired_jobs()`

Tasks must call services only.

## Required tests

Create tests under `apps/jobs/tests/`.

Minimum coverage:

- model uniqueness and protected relations
- deterministic payload hashing
- source seeding idempotency
- fixture ingestion creates/updates records idempotently
- classification stage/PFE/alternance/CDI/remote/hybrid/on-site/languages
- normalization success, missing optional fields, failed unusable payload, idempotency
- search_vector populated
- rule-based skill extraction known/unknown/idempotent
- freshness expired/stale/removed/active
- tasks call services only / handle missing raw ID safely
- no live network dependency

## Final commands

Run exactly:

```bash
source .venv/bin/activate
python manage.py makemigrations jobs --settings=config.settings.local
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

Then run:

```bash
find . -type d -name "__pycache__" -print
find . -name "*.pyc" -print
find . -maxdepth 3 -name "task.md" -print
find . -maxdepth 3 -name "*.sqlite3" -print
find . -maxdepth 3 -name "celerybeat-schedule*" -print
git status --short
git diff --stat
```

Remove junk files if found.

## Report

Fill:

```text
docs/phases/phase_04_job_ingestion_normalization/agent_report.md
```

Use the template exactly.

Do not commit. Do not merge. Do not push.
