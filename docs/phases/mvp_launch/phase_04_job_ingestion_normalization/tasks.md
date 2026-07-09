# Phase 4 - Job Ingestion and Normalization - tasks.md

## Phase goal

Build the job ingestion foundation for France-first IT jobs without making the public user search depend on live France Travail API availability.

Phase 4 turns external/fixture job payloads into local PostgreSQL records:

`JobSource -> IngestionRun -> RawJobRecord -> NormalizedJob -> NormalizedJobSkill`

The output of this phase is local, normalized, searchable job data ready for Phase 5 public job search.

## Source-of-truth documents

Follow these project documents:

- `AGENTS.md`
- `docs/phases/phase_04_job_ingestion_normalization/tasks.md`
- `docs/phases/phase_04_job_ingestion_normalization/prompt.md`
- `docs/phases/phase_04_job_ingestion_normalization/acceptance.md`
- `docs/phases/phase_04_job_ingestion_normalization/agent_report_template.md`
- Project PDFs: Database Schema v1, Service Contracts v1, Data Flow / Sequence Diagrams v1, Implementation Roadmap v1, MVP Backlog v1

## Hard phase boundary

Phase 4 is not public job search, not CV, not matching, not recommendations, and not LLM.

Do **not** implement:

- Phase 5 public `/jobs/` pages, public job detail pages, filters, pagination, templates, or URL routes
- User-facing job search views
- CV upload or CV parsing
- Match scoring, quick match, recommendations, saved jobs
- OpenRouter/LLM calls
- Email digest or unsubscribe flows
- Privacy deletion workflows
- Live France Travail calls from any user-facing request
- React, Next.js, Angular, FastAPI, SQLAlchemy, MongoDB, SPA architecture

Allowed:

- Create `apps/jobs`
- Create job ingestion/normalization models, services, Celery tasks, admin registrations, fixture data, tests
- Create a France Travail client skeleton under `apps/jobs/services/france_travail/client.py`, but no tests may depend on the live API

## Architecture rules

- Views stay thin. In Phase 4 there should normally be no public views.
- Business logic goes in services.
- Celery tasks call services only.
- Models store data and do not call external APIs.
- Public identifiers use UUID `public_id` where public routing will exist later.
- No live France Travail API calls during normal user job search.
- Phase 4 tests must not call external networks.
- Use Django ORM and PostgreSQL features. Do not introduce SQLAlchemy.

---

## TTA-0400 - Create jobs app structure

### Goal
Create the jobs app and service/test folder structure.

### Required work

Create:

```text
apps/jobs/
apps/jobs/services/
apps/jobs/services/france_travail/
apps/jobs/management/commands/
apps/jobs/fixtures/
apps/jobs/tests/
```

Register app in `INSTALLED_APPS` using config class:

```python
"apps.jobs.apps.JobsConfig"
```

If using `SearchVectorField`, ensure `django.contrib.postgres` is installed in `INSTALLED_APPS` if not already present.

### Acceptance

- `apps.jobs` imports cleanly.
- `python manage.py check --settings=config.settings.local` passes.
- No Phase 5/public views are created.

---

## TTA-0401 - Create JobSource and IngestionRun models

### Goal
Store external job source configuration and ingestion run history.

### Models

Create `apps/jobs/models.py` with model choices and models.

#### `JobSource`

Fields:

- `name`: CharField
- `slug`: SlugField, unique, indexed. MVP slug: `france_travail`
- `base_url`: URLField, blank allowed
- `source_type`: choices: `api`, `manual`, `fixture`
- `is_active`: BooleanField default true
- `last_successful_sync_at`: DateTimeField null/blank
- `created_at`, `updated_at`

Constraints/indexes:

- unique `slug`
- index `slug`, `is_active`, `last_successful_sync_at`

#### `IngestionRun`

Fields:

- `source`: FK `JobSource`, `on_delete=PROTECT`
- `status`: choices `running`, `success`, `partial_success`, `failed`
- `trigger_type`: choices `scheduled`, `manual_admin`, `startup_fixture`, `retry`
- `started_at`: DateTimeField
- `finished_at`: DateTimeField null/blank
- `search_params_json`: JSONField default dict, blank true
- `fetched_count`, `created_count`, `updated_count`, `unchanged_count`, `marked_stale_count`, `marked_expired_count`, `error_count`: PositiveIntegerField default 0
- `error_message`: TextField blank
- `created_at`

