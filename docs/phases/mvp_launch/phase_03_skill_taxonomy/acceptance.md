# Phase 3 — Skill Taxonomy Foundation — Acceptance Criteria

Phase 3 is accepted only if all checks below pass.

---

## 1. Scope Acceptance

Must be true:

- `apps/skills` exists.
- `Skill`, `SkillAlias`, and `UnmatchedSkillCandidate` exist.
- `SkillNormalizerService` exists.
- `SkillSeedService` exists.
- `UnmatchedSkillReviewService` exists.
- `seed_skills` management command exists.
- Django Admin registrations exist for the three skill models.

Must not exist unless already created in earlier phases:

- `apps/jobs`
- `apps/cvs`
- `apps/matching`
- `apps/recommendations`
- `apps/llm`
- job ingestion tasks
- CV parsing tasks
- match scoring
- recommendations
- OpenRouter calls
- email digest implementation

No Phase 4 work is allowed.

---

## 2. Model Acceptance

### Skill

Required:

- `canonical_name` unique.
- `slug` unique.
- `category` choices exist.
- `is_active` exists.
- `source` exists.
- `esco_uri` optional.
- timestamps exist.
- useful indexes exist.

Pass conditions:

- duplicate slug is rejected.
- duplicate canonical name is rejected.
- inactive skill remains stored.

### SkillAlias

Required:

- `skill` FK to `Skill`.
- `alias` exists.
- `normalized_alias` unique.
- `language` exists.
- timestamps exist.

Pass conditions:

- alias can map raw input to canonical skill.
- duplicate normalized alias is rejected.

### UnmatchedSkillCandidate

Required:

- `raw_skill_text`
- `normalized_text`
- `source_type`
- `source_model`
- `source_object_id`
- `occurrence_count`
- `status`
- `mapped_skill`
- `reviewed_by`
- `reviewed_at`
- timestamps
- unique `normalized_text` + `source_type`

Pass conditions:

- unknown candidate can be created.
- duplicates are controlled by unique constraint and service logic.

---

## 3. Service Acceptance

### SkillNormalizerService

Must pass:

- `ReactJS` -> `React`
- `Postgres` -> `PostgreSQL`
- `Python3` -> `Python`
- case/spacing/punctuation normalization works
- accent normalization works
- unknown skill creates pending `UnmatchedSkillCandidate`
- repeated unknown skill increments `occurrence_count`
- unknown skill does not auto-create canonical `Skill`
- duplicate raw inputs do not duplicate canonical skills in returned result

### SkillSeedService and `seed_skills`

Must pass:

- command exists
- command creates canonical skills
- command creates aliases
- command is idempotent
- second run does not duplicate rows
- required aliases exist after seed

### UnmatchedSkillReviewService

Must pass:

- staff can map candidate to existing skill
- staff can ignore candidate
- non-staff cannot map/ignore
- mapping records reviewer and timestamp
- ignoring records reviewer and timestamp
- mapping can create safe alias from candidate when not already present

---

## 4. Admin Acceptance

Must pass:

- `Skill` admin registered.
- `SkillAlias` admin registered.
- `UnmatchedSkillCandidate` admin registered.
- list display is useful.
- search fields exist.
- filters exist.
- admin review path exists for pending candidates.
- admin actions call services where business state changes occur.
- no secrets are exposed.

---

## 5. Migration Acceptance

Must pass:

```bash
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py migrate --settings=config.settings.local
```

Rules:

- migrations are reasonable and app-scoped.
- no migration reset of earlier committed phases.
- no destructive changes to Phase 0–2 models unless explicitly required and justified.
- do not casually reset migrations.

---

## 6. Test Acceptance

Must pass:

```bash
python manage.py test --settings=config.settings.local
```

Required test categories:

- skill model tests
- alias model tests
- unmatched candidate model tests
- normalizer service tests
- seed command/service tests
- review service tests
- admin tests where practical

---

## 7. Runtime Checks

Must pass:

```bash
python manage.py check --settings=config.settings.local
python manage.py seed_skills --settings=config.settings.local
python manage.py seed_skills --settings=config.settings.local
```

Second seed run must not create duplicate skills or aliases.

---

## 8. Junk / Safety Checks

Run:

```bash
find . -type d -name "__pycache__" -print
find . -name "*.pyc" -print
find . -maxdepth 3 -name "task.md" -print
find . -maxdepth 3 -name "*.sqlite3" -print
find . -maxdepth 3 -name "celerybeat-schedule*" -print
git status --short
git diff --stat
```

Must not leave:

- `.env`
- `__pycache__`
- `*.pyc`
- `task.md`
- local SQLite DB
- Celery Beat schedule files
- temporary logs
- generated junk

---

## 9. Final Stop/Go Gate

Phase 3 can be sent for review only when:

- all required checks pass
- `agent_report.md` exists
- no Phase 4 code exists
- no secrets/junk files are present
- the implementation stays inside Django + ORM + services + admin

Do not commit until after senior review.
