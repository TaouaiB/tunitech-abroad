# Phase 15E Codex Verification Report

## Verdict

REPAIRED_PASS

## Summary

Codex reviewed the Phase 15E implementation as a strict verifier, repaired issues in scope, and did not commit.

Main repairs:
- Centralized public visibility and matchability queryset logic in `JobEligibilityService`.
- Wired public search, recommendation generation, recommendation dashboard filtering, matching entrypoints, and saved-job display to eligibility.
- Hardened IT/non-IT classification edge cases for protected IT roles and non-IT false positives.
- Repaired zero-materialized-skill handling so zero-skill jobs can never be `public_matchable`.
- Tightened public wording so `Compétences en cours d'analyse` is reserved for pending/processing analysis.
- Added/expanded regression tests for Phase 15E classification, eligibility, badge deduplication, match blocking, and reclassification idempotency.
- Repaired the reclassification command output to include required visibility/matchability/admin-review/zero-skill metrics.

## Files reviewed

- `apps/jobs/services/it_classification.py`
- `apps/jobs/services/skill_signals.py`
- `apps/jobs/services/eligibility.py`
- `apps/jobs/services/search.py`
- `apps/jobs/services/presentation.py`
- `apps/jobs/templatetags/job_presentation.py`
- `apps/jobs/views.py`
- `apps/matching/views.py`
- `apps/recommendations/services/recommendation.py`
- `apps/recommendations/services/query.py`
- `apps/jobs/management/commands/reclassify_jobs.py`
- `templates/jobs/job_detail.html`
- `templates/jobs/partials/job_card.html`
- `templates/recommendations/partials/recommendation_card.html`
- `templates/dashboard/saved_jobs.html`
- Phase 15E tests under `apps/jobs/tests/`

## Repairs applied

- Added central queryset helpers:
  - `JobEligibilityService.filter_publicly_visible()`
  - `JobEligibilityService.filter_matchable()`
  - `JobEligibilityService.active_public_base_queryset()`
- Kept explicit non-IT exclusions strict:
  - `skill_signal_quality == "excluded_non_it"`
  - `classification_json` containing `{"confidence": "excluded"}`
  - `classification_json` containing `{"is_it": false}`
- Preserved compatibility for older high-confidence or unclassified test fixtures without weakening explicit exclusions.
- Changed `generic_only` from matchable to admin-review-only.
- Required at least one materialized `NormalizedJobSkill` row for `public_matchable`.
- Updated `filter_matchable()` to exclude zero-skill jobs with `job_skills__isnull=False`.
- Updated `is_matchable(job)`/`classify_public_state(job)` to return false/admin-review for finished, failed, or not-enough-text zero-skill jobs.
- Kept `public_limited_pending_analysis` only for truly pending/processing jobs.
- Blocked match actions for non-matchable jobs.
- Filtered recommendation candidates to matchable jobs.
- Filtered displayed recommendations to publicly visible jobs.
- Updated saved jobs to still display saved rows that later become non-public, without linking normal users to a 404 detail.
- Added public visibility/matchability template helpers.
- Deduplicated badges through the central presentation service.
- Updated old job-card tests to match the Phase 15E wording rule.

## Classification verdict

PASS after repair.

Protected IT examples now classify as IT and reclassify away from `excluded_non_it`:
- Data Engineer GCP
- Data Engineer / Expert Data Intégration
- Tech Lead / DevOps
- Développeur .NET / C# Fullstack
- Développeur fullstack Java/Angular
- Consultant Cybersécurité Sénior with audit/security delivery
- Ingénieur en Optimisation R&D with algorithm/software evidence

Non-IT false positives now classify as excluded:
- Chargé d'affaires / commercial agencement bois
- SDR/BDR Business Developer Cybersécurité
- Animateur / développeur réseau de franchise
- Médiateur scientifique cybersécurité
- Generic transformation digitale/business consulting without hands-on technical role
- Développeur-vendeur / photography retail wording
- Médiateur/Médiatrice scientifique - spécialité cybersécurité with grand-public/outreach wording
- Animateur/trice réseau / développeur/euse réseau de franchise with franchisés/points-de-vente wording

## Eligibility/Public Surface Verdict

PASS after repair.

Public list uses `JobEligibilityService.filter_publicly_visible()`.
Public detail 404s excluded/admin-review-only jobs for normal users.
Recommendations use eligibility for both generation and dashboard display.
Saved jobs can still show a previously saved job that later becomes non-public, but without a public detail link.