Indexes:

- source, status, started_at, finished_at, trigger_type

### Services/commands

Create a small source seed path:

- `apps/jobs/services/source_seed.py` or equivalent
- management command: `python manage.py seed_job_sources --settings=config.settings.local`

It must create/update the `france_travail` source idempotently.

### Tests

- `JobSource.slug` unique.
- `IngestionRun` links to source.
- `seed_job_sources` is idempotent.

---

## TTA-0402 - Create RawJobRecord model

### Goal
Store original external job payloads before normalization.

### Model: `RawJobRecord`

Fields:

- `source`: FK `JobSource`, `on_delete=PROTECT`
- `source_job_id`: CharField
- `raw_payload_json`: JSONField
- `payload_hash`: CharField length 64, indexed. SHA256 canonical JSON.
- `first_seen_at`: DateTimeField
- `last_seen_at`: DateTimeField
- `last_fetched_at`: DateTimeField
- `source_status`: CharField blank
- `normalization_status`: choices `pending`, `success`, `failed`, `skipped_unchanged`; default `pending`
- `normalization_error`: TextField blank
- `ingestion_run`: FK `IngestionRun`, null/blank, `on_delete=SET_NULL`
- `created_at`, `updated_at`

Constraints/indexes:

- unique `(source, source_job_id)`
- indexes: source, source_job_id, payload_hash, last_seen_at, last_fetched_at, normalization_status, ingestion_run

### Helper

Implement deterministic payload hashing:

```python
hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()
```

Place in a service/helper module, not in the model.

### Tests

- Duplicate `(source, source_job_id)` rejected.
- Payload hash is deterministic independent of key order.
- Payload hash changes when payload changes.

---

## TTA-0403 - Create NormalizedJob and NormalizedJobSkill models

### Goal
Store clean, local, searchable jobs and canonical job skills.

### Model: `NormalizedJob`

Fields:

- `public_id`: UUIDField default uuid4, unique, editable false, db_index true
- `source`: FK `JobSource`, `on_delete=PROTECT`
- `raw_record`: OneToOneField `RawJobRecord`, `on_delete=CASCADE`
- `source_job_id`: CharField
- `title`: CharField
- `company_name`: CharField blank
- `location`: CharField blank
- `country`: CharField default `FR`
- `city`: CharField blank
- `department`: CharField blank
- `region`: CharField blank
- `contract_type`: CharField blank
- `remote_type`: choices `remote`, `hybrid`, `on_site`, `unknown`
- `job_type`: choices `internship`, `full_time_job`, `apprenticeship`, `contract`, `unknown`
- `experience_level`: choices `internship`, `junior`, `mid_level`, `senior`, `unknown`
- `description`: TextField
- `source_url`: URLField blank
- `published_at`: DateTimeField null/blank
- `expires_at`: DateTimeField null/blank
- `first_seen_at`, `last_seen_at`, `last_fetched_at`: DateTimeField
- `status`: choices `active`, `stale`, `expired`, `removed`, `archived`, default `active`
- `normalization_version`: CharField default `ft_v1`
- `skill_extraction_status`: choices `pending`, `success`, `failed`, `not_enough_text`, default `pending`
- `required_skills_json`: JSONField default list, blank true
- `optional_skills_json`: JSONField default list, blank true
- `language_requirements_json`: JSONField default dict, blank true
- `search_vector`: SearchVectorField null/blank
- `created_at`, `updated_at`

Constraints/indexes:

- unique `(source, source_job_id)`
- unique `raw_record`
- unique `public_id`
- indexes for public_id, source, source_job_id, status, job_type, contract_type, remote_type, experience_level, country/city/department/region, published_at/expires_at, last_seen_at/last_fetched_at
- GIN index for search_vector

### Model: `NormalizedJobSkill`

Fields:

- `job`: FK `NormalizedJob`, `on_delete=CASCADE`
- `skill`: FK `skills.Skill`, `on_delete=PROTECT`
- `requirement_type`: choices `required`, `optional`, `detected`, `unknown`
- `source`: choices `rule`, `llm`, `admin`, `source_api`
- `confidence`: DecimalField max_digits 4 decimal_places 3 null/blank
- `created_at`

Constraints/indexes:

