# Phase 15D Codex Verification Report

## Verdict

REPAIRED_PASS

## Summary

Codex verified the Phase 15D implementation and repaired in-scope issues in curated decision loading, ignore rules, unmatched candidate reconciliation, zero-skill recovery dry-run behavior, false-positive protection, and tests. No commit was made.

The phase folder did not contain `agent_report.md` at verification time.

## Files reviewed

- `apps/skills/services/seed.py`
- `apps/skills/services/normalizer.py`
- `apps/skills/services/ignored.py`
- `apps/skills/services/phase_15d_decisions.py`
- `apps/skills/management/commands/reconcile_unmatched_skill_candidates.py`
- `apps/jobs/services/zero_skill_recovery.py`
- `apps/jobs/management/commands/recover_zero_skill_jobs.py`
- `apps/jobs/services/skill_materialization.py`
- `apps/jobs/services/skill_extraction.py`
- `apps/jobs/services/admin_operations.py`
- `apps/jobs/admin.py`
- `apps/skills/models.py`
- `apps/jobs/models.py`
- `apps/skills/tests/test_seed.py`
- `apps/skills/tests/test_ignore_rules.py`
- `apps/jobs/tests/test_zero_skill_recovery.py`
- Phase 15A/15B/15C Codex reports
- Phase 15D decision/rule files

## Repairs applied

- Added `apps/skills/services/phase_15d_decisions.py` to load approved Phase 15D decisions from the curated CSV once and share them across seed, ignore, and reconcile code.
- Changed seed logic to use only approved `alias_to_existing` and `create_new_skill` decisions.
- Narrowed ignore behavior:
  - exact approved ignore terms are supported;
  - defensive normalization was added;
  - the broad `experience in ...` prefix was replaced with sector/industry-specific matching.
- Changed `reconcile_unmatched_skill_candidates` to operate only on approved Phase 15D decisions, protecting `keep_pending`/unapproved rows from accidental mapping.
- Fixed zero-skill recovery to:
  - skip jobs that already have materialized skills;
  - skip classified/excluded non-IT jobs;
  - support service-level dry-run;
  - return reason counts and examples.
- Updated the recovery command to pass dry-run into the service and print skipped/exemplar counts.
- Strengthened tests for seed idempotency, curated aliases/new skills, already-resolved rows, ignore behavior, reconcile dry-run/apply, recovery dry-run/apply/idempotency, false-positive exclusion, and admin action delegation.

## Taxonomy verdict

PASS after repair.

- Only approved Phase 15D taxonomy decisions are seeded.
- `already_resolved` rows do not create duplicate aliases.
- `alias_to_existing` and `create_new_skill` rows are idempotent.
- Duplicate DB checks passed:

```text
duplicate_canonical_skills []
duplicate_normalized_aliases []
duplicate_job_skills []
```

## Ignore/Reconcile verdict

PASS after repair.

- Ignore rules are narrow and tested.
- Ignored raw candidates become `ignored`, not `pending`.
- Reconcile dry-run rolls back changes.
- Reconcile apply maps only approved curated candidates.
- `keep_pending`/unapproved rows are untouched.
- Re-running apply is idempotent.

Command results:

```text
python manage.py reconcile_unmatched_skill_candidates --dry-run --settings=config.settings.local
Dry run: Changes rolled back.
Total pending candidates evaluated: 15
Resolved (mapped): 15
Resolved (ignored): 0
Remaining pending: 0
```

```text
python manage.py reconcile_unmatched_skill_candidates --apply --settings=config.settings.local
Apply: Changes committed.
Total pending candidates evaluated: 15
Resolved (mapped): 15
Resolved (ignored): 0
Remaining pending: 0
```

Second apply:

```text
Total pending candidates evaluated: 0
Resolved (mapped): 0
Resolved (ignored): 0
Remaining pending: 0
```

## Zero-Skill Recovery verdict

PASS after repair.

- Recovery uses stored job title/description only.
- Recovery maps evidence to existing canonical `Skill` records.
- Recovery creates `NormalizedJobSkill` rows with deterministic `rule` source only.
- Dry-run does not write.
- Apply is idempotent.
- Jobs that already have skills are skipped.
- The admin action delegates to `ZeroSkillJobRecoveryService`.

Local command results:

