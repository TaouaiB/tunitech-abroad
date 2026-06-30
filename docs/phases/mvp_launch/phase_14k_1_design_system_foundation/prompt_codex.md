# Codex Verification Prompt — Phase 14K-1 Design System Foundation

You are verifying Gemini's implementation of **Phase 14K-1 — Design System Foundation** for TuniTech Abroad.

This is verification-only. Do not implement new features. Do not redesign pages. Do not start Phase 14K-2.

## 1. Read first

Read:

```text
AGENTS.md
docs/phases/phase_14k_1_design_system_foundation/tasks.md
docs/phases/phase_14k_1_design_system_foundation/acceptance.md
docs/phases/phase_14k_1_design_system_foundation/prompt_gemini.md
docs/design/approved_ui_ux/README_APPROVED.md
docs/design/approved_ui_ux/design_vision/02_theme_tokens_tailwind.md
docs/design/approved_ui_ux/design_vision/04_components_specification.md
docs/design/approved_ui_ux/design_vision/10_backend_safety_and_template_guardrails.md
```

Then inspect the changed files.

## 2. Expected scope

Allowed changed implementation files:

```text
tailwind.config.js
static/src/css/app.css
static/css/app.css
```

Allowed report files:

```text
docs/phases/phase_14k_1_design_system_foundation/agent_report.md
docs/phases/phase_14k_1_design_system_foundation/codex_report.md
```

No other app files should change.

Block if changed unexpectedly:

```text
templates/**
apps/**
config/**
requirements*.txt
pyproject.toml
package.json
.env
.env.*
```

Also block if Phase 14K-2 or later was created.

## 3. Required verification questions

Answer these explicitly in your report:

1. Did Gemini modify only allowed files?
2. Is `darkMode: "media"` present in `tailwind.config.js`?
3. Were new dependencies added? They should not be.
4. Were templates redesigned? They should not be.
5. Were app code/views/services/models changed? They should not be.
6. Does `static/src/css/app.css` contain the required `.tta-*` design-system class families?
7. Does the CSS build pass?
8. Does Django check pass?
9. Does `git diff --check` pass?
10. Does `git diff --cached --check` pass if changes are staged?
11. Do security greps show any new forbidden pattern?
12. Did Gemini start Phase 14K-2? It must not.

## 4. Required class-family inspection

Search `static/src/css/app.css` and verify these classes or equivalent source definitions exist:

```text
.tta-page
.tta-container
.tta-card
.tta-card-hover
.tta-btn
.tta-btn-primary
.tta-btn-secondary
.tta-btn-ghost
.tta-btn-danger
.tta-badge
.tta-badge-success
.tta-badge-warning
.tta-badge-danger
.tta-skill-chip
.tta-input
.tta-select
.tta-textarea
.tta-checkbox
.tta-sticky-save-bar
.tta-drawer-backdrop
.tta-drawer-panel
.tta-dropdown-menu
.tta-progress
.tta-progress-bar
.tta-score-ring
.tta-toast-container
.tta-toast
.tta-skeleton
.tta-dropzone
.tta-pagination
.tta-empty
.tta-legal
.tta-error-page
```

If a class is missing, decide whether it is a true blocker or a minor issue. Missing foundational component classes should generally be BLOCKED.

## 5. Required commands

Run from project root:

```bash
git status --short

git diff --stat

git diff --name-only

git diff --check

git diff --cached --check || true

source .venv/bin/activate
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
npm run css:build
python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
```

If full tests are feasible, run:

```bash
python manage.py test --settings=config.settings.local --parallel 1
```

If not run, explain why and mark whether that is acceptable.

Run architecture/security greps:

```bash
grep -R "cdn.tailwindcss.com" templates config static -n || true
grep -R "React\|Next.js\|next/\|createRoot\|vue\|angular\|Vite" package.json templates static apps -n 2>/dev/null || true
grep -R "FranceTravailClient\|search_offers\|api.francetravail" apps/*/admin.py apps/*/views.py templates -n 2>/dev/null || true
grep -R "OpenRouterClient\|OPENROUTER\|run_llm\|client.chat\|_make_request" apps/*/admin.py apps/*/views.py templates -n 2>/dev/null || true
grep -R "file.url\|cv.file.url\|upload.file.url\|raw_text\|raw_request_json\|raw_response_text\|raw_response_json" templates apps -n 2>/dev/null || true
grep -R "<int:" apps templates config -n 2>/dev/null || true
git diff -- . ':!.env' ':!.env.*' | grep -iE "sk-or-|Bearer [A-Za-z0-9_.-]{20,}|OPENROUTER_API_KEY=.*[^=]|FRANCE_TRAVAIL_CLIENT_SECRET=.*[^=]|EMAIL_HOST_PASSWORD=.*[^=]" || echo "OK: no obvious secrets in diff"
```

## 6. PASS / BLOCKED / FAIL rules

Use:

- PASS only if all scope, build, check, and safety requirements pass.
- BLOCKED if there are fixable issues such as missing classes, unexpected file changes, failed CSS build, failed check, trailing whitespace, or phase boundary problems.
- FAIL only if the implementation is fundamentally wrong, uses forbidden stack, corrupts app structure, exposes secrets/CV files, or ignores the phase boundary heavily.

## 7. Report output

Create or update:

```text
docs/phases/phase_14k_1_design_system_foundation/codex_report.md
```

Use the template in `codex_report_template.md`.

Do not commit.