- unique `(job, skill, requirement_type)`
- indexes: job, skill, requirement_type, source, confidence

### Tests

- `NormalizedJob.public_id` is a UUID and unique.
- Duplicate job skill rows are prevented.
- `Skill` deletion is protected when used by job skill.

---

## TTA-0404 - Implement JobFixtureIngestionService

### Goal
Load synthetic France Travail-like fixture payloads into `RawJobRecord` for development and tests.

### Required files

- `apps/jobs/services/fixture_ingestion.py`
- `apps/jobs/fixtures/france_travail_sample_jobs.json`
- optional management command: `ingest_job_fixtures`

### Rules

- Fixture payloads must be synthetic, realistic, France IT-focused, and include internships/PFE/junior jobs.
- No copyrighted real job descriptions.
- No live API calls.
- Use same `RawJobRecord` path as real ingestion.
- Compute payload hash.
- Existing records are updated, not duplicated.
- Changed fixture updates `payload_hash`, `last_seen_at`, `last_fetched_at`, and `normalization_status=pending` if changed.
- Unchanged fixture increments `unchanged_count` and does not duplicate.

### Suggested command

```bash
python manage.py ingest_job_fixtures apps/jobs/fixtures/france_travail_sample_jobs.json --settings=config.settings.local
```

### Tests

- Fixture ingestion creates raw records.
- Running same fixture twice does not duplicate records.
- Changed fixture updates payload hash and run counts.
- IngestionRun status/counts are correct.

---

## TTA-0405 - Implement JobClassificationService

### Goal
Classify job type, remote type, experience level, and language requirements.

### File

`apps/jobs/services/classification.py`

### Contract

```python
JobClassificationService.classify(payload: dict, description: str, title: str) -> dict
```

Return:

```python
{
    "job_type": "internship" | "full_time_job" | "apprenticeship" | "contract" | "unknown",
    "remote_type": "remote" | "hybrid" | "on_site" | "unknown",
    "experience_level": "internship" | "junior" | "mid_level" | "senior" | "unknown",
    "language_requirements": {
        "french": "required" | "preferred" | "unknown",
        "english": "required" | "preferred" | "unknown",
    },
}
```

### Rules

Detect at least:

- `stage`, `stagiaire`, `PFE`, `fin d'études` -> internship
- `alternance`, `apprentissage` -> apprenticeship
- `CDI`, `CDD` -> full-time/contract where possible
- `freelance`, `mission` -> contract where possible
- `télétravail`, `remote`, `à distance` -> remote
- `hybride`, `hybrid` -> hybrid
- `présentiel`, `sur site`, `on-site` -> on_site
- French/English required/preferred from text signals

### Tests

- Stage/PFE detected as internship.
- Alternance/apprentissage detected as apprenticeship.
- CDI/CDD detected where possible.
- Remote/hybrid/on-site detected.
- French/English required/preferred detection works.

---

## TTA-0406 - Implement JobNormalizationService

### Goal
Normalize `RawJobRecord` into `NormalizedJob` defensively.

### File

`apps/jobs/services/normalization.py`

### Contract

```python
JobNormalizationService.normalize(raw_record: RawJobRecord) -> NormalizedJob
```

### Rules

- Read `raw_payload_json` defensively.
- Support France Travail-like keys but tolerate missing values.
- Map title, company, location, contract type, description, dates, source URL.
- Use `JobClassificationService`.
- Create/update `NormalizedJob` idempotently.
- Populate `search_vector` using PostgreSQL full-text search.
- Update raw record status:
  - success on success
  - failed and `normalization_error` on failure
  - skipped_unchanged only when intentionally skipped
- Missing optional fields must not crash.
- A missing title or unusable payload should fail gracefully and store error.

### Search vector weights

Prepare the field for Phase 5:

- title = A
- required skills = A
- optional skills = B
- company = B
- location = C
- description = D

At Phase 4, it is acceptable to include title/company/location/description immediately and leave skills included once job skill extraction runs.

### Tests

- Valid raw job normalizes successfully.
- Missing company/location handled.
- Failed normalization stores error.
- Re-normalizing same raw job updates existing `NormalizedJob`, does not duplicate.
- Search vector is populated.

---

## TTA-0407 - Implement minimal rule-based JobSkillExtractionService

### Goal
Attach canonical skills to normalized jobs using Phase 3 `SkillNormalizerService`.

