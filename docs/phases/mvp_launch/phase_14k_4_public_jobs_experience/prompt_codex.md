# Codex Verify-and-Repair Prompt — Phase 14K-4 Public Jobs Experience

You are Codex acting as senior verifier, repair agent, and code reviewer for TuniTech Abroad.

Current phase: **Phase 14K-4 — Public Jobs Experience**.

## Operating mode

You must verify, fix, enhance only within approved design docs, test, and repeat until confident.

Use this loop:

```text
inspect → verify → fix in-scope issues → enhance only within approved design docs → test → re-check → repeat until PASS or REPAIRED_PASS
```

You are allowed to repair small issues directly when all are true:

1. The fix is clearly inside Phase 14K-4 scope.
2. The fix does not require a product decision.
3. The fix does not add a dependency.
4. The fix does not modify models, services, views, URLs, settings, forms, admin, tasks, or business logic.
5. The fix does not expose CV files, raw CV text, provider payloads, secrets, or internal IDs.
6. The fix follows the approved UI/UX documentation.

Do not block for:

- staged vs unstaged files
- mixed docs and implementation in the working tree
- missing report file you can create
- trailing whitespace you can clean
- generated CSS changing after `npm run css:build`
- small template route/copy/class issue you can repair safely

Block only for:

- required product decision
- missing context that blocks safe repair
- forbidden architecture change
- new route/model/service/view needed
- dependency decision
- secret/privacy risk
- CV exposure risk
- LLM/provider/France Travail live-call risk
- tests still failing after reasonable in-scope repair

Do not commit.

## Read first

- `AGENTS.md`
- `docs/phases/phase_14k_4_public_jobs_experience/tasks.md`
- `docs/phases/phase_14k_4_public_jobs_experience/acceptance.md`
- `docs/phases/phase_14k_4_public_jobs_experience/agent_report.md` if present
- `docs/design/approved_ui_ux/README_APPROVED.md`
- `docs/design/approved_ui_ux/design_vision/04_components_specification.md`
- `docs/design/approved_ui_ux/design_vision/05_page_specs_public.md`
- `docs/design/approved_ui_ux/design_vision/07_jobs_matching_recommendations_deep_spec.md`
- `docs/design/approved_ui_ux/design_vision/09_accessibility_responsive_empty_states.md`
- `docs/design/approved_ui_ux/design_vision/10_backend_safety_and_template_guardrails.md`
- `docs/design/approved_ui_ux/design_vision/12_french_ux_copy_dictionary.md`
- `docs/design/approved_ui_ux/static_ui_prototype/jobs.html`
- `docs/design/approved_ui_ux/static_ui_prototype/job-detail.html`
- `docs/design/approved_ui_ux/static_ui_prototype/component-states.html`

Then inspect:

```bash
git status --short --branch
git diff --name-only
git diff --stat
find templates/jobs -maxdepth 4 -type f | sort || true
find templates/matching -maxdepth 4 -type f | sort || true
grep -R "app_name =" apps/*/urls.py config/urls.py -n || true
grep -R "matching:quick_match\|jobs:list\|jobs:detail\|public_id\|hx-\|file.url\|raw_text\|raw_request\|raw_response" templates/jobs templates/matching apps/jobs -n 2>/dev/null || true
```

## Verify and repair scope

Allowed repair files:

- `templates/jobs/**/*.html`
- `templates/jobs/*.html`
- `templates/matching/partials/**/*.html` only if directly rendered inside public job detail/quick-match and only for visual/template polish
- `static/css/app.css` only if regenerated
- `docs/phases/phase_14k_4_public_jobs_experience/codex_report.md`

Do not edit backend app code, URLs, settings, migrations, tests, dependencies, `.env`, or future-phase/private-page templates.

## What to verify

Jobs list:

- Search/filter form still works and preserves names.
- HTMX attributes preserved if present.
- Cards are readable and professional.
- Metadata fallbacks are safe.
- Pagination works.
- Empty state exists.
- Loading/skeleton state exists if HTMX is used.
- Mobile layout is acceptable.
- No fake jobs/metrics.

Job detail:

- Route uses UUID `public_id`.
- No internal integer ID in public URL.
- No `matching:quick_match` without public_id.
- Apply/save/quick-match behavior preserved if present.
- Description and skills display safely.
- No raw payload/CV/raw text exposure.
- Canonical French labels used where relevant.

## Required checks

Run after any repair:

```bash
source .venv/bin/activate
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test --settings=config.settings.local --parallel 1
npm run css:build
python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
git diff --check
git diff --cached --check || true
```

Run security checks:

```bash
grep -R "cdn.tailwindcss.com" templates config static -n || true
grep -R "React\|Next.js\|next/\|createRoot\|vue\|angular\|Vite" package.json templates static apps -n 2>/dev/null || true
grep -R "FranceTravailClient\|search_offers\|api.francetravail" apps/*/admin.py apps/*/views.py templates -n 2>/dev/null || true
grep -R "OpenRouterClient\|OPENROUTER\|run_llm\|client.chat\|_make_request" apps/*/admin.py apps/*/views.py templates -n 2>/dev/null || true
grep -R "file.url\|cv.file.url\|upload.file.url\|raw_text\|raw_request_json\|raw_response_text\|raw_response_json" templates apps -n 2>/dev/null || true
grep -R "<int:" apps templates config -n 2>/dev/null || true
git diff -- . ':!.env' ':!.env.*' | grep -iE "sk-or-|Bearer [A-Za-z0-9_.-]{20,}|OPENROUTER_API_KEY=.*[^=]|FRANCE_TRAVAIL_CLIENT_SECRET=.*[^=]|EMAIL_HOST_PASSWORD=.*[^=]" || echo "OK: no obvious secrets in diff"
```

Classify existing broad hits. Only block if this phase introduced a real forbidden implementation or exposure.

## Supplemental route smoke

Smoke-check using Django test client, preferably with `HTTP_HOST='localhost'`:

- `/jobs/`
- `/`
- `/accounts/login/`
- one real job detail route if a local job exists

If no local job exists, document that job detail smoke was skipped.

## Verdict rules

- PASS: no repair needed and all checks pass.
- REPAIRED_PASS: you fixed one or more small in-scope issues and all checks pass.
- BLOCKED: only for product/architecture/security/privacy/dependency/missing-context issues or unresolved tests after reasonable in-scope repair.
- FAIL: serious out-of-scope implementation, forbidden stack, privacy leak, or broken architecture.

## Report

Create or update:

`docs/phases/phase_14k_4_public_jobs_experience/codex_report.md`

Use:

`docs/phases/phase_14k_4_public_jobs_experience/codex_report_template.md`

Report must include:

- final verdict
- exact files Codex changed
- repairs made
- commands run and results
- route smoke results
- security grep classification
- final commit recommendation

Do not commit.
