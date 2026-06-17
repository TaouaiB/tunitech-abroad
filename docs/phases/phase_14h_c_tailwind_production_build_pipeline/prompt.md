# Prompt — Phase 14H-C Tailwind Production Build Pipeline

You are working on TuniTech Abroad.

Read before editing:
- `AGENTS.md`
- `docs/phases/phase_14h_c_tailwind_production_build_pipeline/scope.md`
- `docs/phases/phase_14h_c_tailwind_production_build_pipeline/tasks.md`
- `docs/phases/phase_14h_c_tailwind_production_build_pipeline/acceptance.md`
- `docs/phases/phase_14h_c_tailwind_production_build_pipeline/boundaries.md`
- `docs/phases/phase_14h_c_tailwind_production_build_pipeline/test_plan.md`
- `docs/phases/phase_14h_c_tailwind_production_build_pipeline/regression_security_checks.md`

Mission:
Replace the Tailwind CDN with a local Tailwind CLI build pipeline while keeping the current Django-template UI and behavior stable.

Work automatically through Phase 14H-C only.

Do not commit.
Do not deploy.
Do not start Phase 14H-D.
Do not configure deployment hosting.
Do not change business logic.
Do not redesign the app.

Implementation requirements:
1. Remove `https://cdn.tailwindcss.com` from `templates/base.html`.
2. Add Tailwind build files using a simple CLI approach.
3. Add `npm run css:build` and `npm run css:watch`.
4. Compile CSS into a Django static path, preferably `static/css/app.css`.
5. Load compiled CSS from `templates/base.html` using `{% static 'css/app.css' %}`.
6. Add a small test proving the CDN is gone and local CSS is referenced/existing.
7. Update docs with local/deploy static build instructions.
8. Keep HTMX and Alpine intact.
9. Do not add React/Next/Vue/Angular/Vite app architecture.

Required checks:
- `npm run css:build`
- `python manage.py check --settings=config.settings.local`
- `python manage.py makemigrations --check --dry-run --settings=config.settings.local`
- `python manage.py test apps.core apps.dashboard apps.cvs apps.jobs --settings=config.settings.local`
- `python manage.py test --settings=config.settings.local --parallel 1`
- `python manage.py collectstatic --dry-run --noinput --settings=config.settings.local`
- `git diff --check`
- all commands from regression_security_checks.md

Final report must include:
- Files changed
- Exact CSS build approach
- Commands run and results
- Manual browser pages to inspect
- Remaining risks
- FINAL_VERDICT: FAIL or FINAL_VERDICT: BLOCKED_HUMAN_VISUAL_SIGNOFF
