# Phase 3 — Skill Taxonomy Foundation — Tasks

## Phase Goal

Build the canonical skill taxonomy foundation used later by job normalization, CV parsing, matching, and recommendations.

Phase 3 creates:

- `apps/skills`
- `Skill`
- `SkillAlias`
- `UnmatchedSkillCandidate`
- `SkillNormalizerService`
- `SkillSeedService`
- `UnmatchedSkillReviewService`
- idempotent seed command
- Django Admin support for skill taxonomy and unmatched skill review
- tests for models, services, seed command, and admin/service review paths

This phase does **not** build jobs, CV parsing, matching, recommendations, LLM, or emails.

---

## Current Project Context

Phase 0 is complete.
Phase 1 is complete.
Phase 2 is complete or must be committed before starting Phase 3.

Current relevant Phase 2 state:

- `apps/accounts` exists with custom `User`.
- `apps/profiles` exists.
- `apps/profiles.ProfileSkill` is a Phase 2 shell using raw skill names. It does **not** link to `skills.Skill` yet.
- `apps/notifications.EmailPreference` exists.
- `apps/privacy.ConsentRecord` exists.
- `apps/analytics.UserEvent` exists.
- `apps/core.SystemSetting` exists.

Do not refactor `profiles.ProfileSkill` in Phase 3 unless explicitly needed for import safety. Skill-to-profile integration belongs to later CV/profile/matching phases.

---

## Hard Scope Boundary

Allowed in Phase 3:

- Create `apps/skills`.
- Add `skills` to `INSTALLED_APPS`.
- Create migrations for `skills` only.
- Create skill taxonomy models.
- Create admin registrations and admin review helpers.
- Create service layer under `apps/skills/services/`.
- Create seed data and seed command.
- Add tests for Phase 3.

Forbidden in Phase 3:

- Do not create `apps/jobs`.
- Do not create job ingestion, raw jobs, normalized jobs, job search, or France Travail clients.
- Do not create `apps/cvs`.
- Do not create CV upload, CV parsing, PDF extraction, or private media logic.
- Do not create matching or recommendations.
- Do not create LLM/OpenRouter integration.
- Do not create email digest, email events, unsubscribe tokens, or real email sending.
- Do not add Celery tasks for jobs/CV/matching.
- Do not modify public URL structure for jobs/matches/CV.
- Do not expose integer IDs publicly.
- Do not commit, merge, or push.

---

## Tickets

### TTA-0301 — Create `Skill` model

**Priority:** P0  
**Type:** model

Create canonical skill model.

Required location:

```text
apps/skills/models.py
```

Required fields:

- `canonical_name` — unique, human-readable skill name, example `Python`, `Django`, `PostgreSQL`
- `slug` — unique slug, example `python`, `django`, `postgresql`
- `category` — choice field
- `is_active` — boolean, default `True`
- `source` — choice/string field, examples `manual`, `seed`, `esco`, `admin`, `imported`
- `esco_uri` — optional URL field
- `created_at`
- `updated_at`

Required categories:

```text
programming_language
frontend
backend
database
devops
cloud
testing
data_ai
mobile
tools
methodology
soft_skill
security
other
```

Required constraints/indexes:

- unique `canonical_name`
- unique `slug`
- indexes for `slug`, `canonical_name`, `category`, `is_active`, `source`

Rules:

- Do not normally delete skills. Use `is_active=False`.
- `__str__` should return `canonical_name`.
- Slug generation should be deterministic and safe.

Acceptance:

- Duplicate `canonical_name` rejected.
- Duplicate `slug` rejected.
- Inactive skills remain queryable.

---

### TTA-0302 — Create `SkillAlias` model

**Priority:** P0  
**Type:** model

Create alias model mapping raw skill text to canonical skills.

Required fields:

- `skill` — ForeignKey to `Skill`, protected from deletion
- `alias` — original alias text, example `ReactJS`, `Postgres`, `Python3`
- `normalized_alias` — unique normalized lowercase/stripped text
- `language` — `fr`, `en`, `unknown`, optional/default `unknown`
- `created_at`
- `updated_at`

