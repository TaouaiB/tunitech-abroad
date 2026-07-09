# Phase 15C Tasks — Admin Job Skill Review + Unknown Badge Cleanup

## Objective

Create an admin workflow for jobs that still have no materialized skills, and hide ugly `Unknown` placeholder badges from public UI.

This phase must stay within:
- admin/data-quality
- skill review
- presentation cleanup

No matching formula change. No LLM calls from views. No France Travail calls from views. No SPA.

---

## Task 1 — Inspect current job/admin/skill structure

Inspect:
- `apps/jobs/models.py`
- `apps/jobs/admin.py`
- `apps/jobs/services/presentation.py`
- `apps/jobs/services/skill_materialization.py`
- `apps/jobs/services/skill_extraction.py`
- `apps/skills/models.py`
- templates for job cards and job detail
- existing admin filters/actions/tests

Find:
- `NormalizedJob`
- `NormalizedJobSkill`
- relationship name for job skills
- fields for `skill_extraction_status`, `skill_signal_quality`
- available source/requirement_type values
- existing public badge presentation functions

---

## Task 2 — Admin list for jobs needing skill review

Add or improve Django admin support so staff can find jobs needing review.

Minimum:
- filter/list view for active jobs with zero `NormalizedJobSkill`
- visible columns:
  - title
  - company
  - location
  - status
  - source
  - skill_signal_quality
  - skill_extraction_status
  - enrichment status if accessible without expensive query explosion
  - job skill count
  - last_seen_at / created_at
- search by title/company/source external ID if available
- admin filter for:
  - no materialized skills
  - active only
  - strong/partial signal
  - extraction status
  - source

Implementation can use `SimpleListFilter` and annotations.
Avoid N+1 queries where reasonable.

---

## Task 3 — Admin inline/editor for `NormalizedJobSkill`

Admin must allow manual canonical skill assignment.

Minimum:
- `NormalizedJobSkill` inline on `NormalizedJob` admin, or a dedicated admin model with strong filtering/search.
- Admin can add:
  - skill
  - requirement_type
  - source=`admin`
  - confidence if model supports it
- Admin can remove wrong job skill rows.
- Admin must not edit raw provider JSON or raw LLM response from this workflow.

If source has choices, ensure `admin` source exists. If it does not, inspect existing choices before adding migrations. Prefer existing admin/manual source value if already present.

---

## Task 4 — Admin actions

Add safe admin actions for selected jobs:

1. Re-run deterministic skill extraction/materialization.
   - Calls service layer only.
   - Does not call OpenRouter directly.
   - Does not call France Travail.
   - Reports success/failed counts.

2. Rebuild/materialize from existing enrichment data if enrichment exists.
   - Calls materialization service only.
   - Does not call provider again.
   - Reports counts.

Optional only if already supported safely:
3. Queue LLM enrichment for selected jobs.
   - Must call task/service only.
   - Must respect existing caps/rate limits.
   - Must clearly label potential cost.
   - Do not implement if it requires broad scope.

---

## Task 5 — Management command/report for job skill review

Add command:

```bash
python manage.py export_jobs_needing_skill_review --active-only --limit 200 --settings=config.settings.local
```

or similar.

Output CSV/JSONL to `var/review/`.

Columns:
- job id
- public_id
- title
- company
- location
- status
- source
- source external id if available
- skill_signal_quality
- skill_extraction_status
- job_skill_count
- enrichment status
- required/optional enrichment counts if available
- description excerpt
- job URL/path if easy

This is for admin/manual review.

---

## Task 6 — Public UI cleanup: hide `Unknown`

Fix public job card/detail badges so placeholder values are not displayed.

Filter these values before badge rendering:
- `unknown`
- `Unknown`
- `UNKNOWN`
- `none`
- `null`
- `n/a`
- empty/whitespace

Do this in a presentation helper/service if one exists.
Do not put scattered template-only conditionals everywhere if there is already a presentation service.

Add tests proving:
- a job with unknown experience/remote/status display does not render `Unknown`
- valid badges still render
- no useful real value is removed

---

## Task 7 — Regression tests

Required tests:
- admin/query helper identifies active jobs with no `NormalizedJobSkill`
- admin action calls service and updates messages/counts or service-level helper is tested
- manual/admin `NormalizedJobSkill` creation is possible and uses canonical `Skill`
- public job card/detail hides `Unknown`
- materialization/report command includes a clearly IT job with zero skills
- no OpenRouter/France Travail calls from views/templates/admin actions directly

---

## Task 8 — Local verification

Run:

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test --settings=config.settings.local --parallel 1
npm run css:build
python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
git diff --check
```

Run safety greps:

```bash
grep -R "OpenRouterClient\|OPENROUTER\|client.chat\|_make_request" apps/*/views.py apps/*/admin.py templates -n 2>/dev/null || true
grep -R "FranceTravailClient\|search_offers\|api.francetravail" apps/*/views.py templates -n 2>/dev/null || true
grep -R "file.url\|cv.file.url\|upload.file.url\|raw_text\|raw_request_json\|raw_response_text\|raw_response_json" templates apps -n 2>/dev/null || true
grep -R "<int:" apps templates config -n 2>/dev/null || true
git diff -- . ':!.env' ':!.env.*' | grep -iE "sk-or-|Bearer [A-Za-z0-9_.-]{20,}|OPENROUTER_API_KEY=.*[^=]|FRANCE_TRAVAIL_CLIENT_SECRET=.*[^=]|EMAIL_HOST_PASSWORD=.*[^=]" || echo "OK: no obvious secrets in diff"
```

---

## Deliverables

Create/update:
- code changes
- tests
- `docs/phases/phase_15c_admin_job_skill_review_unknown_badge_cleanup/agent_report.md`
- Codex later creates `codex_report.md`

Do not commit.
