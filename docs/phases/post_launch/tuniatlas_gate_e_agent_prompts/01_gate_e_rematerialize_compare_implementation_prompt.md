# Gate E — Rematerialize and Compare Implementation Prompt

You are working in the TuniAtlas Django repository.

## Agent choice

Recommended agent: **Codex GPT-5.5 medium in Warp**.

Reason: this gate requires safe Django service orchestration, local database mutation controls, deterministic comparison reports, and broad regression testing.

## Current state

Expected local branch:
- `dev`
- local `dev` is ahead of `origin/dev` by 4 commits:
  - Gate A.2 production trust stabilization
  - Gate B skill extraction policy
  - Gate C CV parser signals
  - Gate D admin anomaly review
- These commits are local only. Do not push.

The latest full safety suite passed:
- `528 tests`
- final result `OK`

Start with:

```bash
cd ~/Projects/tunitech-abroad
source .venv/bin/activate

git status --short --branch
git log --oneline --decorate -8
git diff --stat
git diff --check
```

Stop if:
- branch is not `dev`
- unexpected uncommitted changes exist
- `.env` is modified
- migrations are created unexpectedly
- the four local gate commits are not present

Do **not** commit.
Do **not** push.
Do **not** deploy.

## Product context

TuniAtlas is a job intelligence platform for Tunisian IT candidates targeting international tech opportunities.

Architecture constraints:
- Django, Django ORM, PostgreSQL, Redis, Celery, Django templates, HTMX/Tailwind.
- No React, Next.js, FastAPI, MongoDB, SQLAlchemy, SPA.
- Views stay thin.
- Business logic belongs in services.
- Celery tasks call services only.
- No LLM calls from Django views.
- No France Travail live API calls during normal user search.
- User search reads local PostgreSQL only.
- Public URLs use UUID public_id.
- CV files remain private.
- CVUpload.objects excludes soft-deleted CVs.
- CVUpload.all_objects is only for admin/privacy/deletion/internal tasks.
- Matching stays deterministic.
- LLM may extract/explain/suggest but never decides final fit score.

## Gate E objective

Apply Gate B and Gate C logic to existing **local** data, then compare before/after quality.

Required outcomes:
- rebuild existing job skill materialization from stored local job data
- rebuild job search vectors/index data using existing local services
- re-evaluate active job quality/matchability
- invalidate/recompute stale matches and recommendations safely
- optionally reparse active CVs locally through Gate C-safe services if private files exist
- produce a deterministic before/after report
- preserve rollback ability
- no production changes

Use the Gate A baseline:
`docs/phases/post_launch/gate_a_baseline_current_damage/gate_a_baseline_report_2026_07_10.md`

## Safety rules

### 1. Backup before mutation

Before any apply run:
- inspect local database configuration without printing passwords/secrets
- create a timestamped local PostgreSQL backup
- verify the backup file exists and is non-empty
- write the backup path into the Gate E report
- never include the backup in Git or the review zip
- never print real secrets

If a safe backup cannot be created, stop before mutation and report the exact blocker.

### 2. Dry-run first

Any new Gate E command must default to dry-run/read-only behavior.

Mutation must require explicit `--apply`.

Recommended shape:

```bash
python manage.py run_gate_e_rematerialization --report-path ...          # dry run
python manage.py run_gate_e_rematerialization --apply --report-path ... # apply
```

Do not make mutation the default.

### 3. Local-only guard

The apply command must refuse to run when:
- production settings are active
- `DEBUG=False`, unless an explicit safe local override already exists and is clearly documented
- database host/name matches known production configuration if detectable safely

Do not weaken production safety settings.

## Required implementation

### A. Gate E orchestration service

Add a service such as:
- `apps/jobs/services/gate_e_rematerialization.py`
- or an equivalent existing service extension

The service must orchestrate existing services rather than duplicating business logic.

It should support deterministic steps:

1. capture before metrics
2. rematerialize stored job skills using Gate B policy
3. reclassify job skill signal quality / matchability using existing services
4. rebuild search vectors/index fields using existing services
5. mark stale or recompute matches/recommendations through existing services
6. optionally reparse active CVs through Gate C parsing service when explicitly requested
7. capture after metrics
8. generate report

Use deterministic ordering by stable IDs/public IDs.

### B. Management command

Add a command such as:

```text
run_gate_e_rematerialization
```

Required options:
- default dry-run
- `--apply`
- `--report-path`
- `--limit`
- `--job-public-id` for targeted testing
- `--include-cvs` explicit opt-in
- `--include-matches` or equivalent explicit control if needed
- `--skip-search-vectors` if existing architecture makes this useful
- useful progress summary
- non-zero exit on failed safety/backup/apply step

Do not use internal integer IDs in user-facing URLs. CLI-only internal IDs are discouraged; prefer public IDs.