Required constraints/indexes:

- unique `normalized_alias`
- indexes for `skill`, `normalized_alias`, `language`

Acceptance:

- `ReactJS` can map to `React`.
- `Postgres` can map to `PostgreSQL`.
- Duplicate normalized alias is rejected.

---

### TTA-0303 — Create `UnmatchedSkillCandidate` model

**Priority:** P0  
**Type:** model

Create model for raw skill terms that do not match the canonical taxonomy.

Required fields:

- `raw_skill_text`
- `normalized_text`
- `source_type` — choices: `cv`, `job`, `quick_match`, `manual`, `admin`, `unknown`
- `source_model` — optional string, example `CVUpload`, `NormalizedJob`
- `source_object_id` — optional integer
- `occurrence_count` — positive integer, default `1`
- `status` — choices: `pending`, `mapped`, `ignored`
- `mapped_skill` — nullable FK to `Skill`, `SET_NULL`
- `reviewed_by` — nullable FK to `settings.AUTH_USER_MODEL`, `SET_NULL`
- `reviewed_at`
- `created_at`
- `updated_at`

Required constraints/indexes:

- unique constraint on `normalized_text` + `source_type`
- indexes for `normalized_text`, `source_type`, `status`, `mapped_skill`, `reviewed_by`, `occurrence_count`, `created_at`

Acceptance:

- Unknown candidate can be created.
- Repeated unknown candidate increments occurrence count through service logic.
- Candidate can be marked `mapped` or `ignored`.

---

### TTA-0304 — Implement `SkillNormalizerService`

**Priority:** P0  
**Type:** service

Required location:

```text
apps/skills/services/normalizer.py
```

Purpose:

Map raw skill strings to canonical `Skill` records using aliases.

Required contract:

```python
SkillNormalizerService.normalize_many(
    raw_skills: list[str],
    source_type: str,
    source_id: int | None = None,
) -> SkillExtractionResult
```

Create a simple result dataclass, for example:

```python
@dataclass
class SkillExtractionResult:
    canonical_skills: list[Skill]
    unmatched_candidates: list[UnmatchedSkillCandidate]
    raw_candidates: list[str]
    confidence: float | None = None
```

Required processing rules:

1. Ignore empty/null skill values.
2. Lowercase.
3. Strip punctuation where safe.
4. Normalize accents.
5. Collapse whitespace.
6. Exact lookup against `SkillAlias.normalized_alias`.
7. Return canonical `Skill` if matched.
8. Create/update `UnmatchedSkillCandidate` if not matched.
9. Repeated unmatched skill increments `occurrence_count`, not duplicate rows.
10. Do **not** auto-create `Skill` from unknown raw text.
11. Deduplicate canonical skills in returned result.
12. Keep service idempotent and transaction-safe.

Required source type values:

```text
cv
job
quick_match
manual
admin
unknown
```

Acceptance:

- `ReactJS` normalizes to `React` when alias exists.
- `Postgres` normalizes to `PostgreSQL` when alias exists.
- `Python3` normalizes to `Python` when alias exists.
- Unknown skill creates pending `UnmatchedSkillCandidate`.
- Repeated unknown skill increments count.
- Service does not auto-create canonical skills.

---

### TTA-0305 — Implement initial skill seed command

**Priority:** P0  
**Type:** backend/service

Required service location:

```text
apps/skills/services/seed.py
```

Required management command:

```text
apps/skills/management/commands/seed_skills.py
```

Required command:

```bash
python manage.py seed_skills --settings=config.settings.local
```

Required behavior:

- Use `SkillSeedService.seed_initial_taxonomy()`.
- Seed **200–300 canonical skills**.
- Seed useful aliases for those skills.
- Target **at least 500 aliases** if practical.
- Must be idempotent.
- Running it twice must not duplicate skills or aliases.
- Use `update_or_create` / `get_or_create` safely.
- Return useful count summary to stdout.

Seed categories must cover at least:

- programming languages
- frontend
- backend
- databases
- DevOps
- cloud
- testing
- data/AI
- mobile
- tools
- methodology
- soft skills
- security