## Matchability Verdict

PASS after repair.

Only `public_matchable` jobs are matchable.
`public_matchable` requires at least one materialized `NormalizedJobSkill` row.
`public_limited_pending_analysis`, `admin_review_only`, and `excluded` jobs are blocked from quick/detailed match entrypoints.
No scoring formula changes were made.

## Badge/Wording Verdict

PASS after repair.

Badge deduplication is centralized after placeholder filtering.
`Compétences en cours d'analyse` appears only for pending/processing analysis states.
Completed zero-skill jobs display `Compétences techniques non spécifiées`.
Detailed analysis CTAs are hidden/disabled for non-matchable jobs.

## Command/Idempotency Verdict

PASS after repair.

Required data commands ran:

```text
python manage.py reclassify_jobs --active-only --dry-run --limit 500 --settings=config.settings.local
Processed 178 jobs
Excluded: 3 -> 5
Visible: 173 -> 173
Matchable after: 173
Admin review only after: 0
Zero-skill public visible after: 0
```

```text
python manage.py reclassify_jobs --active-only --apply --limit 500 --settings=config.settings.local
Processed 178 jobs
Excluded: 3 -> 5
Visible: 173 -> 173
Matchable after: 173
Admin review only after: 0
Zero-skill public visible after: 0
```

```text
python manage.py reclassify_jobs --active-only --apply --limit 500 --settings=config.settings.local
Processed 178 jobs
Excluded: 5 -> 5
Visible: 173 -> 173
Matchable after: 173
Admin review only after: 0
Zero-skill public visible after: 0
```

Examples corrected from excluded to IT:
- Tech Lead / DevOps
- Consultant Cybersécurité Sénior
- Ingénieur en Optimisation R&D
- Développeur .NET / C# Fullstack
- Data Engineer GCP
- Data Engineer / Expert Data Intégration
- Développeur fullstack Java/Angular confirmé

Example hidden:
- SDR/BDR - Business Developer - Cybersécurité
- Médiateur/Médiatrice scientifique - spécialité cybersécurité
- Animateur/trice réseau / développeur/euse réseau de franchise

## Architecture/Safety Verdict

PASS.

- No OpenRouter calls were added to views/admin/templates.
- No France Travail live calls were added to public views/templates.
- Public search remains local PostgreSQL.
- No DB migration was added.
- No deleted rows/jobs were removed.
- No secrets were added to the diff.

Safety grep notes:
- OpenRouter/France Travail greps over views/templates returned no matches.
- The broad sensitive-field grep returned existing model/service/test/admin references for `raw_text`, `raw_request_json`, and related fields; no template exposure or Phase 15E public-surface leak was found.
- Secret diff grep returned `OK: no obvious secrets in diff`.

## Tests/Checks

Passed:

```text
python manage.py check --settings=config.settings.local
System check identified no issues (0 silenced).
```

```text
python manage.py makemigrations --check --dry-run --settings=config.settings.local
No changes detected
```

```text
python manage.py test --settings=config.settings.local --parallel 1
Ran 523 tests in 119.009s
OK
```

```text
npm run css:build
Done in 839ms.
```

```text
python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
2 static files copied to '/home/bahaedinetaouai/Projects/tunitech-abroad/staticfiles', 134 unmodified.
```

```text
git diff --check
```

No output, indicating whitespace check passed.

Note: `npm run css:build` printed the existing Browserslist/caniuse-lite freshness warning.

## Metrics

From local active job reclassification limited to 500:
- Active processed: 178
- Active `excluded_non_it`: 3 before, 5 after
- Public visible: 173 before, 173 after
- Public matchable after: 173
- Admin review only after: 0
- Zero-materialized-skill public visible after: 0

Final zero-skill diagnostic:

```text
PUBLIC_VISIBLE_ZERO_SKILL=0
PUBLIC_VISIBLE_ZERO_SKILL_TRUE_PENDING_OR_PROCESSING=0
MATCHABLE_ZERO_SKILL=0
FILTER_MATCHABLE_ZERO_SKILL=0
```

## Remaining Risks

- The local data command changed the local database as required by the phase (`--apply` ran twice). No migration or code commit was made.
- `MATCHABLE_ZERO_SKILL = 0`; no known zero-skill matchable jobs remain after repair.
- The broad grep command is intentionally noisy because it scans tests/models/services; the relevant public-surface safety condition passed.

## Commit Recommendation

Ready for human review. Do not commit until Baha reviews the repaired Phase 15E diff and generated report.
