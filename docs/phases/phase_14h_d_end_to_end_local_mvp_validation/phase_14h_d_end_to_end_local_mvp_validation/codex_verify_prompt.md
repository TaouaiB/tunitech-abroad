# Codex Verification Prompt — Phase 14H-D

You are verifying Phase 14H-D only.

Read:

- AGENTS.md
- docs/phases/phase_14h_d_end_to_end_local_mvp_validation/README.md
- docs/phases/phase_14h_d_end_to_end_local_mvp_validation/acceptance.md
- docs/phases/phase_14h_d_end_to_end_local_mvp_validation/test_plan.md
- docs/phases/phase_14h_d_end_to_end_local_mvp_validation/regression_security_checks.md
- docs/validation/local_mvp_e2e_report.md if present

## Task

Verify the Gemini/agent Phase 14H-D work.

If issues are found, fix Phase 14H-D issues only and re-run checks.

## Strict boundaries

- Do not commit.
- Do not deploy.
- Do not start Phase 14I.
- Do not redesign UI.
- Do not add new product features.
- Do not change matching scoring.
- Do not change LLM/job/CV logic unless a clear E2E blocker is found.

## Required checks

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
npm run css:build
python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
python manage.py test apps.core apps.accounts apps.dashboard apps.cvs apps.jobs apps.matching apps.recommendations apps.privacy --settings=config.settings.local
python manage.py test --settings=config.settings.local --parallel 1
git diff --check
```

Run the regression/security greps from `regression_security_checks.md`.

## Verify report quality

`docs/validation/local_mvp_e2e_report.md` must mention:

- Branch/commit
- Services used
- Browser pages/flows tested or marked as human-blocked
- CV upload/parse status result
- Job ingestion smoke result
- Matching/recommendation result
- Privacy/deletion result or why not executed
- Remaining risks

## Final verdict

Use only:

```text
FINAL_VERDICT: FAIL
```

or

```text
FINAL_VERDICT: BLOCKED_HUMAN_VISUAL_SIGNOFF
```