### C. Metrics and comparison report

Generate a Markdown report under:

```text
docs/phases/post_launch/gate_e_rematerialize_compare/
```

The generated report must include:

#### Environment and safety
- timestamp
- Git commit
- settings module
- database engine/host/name in redacted-safe form
- backup path
- dry-run/apply mode
- processed counts
- failures

#### Before and after counts
- active jobs
- total materialized job skills
- zero-skill active jobs
- generic-only active jobs
- weak/missing/partial/strong signal counts
- low-confidence materialized skills
- unmatched candidate totals and statuses
- stale/active recommendations
- match result counts
- active CVs
- CV parse warning counts if CV reparse included

#### Top changes
- top removed noisy skills
- top added/retained hard technical skills
- top unmatched phrases before/after
- jobs changing from generic-only/zero-skill to useful signals
- jobs becoming hidden/weak because only broad/noisy terms remained
- failures/skipped rows

#### Regression cases
Explicitly evaluate:
- `chef de projet` does not become Chef
- DevOps Chef remains valid
- SQL Server does not duplicate SQL
- PostgreSQL/MySQL/SQLite remain distinct
- source metadata phrases do not become skills
- Teamwork/Communication/Agile/Scrum do not drive technical matching
- API/Monitoring broad terms do not become required hard skills
- REST API/OpenAPI/GraphQL remain specific where supported
- noisy CV phrases do not become confirmed ProfileSkill rows
- recommendation score and opened match detail remain consistent after refresh

### D. Job rematerialization behavior

Use stored local data only:
- existing raw payload
- normalized title/description
- existing enrichment payload where already stored
- existing canonical Skill/SkillAlias rows

Do not:
- call France Travail
- call OpenRouter/LLM
- auto-create canonical skills
- delete source job records
- modify unrelated user/account data

Rematerialization must be idempotent.

### E. Search vectors

Inspect current search-vector architecture first.

Rebuild through existing service/command only.

Do not:
- write raw SQL if an existing service exists
- introduce a new search backend
- add vector embeddings unless already part of the current architecture
- call external embedding APIs

### F. Matches and recommendations

After job skill changes:
- old affected matches/recommendations must not remain falsely current
- use existing staleness/recompute services
- keep ordering deterministic
- do not globally recompute unrelated users if avoidable
- record counts of invalidated/recomputed rows

### G. Optional CV reparse

Only with explicit `--include-cvs`.

Rules:
- active non-deleted CVs only through `CVUpload.objects`
- private file paths only
- use existing parsing service
- preserve confirmed user data
- no raw CV text in generated report
- no private file path exposed in report beyond safe internal count/status
- failures should be isolated per CV and reported without sensitive content

### H. Tests required

Add tests for:
- command defaults to dry-run
- apply requires explicit flag
- production/local safety guard
- deterministic job ordering
- targeted `--job-public-id`
- idempotent second apply
- no external API/LLM calls
- no canonical Skill auto-creation
- before/after metrics correctness
- search vector rebuild calls existing service
- affected recommendations/matches become stale or refreshed correctly
- optional CV reparse uses only active non-deleted CVs
- report does not contain raw CV text or secrets
- backup failure prevents mutation
- partial row failure is reported without aborting unrelated rows unless transaction policy requires rollback

### I. Run sequence

First run targeted dry-run:

```bash
python manage.py run_gate_e_rematerialization   --job-public-id <SAFE_LOCAL_JOB_PUBLIC_ID>   --report-path /tmp/tuniatlas_gate_e_target_dry_run.md
```

Then targeted apply after backup:

```bash
python manage.py run_gate_e_rematerialization   --apply   --job-public-id <SAFE_LOCAL_JOB_PUBLIC_ID>   --report-path /tmp/tuniatlas_gate_e_target_apply.md
```

Then verify idempotency by applying the same target again.

Only after targeted checks pass, run full local dry-run and full local apply.

Do not run `--include-cvs` until job-only apply is verified.

If CV reparse is safe and tests pass, run it as a separate explicit local step.

## Required test commands

Run:

```bash
python manage.py check --settings=config.settings.local
python manage.py test apps.jobs apps.skills apps.cvs apps.matching apps.recommendations --settings=config.settings.local
python manage.py test apps.accounts apps.core apps.cvs apps.jobs apps.matching apps.recommendations --settings=config.settings.local
```

Run `npm run css:build` only if CSS changed. CSS should not be needed.

## Expected final report

Report:
- files changed
- backup path and verification result
- dry-run results
- targeted apply and idempotency results
- full local apply results
- before/after metrics
- report path committed or staged
- tests run and final results
- failures/deferred cases
- confirm no production access
- confirm no live France Travail/OpenRouter calls
- confirm no migrations unless explicitly justified
- confirm no commit/push
