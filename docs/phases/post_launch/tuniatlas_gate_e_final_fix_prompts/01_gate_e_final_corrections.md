# Gate E — Final Corrections

Use **Codex GPT-5.5 medium in Warp**.

## Start and boundaries

```bash
cd ~/Projects/tunitech-abroad
source .venv/bin/activate

git status --short --branch
git log --oneline --decorate -8
git diff --check
```

Expected:
- branch `dev`
- ahead of `origin/dev` by four committed gates
- Gate E changes remain uncommitted
- no `.env` changes

Do not commit.
Do not push.
Do not deploy.
Do not access production.
Do not call France Travail or OpenRouter.
Do not reparse CVs in this correction unless explicitly required by a failing Gate C test.

## Current blockers

### 1. Recommendation/match consistency is not actually checked

The report currently marks this as `pass` when refresh counters are greater than zero.

That is not evidence of score consistency.

Replace it with a measured check:

- For every affected user/job pair having both a refreshed active `JobRecommendation` and a current/latest `MatchResult`, compare their actual current `fit_score`.
- `pass`: at least one comparable pair exists and every comparable pair matches.
- `fail`: any comparable pair differs.
- `not_run`: `--include-matches` was not used or no comparable pair exists.
- Include comparable-pair count and mismatch count in the report.
- Never infer consistency from refresh counters.

Add tests for:
- matching recommendation/current-match scores produce `pass`
- mismatched scores produce `fail`
- no comparable pair produces `not_run`
- same-user unrelated job remains unchanged

### 2. Database-family regression is not proving distinct skills

The current check only proves PostgreSQL, MySQL, and SQLite are materializable.

Resolve through actual aliases and prove:
- each maps to the expected canonical skill
- canonical IDs/names are distinct
- SQL Server does not also become generic SQL

Add tests using actual `Skill`/`SkillAlias` rows.

### 3. Chef regression is too weak

Do not classify only the phrase `chef cookbooks`.

Use the real ambiguity/context API and/or a materialization test:

- `chef de projet informatique` must not materialize Chef
- `Chef cookbook`, `Chef Infra`, or equivalent DevOps context must materialize canonical Chef
- verify actual canonical result, not only a policy enum

### 4. CV noise regression uses the wrong query

The current query checks all confirmed profile skills and only six generic names.

Fix it so the report checks CV-originated rows only, using the actual source value used by `CVParsingService`.

Cover the Gate A noisy CV examples, including:

```text
language extraction
location extraction
recommended learning topics
stock alerts
stock movements
suppliers
validation
server
freelance web developer
web development
authentication flows
implemented input validation
bug reports
```

Rules:
- manually confirmed skills must not make this check fail
- a confirmed CV-origin noisy row must make it fail
- do not include raw CV text in the report

### 5. Quality Gate Explanation is hard-coded prose

Replace `_quality_gate_explanation()` with calculated metrics and statuses.

At minimum report:

```text
broad_materialized_rows
broad_required_rows
broad_optional_rows
broad_detected_rows
soft_or_process_materialized_rows
unexpected_noisy_added_rows
broad_signal_scoring_check: pass|fail|not_run
```

Do not claim broad signals are non-scoring unless tests and actual scoring calculations prove it.

### 6. Prove broad signals do not alter fit score

Gate E added many broad detected signals, especially `Software Development`.

Add regression tests around `MatchScoringService`:

- Adding/removing a broad detected `Software Development` row must not improve technical score.
- It must not create a missing-required-skill penalty.
- `API` and `Monitoring` broad rows must not change deterministic fit score.
- A specific supported technical skill such as REST API, PostgreSQL, or Django must still affect scoring as intended.
- Required/optional exact technical skill behavior must remain unchanged.

If current scoring includes broad detected signals, make the smallest service-layer correction necessary. Do not redesign scoring.

Use the shared Gate B policy to decide whether a job skill is hard technical, broad, soft/process, metadata, or rejected noise.

### 7. Report actual noisy additions

Calculate unexpected additions from actual before/after rows.

The report must not print:

```text
unexpected noisy canonical additions: none
```

unless the calculated count is zero.

List only canonical skill name, policy class, requirement type, and count. No private or raw CV data.

### 8. Include test evidence in the next review package

The previous zip contained no actual test output files.

Capture:

```text
meta/django_check.txt
meta/gate_e_tests.txt
meta/domain_tests.txt
meta/full_safety_tests.txt
meta/gate_e_execution_summary.txt
```

A command failure must stop the workflow and remain visible in its log.

## Restore the clean local baseline before rerunning Gate E

Gate E already mutated the local database.

Expected earliest pre-Gate-E backup:

```text
/tmp/tuniatlas_gate_e_backup_20260710_171545.dump
```

Before restoring:

1. Confirm exact local settings:
   - `DJANGO_SETTINGS_MODULE=config.settings.local`
   - `DEBUG=True`
   - PostgreSQL host is empty, localhost, 127.0.0.1, or ::1
2. Confirm the target backup exists and is non-empty.
3. Create and verify a new timestamped safety backup of the current post-apply local database.
4. Restore only the local database.
5. Do not print the password or full connection URI.
6. If any guard fails, stop.

Use `pg_restore --clean --if-exists --no-owner` or the repository/local Docker equivalent that matches the actual local setup.

Do not delete either backup.

## Rerun sequence after fixes and baseline restore

1. Focused tests.
2. One targeted dry-run.
3. One targeted apply.
4. Second targeted apply proving idempotency.
5. Full local dry-run.
6. Inspect the calculated quality gate.
7. Full local apply with `--include-matches` only if the full dry-run has no failed quality checks.
8. Do not use `--include-cvs`.

Generate fresh reports under:

```text
docs/phases/post_launch/gate_e_rematerialize_compare/
```

Replace stale Gate E reports rather than keeping conflicting report versions.

## Required tests

```bash
python manage.py check --settings=config.settings.local

python manage.py test   apps.jobs.tests.test_gate_e_rematerialization   --settings=config.settings.local

python manage.py test   apps.jobs apps.skills apps.cvs apps.matching apps.recommendations   --settings=config.settings.local

python manage.py test   apps.accounts apps.core apps.cvs apps.jobs apps.matching apps.recommendations   --settings=config.settings.local
```

## Final report

Report:
- exact files changed
- scoring behavior before/fix
- calculated regression checks
- pristine backup restored
- safety backup created
- targeted dry-run/apply/idempotency
- full dry-run/apply outcome
- before/after quality metrics
- exact test results
- confirm no production access
- confirm no external API/LLM calls
- confirm no CV reparse
- confirm no commit/push
