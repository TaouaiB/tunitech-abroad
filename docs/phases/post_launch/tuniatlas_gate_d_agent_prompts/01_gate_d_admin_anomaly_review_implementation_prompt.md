# Gate D — Admin Anomaly Review Implementation Prompt

You are working in the TuniAtlas Django repository.

## Agent choice

Recommended agent: **Codex GPT-5.5 medium in Warp**.

Reason: this gate touches Django admin/services/tests and must stay narrow, deterministic, and production-safe.

## Current state

Expected local branch:
- `dev`
- local `dev` is ahead of `origin/dev` by 3 commits:
  - Gate A.2 production trust stabilization
  - Gate B skill extraction policy
  - Gate C CV parser signals
- These commits are local only. Do not push.

Start with:

```bash
cd ~/Projects/tunitech-abroad
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
- Gate A.2, Gate B, and Gate C commits are not present

Do **not** commit.
Do **not** push.

## Product context

TuniAtlas is a job intelligence platform for Tunisian IT candidates targeting international tech opportunities.

Stack constraints:
- Django, Django ORM, PostgreSQL, Redis, Celery, Django templates, HTMX/Tailwind.
- No React, Next.js, FastAPI, MongoDB, SQLAlchemy, SPA.
- Views stay thin.
- Business logic belongs in services.
- Celery tasks call services only.
- No LLM call from Django views.
- Public URLs use UUID public_id.
- CV files are private.
- CVUpload.objects must exclude soft-deleted CVs.
- CVUpload.all_objects is only for admin/privacy/deletion/internal tasks.
- Matching remains deterministic.
- LLM may extract/explain/suggest but must never decide final fit score.

## Gate D scope

Implement **Admin Anomaly Review** only.

Goal:
Give admin/internal reviewers visibility into bad intelligence signals before Gate E rematerialization:
- zero-skill jobs
- generic-only jobs
- ambiguous extracted skills
- unmatched skill candidates
- low-confidence job skills
- bad-description jobs
- hidden job reasons
- CV parser warnings / noisy parse summaries

Use existing models/admin/services where possible. Do **not** add migrations unless absolutely necessary.

Use the Gate A baseline report as source:
`docs/phases/post_launch/gate_a_baseline_current_damage/gate_a_baseline_report_2026_07_10.md`

Gate B and Gate C already hardened extraction/parsing. Gate D should expose review visibility; it must not rework extraction/parsing again.

## Required implementation

### 1. Admin visibility for job skill anomalies

Add/strengthen admin list filters, search fields, readonly fields, and admin actions where useful for existing models such as:
- `NormalizedJob`
- `NormalizedJobSkill`
- `UnmatchedSkillCandidate`
- existing feedback models such as `SkillExtractionFeedback`, `JobQualityFeedback`, or equivalent if present

Must expose at least:
- skill extraction status
- skill signal quality
- zero-skill jobs
- generic-only jobs
- low-confidence job skills
- jobs with rejected/noisy source phrases if existing fields allow
- hidden/excluded jobs and reason fields if existing fields allow
- source and source_job_id
- public_id

Keep admin read-safe and lightweight.

### 2. Service/query layer for anomaly discovery

Add a small service if needed, e.g.:
- `apps/jobs/services/anomaly_review.py`
- or extend existing quality/admin monitoring services

The service should return querysets/counts for:
- active zero-skill jobs
- active generic-only jobs
- low-confidence materialized job skills
- unmatched candidates by status/source/count
- jobs with failed/partial skill extraction
- jobs hidden/excluded by reason
- recent CV parses with warnings if existing CVUpload fields support it

Do not run expensive full recomputation in admin list views.

### 3. Management command or admin report is allowed

Allowed:
- a read-only management command to print anomaly counts/samples.
- admin list filters/actions that mark existing feedback/status if model already supports it.

Not allowed:
- rematerializing all jobs
- reprocessing all CVs
- deleting data
- creating canonical skills automatically
- external API calls
- production deployment

### 4. Admin actions safety

If adding admin actions:
- action names must be explicit and safe.
- no destructive bulk delete.
- no rematerialization.
- actions may mark feedback as reviewed/ignored only if existing model supports it.
- actions must log/count what they changed.
- no real CV file exposure.

### 5. Tests required

Add or update tests for:

- anomaly service returns zero-skill jobs.
- anomaly service returns generic-only jobs.
- anomaly service returns low-confidence job skill rows.
- unmatched candidate admin/service ordering/counts are deterministic.
- hidden/excluded jobs and reasons are visible if model fields exist.
- admin list pages load for superuser for relevant models.
- non-superuser cannot access admin-only CV/private anomaly detail if any custom view is added.
- no private CV file URL exposure.
- no internal integer IDs in public links.

### 6. Commands to run

Run:

```bash
python manage.py check --settings=config.settings.local
python manage.py test apps.jobs apps.skills apps.cvs --settings=config.settings.local
python manage.py test apps.accounts apps.core apps.cvs apps.jobs apps.matching apps.recommendations --settings=config.settings.local
```

Run `npm run css:build` only if you touched CSS. You should not need CSS.

## Expected final report

Report:
- files changed
- admin visibility added
- services/commands added
- tests added
- tests run and result
- any deferred items for Gate E rematerialization
- confirm no migrations unless explicitly justified
- confirm no rematerialization
- confirm no deployment
- confirm no commit/push
