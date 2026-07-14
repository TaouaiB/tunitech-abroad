# Gate E — Fix Blocking Issues

You are correcting the existing Gate E implementation in the TuniAtlas Django repository.

## Agent

Use **Codex GPT-5.5 medium in Warp**.

## Safety

Start with:

```bash
cd ~/Projects/tunitech-abroad
source .venv/bin/activate
git status --short --branch
git log --oneline --decorate -8
git diff --check
```

Expected:
- branch `dev`
- local branch ahead of `origin/dev` by 4 committed gates
- Gate E files uncommitted
- no `.env` change

Do not commit.
Do not push.
Do not deploy.
Do not access production.
Do not call France Travail or OpenRouter.

## Blocking findings to fix

### 1. Gate E was not actually applied

The submitted evidence contains only:

```text
gate_e_rematerialize_compare_dry_run_2026_07_10.md
backup_path: not_applicable_dry_run
mode: dry-run
```

Missing:
- targeted apply report
- second targeted apply/idempotency report
- full local apply report
- verified non-empty backup path in apply report

Implement/fix safely, then execute the required sequence on the local database only.

### 2. Local apply guard is too weak

Current guard can allow a remote IP/database with an innocent name.

For `--apply`, require:
- exact local settings module (`config.settings.local` or the repo's exact local module)
- `DEBUG=True`
- PostgreSQL
- host must be empty/local socket, `localhost`, `127.0.0.1`, or `::1`

Reject every other host by default.

Add tests for:
- remote numeric IP rejected
- remote hostname rejected
- localhost accepted
- production settings rejected before backup

### 3. Regression report is misleading

`_regression_cases()` currently prints many hard-coded `True` values.

Remove hard-coded PASS results.

Each reported regression case must be calculated from actual before/after job skill rows or explicit deterministic policy checks with real inputs and context.

At minimum compute:
- `chef de projet` rejects Chef
- DevOps/Chef cookbook context accepts Chef
- SQL Server does not add SQL duplicate
- PostgreSQL, MySQL, SQLite remain distinct
- source metadata phrases reject materialization
- Teamwork, Communication, Agile, Scrum are not required technical skills
- API and Monitoring are not required hard skills
- REST API, OpenAPI, GraphQL retain specific behavior where supported
- CV noisy phrases are not confirmed ProfileSkill rows
- recommendation/match score consistency is based on actual refreshed records when `--include-matches` is used; otherwise report `not_run`, never PASS

Use statuses: `pass`, `fail`, `not_run`.

### 4. Report labels broad skills as hard technical

The dry-run report lists `Software Development: 115` under:

```text
top_added_or_retained_hard_technical_skills
```

This is incorrect because Gate B classifies Software Development as broad technical.

Split report output into:
- added hard technical skills
- added broad/non-scoring signals
- removed noisy/soft/process skills
- retained hard technical skills

Use Gate B extraction policy to classify each canonical skill.

### 5. Top unmatched phrases are not phrases

The report currently prints only grouped status totals such as:

```text
job:pending: 2090
```

Add actual deterministic top candidate phrases:
- normalized candidate text
- source type
- status
- occurrence count
- no raw CV text
- no private paths

### 6. Before/after transitions are inconsistent

The report says:
- zero-skill jobs: 5 → 0
- jobs changing to useful signals: none

Track transitions using both:
- materialized skill count before/after
- signal quality before/after

Report:
- zero-skill → nonzero
- nonzero → zero-skill
- generic/weak → useful
- useful → weak/generic
- unchanged

### 7. Refresh scope is too broad

Current code:
- adds every processed job to `affected_job_ids`, even if nothing changed
- refreshes every MatchResult for an affected user, including unrelated jobs

Fix:
- add a job to `affected_job_ids` only if its skill set, requirement types, confidence, quality, classification, or search-vector-relevant data changed
- for targeted runs, refresh only MatchResult rows for affected jobs
- mark/recompute only recommendations affected by changed jobs, while preserving unrelated active recommendations
- add a same-user/unrelated-job regression test

Do not globally recompute unrelated jobs/users.

### 8. Dry-run side-effect safety

Dry-run may use transactional DB writes for job simulation, but must not trigger non-transactional side effects.

Required:
- no task enqueue
- no email
- no external API
- no LLM
- no CV reparse in dry-run

Reject `--include-cvs` unless `--apply` is also present.

For CV apply:
- require existing CV LLM extraction to be disabled
- use active non-deleted `CVUpload.objects` only
- no raw text in reports

### 9. Quality gate before full apply

The current projection shows:
- low-confidence skills: 9 → 212
- total materialized skills: 1677 → 1810
- unmatched pending job candidates: 2084 → 2090
- Software Development added 115 times

Do not silently accept these as improvement.

The corrected report must explain these changes by category and prove:
- broad signals do not become required missing skills
- broad signals do not affect deterministic fit score
- soft/process skills are removed from scoring
- specific technical skills remain
- no unexpected noisy canonical skills are introduced

If the full dry-run reveals a real Gate B defect, stop before full apply and report it. Do not hide it with report wording.

## Required execution sequence

After code/tests pass:

1. Select one safe local active job public UUID.
2. Targeted dry-run.
3. Targeted apply with verified backup.
4. Second targeted apply to prove idempotency.
5. Full local dry-run.
6. Review full dry-run metrics.
7. Full local apply only if no blocking quality regression remains.
8. Run with `--include-matches` as part of the approved full apply or a separate explicit apply.
9. CV reparse remains separate and explicit; do not run it unless all safety checks pass.

Generate and preserve reports under:

```text
docs/phases/post_launch/gate_e_rematerialize_compare/
```

Expected reports:
- targeted dry-run
- targeted apply
- targeted second apply/idempotency
- full dry-run
- full apply
- optional matches refresh
- optional CV reparse only if actually run

Do not include database backup files in Git or review zip.

## Required tests

```bash
python manage.py check --settings=config.settings.local
python manage.py test apps.jobs.tests.test_gate_e_rematerialization --settings=config.settings.local
python manage.py test apps.jobs apps.skills apps.cvs apps.matching apps.recommendations --settings=config.settings.local
python manage.py test apps.accounts apps.core apps.cvs apps.jobs apps.matching apps.recommendations --settings=config.settings.local
```

## Final report

Report:
- exact files changed
- exact commands run
- backup path and non-empty verification
- targeted dry-run/apply/idempotency results
- full dry-run/apply results
- before/after quality interpretation
- whether CV reparse was run or deferred
- no production access
- no external API/LLM calls
- no commit/push
