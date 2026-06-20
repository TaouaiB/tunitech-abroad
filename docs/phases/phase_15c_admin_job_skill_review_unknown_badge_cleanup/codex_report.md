# Phase 15C Codex Verification Report

## Verdict

REPAIRED_PASS

## Summary

Codex verified the Gemini implementation for Phase 15C and repaired in-scope issues in the admin review workflow, enrichment rematerialization action, export command, badge placeholder filtering, and tests. No commits were made.

## Files reviewed

- `apps/jobs/admin.py`
- `apps/jobs/models.py`
- `apps/jobs/services/admin_operations.py`
- `apps/jobs/services/presentation.py`
- `apps/jobs/services/skill_materialization.py`
- `apps/jobs/management/commands/export_jobs_needing_skill_review.py`
- `apps/jobs/tests/test_15c_admin_skill_review.py`
- `apps/jobs/tests/test_views.py`
- `apps/jobs/templatetags/job_presentation.py`
- `templates/jobs/partials/job_card.html`
- `templates/jobs/job_detail.html`
- `templates/dashboard/saved_jobs.html`
- `templates/recommendations/partials/recommendation_card.html`
- `docs/phases/phase_15c_admin_job_skill_review_unknown_badge_cleanup/agent_report.md`

## Repairs applied

- Expanded `NormalizedJobAdmin` with review-oriented columns: location, source, signal quality, extraction status, enrichment status, materialized skill count, `last_seen_at`, and `created_at`.
- Added explicit admin filters for zero materialized skills, active review jobs, and strong/partial signal quality.
- Fixed `rematerialize_from_enrichment` to use existing successful `JobEnrichment` rows only. The previous implementation referenced a non-existent `is_valid` field and fell back to rule materialization under an enrichment action.
- Expanded the export command with enrichment status, enrichment required/optional counts, source external ID, and public job path.
- Centralized badge filtering now also hides the legacy placeholder value `t`, which existing public view tests use as meaningless placeholder metadata.
- Strengthened Phase 15C tests for admin queryset review columns, manual canonical skill creation, enrichment-only rematerialization, and export fields.

## Admin Workflow Verdict

PASS after repair.

- Admin can list and filter active jobs with zero materialized `NormalizedJobSkill` rows.
- Admin can manually add/remove canonical `NormalizedJobSkill` rows through the inline.
- Admin actions call service-layer helpers.
- The enrichment rematerialization action does not call an LLM provider and now uses existing successful enrichment only.

## Export Command Verdict

PASS after repair.

Verified:

```bash
python manage.py export_jobs_needing_skill_review --active-only --limit 5 --format csv --settings=config.settings.local
python manage.py export_jobs_needing_skill_review --active-only --limit 5 --format jsonl --settings=config.settings.local
```

Both commands wrote non-empty outputs under `var/review/` with reviewable fields.

## Unknown Badge Verdict

PASS after repair.

Public job cards/details, saved jobs, and recommendation cards use the shared `is_valid_badge` filter. Placeholder values including `unknown`, `none`, `null`, `n/a`, empty strings, and `t` are hidden while valid values still render.

## Architecture/Safety Verdict

PASS.

- No matching formula changes found.
- No direct OpenRouter calls were introduced in views/admin/templates.
- No France Travail live search calls were introduced in views/templates.
- No bulk unmatched candidate promotion found.
- No migrations were needed.

## Tests/Checks

Passed:

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test apps.jobs.tests.test_15c_admin_skill_review --settings=config.settings.local --parallel 1
python manage.py test apps.jobs.tests.test_views --settings=config.settings.local --parallel 1
python manage.py test apps.jobs.tests.test_15c_admin_skill_review apps.recommendations apps.matching --settings=config.settings.local --parallel 1
python manage.py test --settings=config.settings.local --parallel 1
npm run css:build
python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
git diff --check
git diff --cached --check || true
```

Full test result:

```text
Ran 482 tests in 87.208s
OK
```

Note: one attempted parallel Django test command failed because two test processes tried to create the same test database concurrently. It was rerun serially and passed.

## Safety Greps

Passed:

```bash
grep -R "OpenRouterClient\|OPENROUTER\|client.chat\|_make_request" apps/*/views.py apps/*/admin.py templates -n 2>/dev/null || true
grep -R "FranceTravailClient\|search_offers\|api.francetravail" apps/*/views.py templates -n 2>/dev/null || true
grep -R "<int:" apps templates config -n 2>/dev/null || true
git diff -- . ':!.env' ':!.env.*' | grep -iE "sk-or-|Bearer [A-Za-z0-9_.-]{20,}|OPENROUTER_API_KEY=.*[^=]|FRANCE_TRAVAIL_CLIENT_SECRET=.*[^=]|EMAIL_HOST_PASSWORD=.*[^=]" || echo "OK: no obvious secrets in diff"
```

The raw/file exposure grep returned existing model/service/test/admin references, not template exposure from this phase.

## Remaining Risks

- The admin extraction/rematerialization actions run synchronously. Very large selections could time out in the admin request cycle.
- `var/review/` outputs are generated local review artifacts and remain untracked unless intentionally added.

## Commit Recommendation

Review the diff, then commit Phase 15C changes from `dev` when ready. Do not commit from `main`.
