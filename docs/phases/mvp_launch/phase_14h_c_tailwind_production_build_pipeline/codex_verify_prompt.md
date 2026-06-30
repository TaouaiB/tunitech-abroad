# Codex Verification Prompt — Phase 14H-C

You are verifying Phase 14H-C only.

Read:
- `AGENTS.md`
- `docs/phases/phase_14h_c_tailwind_production_build_pipeline/acceptance.md`
- `docs/phases/phase_14h_c_tailwind_production_build_pipeline/boundaries.md`
- `docs/phases/phase_14h_c_tailwind_production_build_pipeline/test_plan.md`
- `docs/phases/phase_14h_c_tailwind_production_build_pipeline/regression_security_checks.md`

Verify the implementation.
If issues are found, fix Phase 14H-C issues only, then re-run checks.
Loop until the phase is clean or clearly blocked.

Do not commit.
Do not deploy.
Do not start Phase 14H-D.
Do not configure hosting.
Do not change business logic.
Do not redesign the UI.

Must verify:
- Tailwind CDN removed.
- Local compiled CSS loaded through Django staticfiles.
- Tailwind build succeeds.
- Generated CSS exists and is non-empty.
- `node_modules/` is not tracked.
- No React/Next/Vue/Angular/SPA introduced.
- HTMX/Alpine remain functional from template perspective.
- No migrations.
- No CV privacy regression.
- No France Travail/OpenRouter calls from views/templates.
- Full tests pass.
- collectstatic dry-run passes.

Run:

```bash
cd ~/Projects/tunitech-abroad
source .venv/bin/activate

npm run css:build
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test apps.core apps.dashboard apps.cvs apps.jobs --settings=config.settings.local
python manage.py test --settings=config.settings.local --parallel 1
python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
git diff --check
```

Run regression/security checks from `regression_security_checks.md`.

Final verdict must be exactly one:
- `FINAL_VERDICT: FAIL`
- `FINAL_VERDICT: BLOCKED_HUMAN_VISUAL_SIGNOFF`