### File

`apps/jobs/services/skill_extraction.py`

### Contract

```python
JobSkillExtractionService.extract_for_job(job: NormalizedJob) -> SkillExtractionResult
```

### Rules

- Rule-based only in Phase 4.
- No LLM calls.
- Extract candidates from title + description + raw payload skills if present.
- Use existing `SkillAlias` values as deterministic candidates where practical.
- Call `SkillNormalizerService.normalize_many(raw_skills, source_type="job", source_id=job.id)`.
- Upsert `NormalizedJobSkill` rows.
- Update `required_skills_json`, `optional_skills_json`, and `skill_extraction_status`.
- Unknown terms must go through `UnmatchedSkillCandidate`, not auto-create `Skill`.

### Tests

- Known alias in description creates `NormalizedJobSkill`.
- Unknown skill creates/updates `UnmatchedSkillCandidate`.
- Extraction is idempotent.
- No LLM/OpenRouter import or call exists.

---

## TTA-0408 - Implement JobFreshnessService

### Goal
Mark jobs active, stale, expired, or removed.

### File

`apps/jobs/services/freshness.py`

### Contract

```python
JobFreshnessService.mark_stale_and_expired(now=None) -> dict
```

### Rules

- If `expires_at` exists and is in the past -> `expired`
- Else if `last_seen_at` older than stale threshold -> `stale`
- Else if `last_seen_at` older than removed threshold -> `removed`
- Else -> active

Default thresholds:

- stale after 24 hours
- removed after 72 hours

Important: the removed check must not be shadowed by the stale check. Check the older/removed threshold before stale, or use clear query conditions.

### Tests

- Past `expires_at` marks expired.
- `last_seen_at` older than removed threshold marks removed.
- `last_seen_at` older than stale threshold marks stale.
- Fresh jobs remain active.

---

## TTA-0409 - Add ingestion Celery tasks

### Goal
Create Celery tasks that call services only.

### File

`apps/jobs/tasks.py`

### Required tasks

```python
normalize_raw_job_record(raw_record_id: int)
mark_stale_and_expired_jobs()
```

Optional if fixture command exists:

```python
ingest_fixture_jobs(path: str)
```

### Rules

- Tasks must call services only.
- Tasks must not contain normalization logic.
- Tasks must not contain classification logic.
- Tasks must handle missing IDs safely and log summary only.
- No external API secrets or payloads in logs.

### Tests

- Task calls normalization service.
- Task handles missing raw record safely.
- Freshness task calls `JobFreshnessService`.

---

## TTA-0410 - Add FranceTravailClient skeleton

### Goal
Create the client boundary without depending on live France Travail availability.

### File

`apps/jobs/services/france_travail/client.py`

### Rules

- Owns external HTTP calls later.
- No views call this client.
- No tests call live API.
- It may be a skeleton with methods and domain exceptions.
- It must not require real credentials to run tests.
- It must not print/log secrets.

### Contract

```python
FranceTravailClient.search_offers(params: dict) -> dict
FranceTravailClient.get_offer_detail(source_job_id: str) -> dict
```

### Tests

- Client can be instantiated without real credentials.
- Methods fail safely if not configured, or are mockable without network.

---

## TTA-0411 - Admin registrations

### Goal
Allow admin inspection and review of ingestion data.

### Required admin

Register:

- JobSource
- IngestionRun
- RawJobRecord
- NormalizedJob
- NormalizedJobSkill

### Rules

- Raw payload display should be safe/truncated.
- Avoid admin actions that perform live API calls.
- Useful filters/search fields for source/status/job_type/remote_type/company/title.

### Tests

- Admin registrations import cleanly.

---

## TTA-0412 - Final cleanup and report

### Required checks

Run:

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

Junk/scope check:

```bash
find . -type d -name "__pycache__" -print
find . -name "*.pyc" -print
find . -maxdepth 3 -name "task.md" -print
find . -maxdepth 3 -name "*.sqlite3" -print
find . -maxdepth 3 -name "celerybeat-schedule*" -print
git status --short
git diff --stat
```

### Expected final state

- Full tests pass.
- No red diagnostics in changed files.
- No Phase 5 public pages or URLs.
- No CV/matching/recommendations/LLM/email work.
- No secrets.
- No review artifacts committed.
- Agent report completed.