```text
python manage.py recover_zero_skill_jobs --active-only --dry-run --limit 200 --settings=config.settings.local
Found 4 jobs with zero skills to inspect.
Dry run: Changes rolled back.
Jobs inspected: 4
Skipped excluded/non-IT: 3
Recovered jobs: 0
Skills created: 0
Still zero-skill: 4
Skipped already skilled: 0
```

```text
python manage.py recover_zero_skill_jobs --active-only --apply --limit 200 --settings=config.settings.local
Found 4 jobs with zero skills to inspect.
Apply: Changes committed.
Jobs inspected: 4
Skipped excluded/non-IT: 3
Recovered jobs: 0
Skills created: 0
Still zero-skill: 4
Skipped already skilled: 0
```

No skills were added on the current local DB because the remaining active zero-skill jobs were excluded or did not contain supported evidence. Unit tests cover the recoverable examples required by the phase.

## False-Positive Protection verdict

PASS after repair.

Tests verify no technical skills are added to:

- `SDR/BDR - Business Developer - Cybersécurité`
- `Médiateur scientifique cybersécurité`
- `Consultant transformation digitale`
- classified `excluded_non_it` jobs with technical words in the description

## Architecture/Safety verdict

PASS.

- No matching formula changes.
- No direct OpenRouter calls from views/admin/templates.
- No France Travail calls from views/templates/admin.
- No provider calls in recovery command/admin action.
- No bulk unmatched candidate promotion.
- No migrations required.

## Tests/checks

Passed:

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test apps.skills.tests.test_ignore_rules apps.skills.tests.test_seed apps.jobs.tests.test_zero_skill_recovery --settings=config.settings.local --parallel 1
python manage.py test --settings=config.settings.local --parallel 1
npm run css:build
python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
git diff --check
git diff --cached --check || true
```

Full test result:

```text
Ran 496 tests in 112.541s
OK
```

Seed idempotency:

```text
python manage.py seed_skills --settings=config.settings.local
Successfully seeded taxonomy. Skills created: 0, Aliases created: 0.
python manage.py seed_skills --settings=config.settings.local
Successfully seeded taxonomy. Skills created: 0, Aliases created: 0.
```

CSS build passed with the existing Browserslist freshness warning.

## Safety greps

Passed:

```bash
grep -R "OpenRouterClient\|OPENROUTER\|client.chat\|_make_request" apps/*/views.py apps/*/admin.py templates -n 2>/dev/null || true
grep -R "FranceTravailClient\|search_offers\|api.francetravail" apps/*/views.py templates -n 2>/dev/null || true
grep -R "<int:" apps templates config -n 2>/dev/null || true
git diff -- . ':!.env' ':!.env.*' | grep -iE "sk-or-|Bearer [A-Za-z0-9_.-]{20,}|OPENROUTER_API_KEY=.*[^=]|FRANCE_TRAVAIL_CLIENT_SECRET=.*[^=]|EMAIL_HOST_PASSWORD=.*[^=]" || echo "OK: no obvious secrets in diff"
```

The raw/file exposure grep returned existing model/service/admin/test references only, not new template exposure from Phase 15D.

## Metrics

Before apply commands:

```text
active_zero_skill_jobs 4
strong_zero_skill_jobs 0
excluded_non_it_zero_skill_jobs 1
normalized_job_skill_rows 1224
unmatched_candidates_by_status [{'status': 'ignored', 'c': 35}, {'status': 'mapped', 'c': 323}, {'status': 'pending', 'c': 515}]
```

After apply commands:

```text
active_zero_skill_jobs 4
strong_zero_skill_jobs 0
excluded_non_it_zero_skill_jobs 1
normalized_job_skill_rows 1224
unmatched_candidates_by_status [{'status': 'ignored', 'c': 35}, {'status': 'mapped', 'c': 338}, {'status': 'pending', 'c': 500}]
```

## Remaining risks

- The current local DB had no recoverable active zero-skill jobs left, so recovery command apply did not reduce the zero-skill count. Unit tests cover the required recoverable examples.
- The Phase 15D folder had no `agent_report.md` at verification time.
- Some generated review files under `var/` remain untracked local artifacts.

## Commit recommendation

Review the diff and generated artifacts, then commit Phase 15D changes from `dev` when ready. Do not commit from `main`.
