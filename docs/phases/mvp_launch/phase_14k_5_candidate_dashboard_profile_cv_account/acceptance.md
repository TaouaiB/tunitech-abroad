# Phase 14K-5 Acceptance — Candidate Dashboard, Profile, CV, Account

## Verdict requirements

Phase 14K-5 can be accepted only with **PASS** or **REPAIRED_PASS** from Codex.

## Scope acceptance

- [ ] Only authenticated candidate/dashboard/profile/CV/account/email-preference templates were changed.
- [ ] `static/css/app.css` changed only because `npm run css:build` regenerated it.
- [ ] Phase docs/reports were added under `docs/phases/phase_14k_5_candidate_dashboard_profile_cv_account/`.
- [ ] No backend app code changed.
- [ ] No models/views/services/forms/tasks/admin/URLs/settings/migrations changed.
- [ ] No dependencies changed.
- [ ] No tests changed.
- [ ] No `.env` or secrets touched.
- [ ] Phase 14K-6 was not started.

## UI acceptance

- [ ] Dashboard uses a clear private workspace/action-center layout.
- [ ] Dashboard links use existing route names only.
- [ ] Profile page/form is readable, sectioned, responsive, and preserves all fields and validation display.
- [ ] CV page has clear private-CV messaging, status display, upload/replace UI, and safe empty/error states.
- [ ] Account/security page is clear and preserves existing account behavior.
- [ ] Email preferences page is styled if it exists and preserves existing preference behavior.
- [ ] Pages use approved `.tta-*` classes and Tailwind utilities where needed.
- [ ] Light/dark adaptive behavior remains system-based.
- [ ] Mobile layout is reasonable by inspection or route smoke.

## Privacy/security acceptance

- [ ] No CV file URL is exposed.
- [ ] No raw CV text is exposed.
- [ ] No raw LLM/provider request or response payload is exposed.
- [ ] No fake download/reparse/delete route was invented.
- [ ] No internal integer public URLs were added.
- [ ] No `matching:quick_match` link is used without `public_id`.
- [ ] No OpenRouter/LLM call was added to views/templates/admin.
- [ ] No France Travail live/API call was added to views/templates/admin.
- [ ] No React/Next/Vue/Angular/Vite implementation or dependency was introduced.
- [ ] No secrets appear in diff.

## Form/behavior acceptance

- [ ] CSRF tokens preserved.
- [ ] Form methods/actions preserved unless replacing a hardcoded path with an existing `{% url %}` route.
- [ ] Hidden inputs preserved.
- [ ] File upload forms keep `enctype="multipart/form-data"` if originally present.
- [ ] HTMX attributes preserved if originally present.
- [ ] Error loops and field errors remain visible.
- [ ] Submit buttons still submit the intended form.

## Required command acceptance

All must pass:

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test --settings=config.settings.local --parallel 1
npm run css:build
python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
git diff --check
git diff --cached --check || true
```

Security greps must show no new blocking issue.

## Report acceptance

Gemini report must exist:

```text
docs/phases/phase_14k_5_candidate_dashboard_profile_cv_account/agent_report.md
```

Codex report must exist:

```text
docs/phases/phase_14k_5_candidate_dashboard_profile_cv_account/codex_report.md
```

Codex report must state:

- final verdict
- exact files changed by Codex
- route verification
- CV privacy verification
- form behavior preservation
- commands run and results
- security grep classification
- blocking issues, if any
- commit recommendation
