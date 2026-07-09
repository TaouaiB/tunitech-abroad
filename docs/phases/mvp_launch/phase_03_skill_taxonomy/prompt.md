# Phase 3 — Skill Taxonomy Foundation — Antigravity/Gemini Prompt

Read this file carefully and execute Phase 3 only.

---

## Mandatory Reading Order

Read these first:

1. `AGENTS.md`
2. `docs/phases/phase_03_skill_taxonomy/tasks.md`
3. `docs/phases/phase_03_skill_taxonomy/acceptance.md`
4. `docs/phases/phase_03_skill_taxonomy/agent_report_template.md`
5. Relevant planning docs in `docs/planning/`, especially:
   - Database Schema v1
   - Service Contracts v1
   - Implementation Roadmap v1
   - MVP Backlog v1
   - Working Agreement v1

Then implement Phase 3 only.

---

## Current Phase

```text
Phase 3 — Skill Taxonomy Foundation
```

Goal:

```text
Build canonical skill taxonomy and alias normalization.
```

Implement these tickets:

```text
TTA-0301 — Create Skill model
TTA-0302 — Create SkillAlias model
TTA-0303 — Create UnmatchedSkillCandidate model
TTA-0304 — Implement SkillNormalizerService
TTA-0305 — Implement initial skill seed command
TTA-0306 — Add admin skill review actions/support
```

You may work automatically through all tickets inside this phase. Do not ask for approval between tickets.

---

## Hard Boundary

Do not start Phase 4.

Do not create or implement:

- jobs app
- job ingestion
- France Travail client
- RawJobRecord
- NormalizedJob
- NormalizedJobSkill
- job search
- public job pages
- CVUpload
- CVParsedData
- CV parsing
- PDF extraction
- matching
- quick match
- recommendations
- saved jobs
- OpenRouter/LLM
- email digest
- unsubscribe tokens
- privacy deletion
- new Celery tasks

Do not refactor `profiles.ProfileSkill` into a canonical FK in Phase 3 unless a minimal import-safe change is absolutely necessary. Existing Phase 2 `ProfileSkill` is a shell using raw/normalized names. Integration of profile skills with canonical skills belongs to later CV/profile/matching phases.

Do not change the approved stack.
Do not use React, Next.js, Angular, FastAPI, MongoDB, SQLAlchemy, or SPA architecture.

---

## Implementation Requirements

### 1. Create skills app

Create:

```text
apps/skills/
apps/skills/apps.py
apps/skills/models.py
apps/skills/admin.py
apps/skills/services/
apps/skills/management/commands/
apps/skills/tests/
```

Add the app to `INSTALLED_APPS` using its AppConfig.

Expected config name example:

```python
"apps.skills.apps.SkillsConfig"
```

---

### 2. Models

Implement:

```text
Skill
SkillAlias
UnmatchedSkillCandidate
```

Follow the fields, constraints, indexes, choices, and delete behavior defined in `tasks.md`.

Important rules:

- `Skill.canonical_name` unique.
- `Skill.slug` unique.
- `SkillAlias.normalized_alias` unique.
- `UnmatchedSkillCandidate` unique on `normalized_text` + `source_type`.
- Use `settings.AUTH_USER_MODEL` for `reviewed_by`.
- Do not create public URLs for these models.
- Do not expose internal IDs in any public route.

---

### 3. Normalization utility

Create a reusable text normalization function, either inside `normalizer.py` or a small utility module.

It must:

- handle `None` and empty strings safely
- lowercase
- remove/normalize accents
- strip punctuation where safe
- normalize `.` and `#` carefully enough for skills like `C#`, `.NET`, `Node.js`
- collapse whitespace
- produce stable values for alias lookup

Do not over-engineer fuzzy matching in Phase 3. Exact alias lookup is enough.

---

### 4. SkillNormalizerService

Implement:

```python
SkillNormalizerService.normalize_many(
    raw_skills: list[str],
    source_type: str,
    source_id: int | None = None,
) -> SkillExtractionResult
```

Required behavior:

- Match `SkillAlias.normalized_alias` exactly.
- Return canonical `Skill` objects.
- Create/update `UnmatchedSkillCandidate` for unknowns.
- Increment `occurrence_count` for repeated unknowns.
- Do not auto-create `Skill` for unknowns.
- Deduplicate canonical skills and raw candidates.
- Use transactions where needed.

---

### 5. Seed service and seed command

Create:

```text
apps/skills/services/seed.py
apps/skills/management/commands/seed_skills.py
```

Command:

```bash
python manage.py seed_skills --settings=config.settings.local
```

Seed target:

- 200–300 canonical skills.
- At least 500 aliases if practical.
- Must include core web/software/IT market skills relevant to Tunisian candidates targeting France.
- Must be idempotent.

Must include aliases required by tests:

```text
ReactJS -> React
Postgres -> PostgreSQL
Python3 -> Python
JS -> JavaScript
TS -> TypeScript
Node -> Node.js
Tailwind -> Tailwind CSS
Docker Compose -> Docker Compose
```

Do not fetch seed data from the web.
Do not call external APIs.

---

### 6. Review service and admin support

Create:

```text
apps/skills/services/review.py
```

Implement:

```python
UnmatchedSkillReviewService.map_candidate(candidate_id, skill_id, reviewed_by)
UnmatchedSkillReviewService.ignore_candidate(candidate_id, reviewed_by)
```

Rules:

- Staff only.
- Non-staff gets permission error or domain error.
- Mapping sets `mapped_skill`, `status`, `reviewed_by`, `reviewed_at`.
- Ignoring sets `status`, `reviewed_by`, `reviewed_at`.
- Mapping may create `SkillAlias` from candidate normalized text if no alias exists.
- Do not auto-create canonical `Skill`.

Admin:

- Register all three models.
- Add useful search/filter/list display.
- Add safe actions for ignoring and mapping where feasible.
- Keep business logic in services, not directly inside admin actions except calling the service.

---

### 7. Tests

Add tests for:

- models
- normalizer service
- seed service/command
- review service
- admin actions if practical

Required examples:

- `ReactJS` maps to `React`.
- `Postgres` maps to `PostgreSQL`.
- `Python3` maps to `Python`.
- unknown skill creates `UnmatchedSkillCandidate`.
- repeated unknown skill increments `occurrence_count`.
- unknown skill does not create `Skill`.
- seed is idempotent.
- staff can map/ignore candidate.
- non-staff cannot map/ignore candidate.

---

## Required Commands

Run after each logical block when relevant.

Final required checks:

```bash
source .venv/bin/activate
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py migrate --settings=config.settings.local
python manage.py test --settings=config.settings.local
python manage.py seed_skills --settings=config.settings.local
python manage.py seed_skills --settings=config.settings.local
```

Check seed idempotency by verifying counts do not grow incorrectly on the second run.

Run junk checks:

```bash
find . -type d -name "__pycache__" -print
find . -name "*.pyc" -print
find . -maxdepth 3 -name "task.md" -print
find . -maxdepth 3 -name "*.sqlite3" -print
find . -maxdepth 3 -name "celerybeat-schedule*" -print
git status --short
git diff --stat
```

Remove generated junk from disk if created.

---

## Git Rules

Do not commit.
Do not merge.
Do not push.

Stop after implementation, checks, and final report.

---

## Final Report

Create or update:

```text
docs/phases/phase_03_skill_taxonomy/agent_report.md
```

Use the structure from:

```text
docs/phases/phase_03_skill_taxonomy/agent_report_template.md
```

Your final message must include:

1. completed tickets
2. files created/changed
3. migrations created
4. services implemented
5. seed counts
6. commands run
7. final check results
8. remaining risks/manual steps
9. confirmation that no Phase 4 work was done