Seed examples that must work in tests:

- `ReactJS` -> `React`
- `Postgres` -> `PostgreSQL`
- `Python3` -> `Python`
- `JS` -> `JavaScript`
- `TS` -> `TypeScript`
- `Node` -> `Node.js`
- `Tailwind` -> `Tailwind CSS`
- `Docker Compose` -> `Docker Compose`

Acceptance:

- Seed command exists.
- Seed command is idempotent.
- Core IT categories are populated.
- Tests prove idempotency.

---

### TTA-0306 — Add admin skill review support

**Priority:** P1  
**Type:** admin/service

Required service location:

```text
apps/skills/services/review.py
```

Required service contracts:

```python
UnmatchedSkillReviewService.map_candidate(
    candidate_id: int,
    skill_id: int,
    reviewed_by: User,
) -> UnmatchedSkillCandidate

UnmatchedSkillReviewService.ignore_candidate(
    candidate_id: int,
    reviewed_by: User,
) -> UnmatchedSkillCandidate
```

Required rules:

- Only staff users can review.
- Mapping sets:
  - `status="mapped"`
  - `mapped_skill`
  - `reviewed_by`
  - `reviewed_at`
- Ignoring sets:
  - `status="ignored"`
  - `reviewed_by`
  - `reviewed_at`
- Mapping may create a `SkillAlias` from candidate text if safe and not already present.
- Do not create a new `Skill` automatically.

Admin requirements:

- Register `Skill`.
- Register `SkillAlias`.
- Register `UnmatchedSkillCandidate`.
- Add useful `list_display`, `search_fields`, `list_filter`, `readonly_fields`.
- Add admin actions where safe:
  - mark selected unmatched candidates as ignored
  - mark selected candidates as mapped only if `mapped_skill` is already set
- Admin should not expose secrets.

Acceptance:

- Admin can inspect skills and aliases.
- Admin can inspect pending unmatched candidates.
- Staff can map candidate to an existing skill through service/admin path.
- Staff can ignore candidate through service/admin path.
- Non-staff cannot use review service.

---

## Required Test Coverage

Add tests under `apps/skills/tests/` or equivalent project test structure.

Minimum tests:

### Model tests

- `Skill` duplicate slug rejected.
- `Skill` duplicate canonical name rejected.
- `SkillAlias` duplicate normalized alias rejected.
- `UnmatchedSkillCandidate` unique normalized text + source type enforced.

### Normalizer service tests

- `ReactJS` -> `React`.
- `Postgres` -> `PostgreSQL`.
- `Python3` -> `Python`.
- accents/punctuation/case/spacing normalized.
- unknown skill creates `UnmatchedSkillCandidate`.
- repeated unknown skill increments `occurrence_count`.
- unknown skill does not auto-create `Skill`.
- duplicate raw inputs return one canonical skill.

### Seed tests

- seed service/command creates skills.
- seed service/command creates aliases.
- running seed twice does not duplicate rows.
- core required aliases exist after seed.

### Review service/admin tests

- staff can map candidate.
- staff can ignore candidate.
- non-staff cannot map/ignore.
- mapping creates alias when safe.

### Project checks

Must pass:

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py migrate --settings=config.settings.local
python manage.py test --settings=config.settings.local
python manage.py seed_skills --settings=config.settings.local
python manage.py seed_skills --settings=config.settings.local
```

Also run junk checks:

```bash
find . -type d -name "__pycache__" -print
find . -name "*.pyc" -print
find . -maxdepth 3 -name "task.md" -print
find . -maxdepth 3 -name "*.sqlite3" -print
find . -maxdepth 3 -name "celerybeat-schedule*" -print
git status --short
```

Do not leave generated junk in the repo.

---

## Stop/Go Gate

Phase 3 is done only when:

- skill taxonomy models exist and migrate cleanly
- aliases map to canonical skills
- unknown skills go to review queue
- repeated unknown skills increment count
- seed command is idempotent
- admin review support exists
- tests pass
- no future phase work exists
- no secrets/junk files are introduced

Do not continue to Phase 4 until this is reviewed and approved.
