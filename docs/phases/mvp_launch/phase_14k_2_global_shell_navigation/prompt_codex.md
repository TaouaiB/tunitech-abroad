# Codex Verification Prompt — Phase 14K-2 Global Shell, Navigation, Messages, Error/Legal Pages

You are verifying Phase 14K-2 after Gemini implementation.

You are not implementing new UI work unless the user explicitly asks. Your job is to inspect the repo, run checks, and write a strict verification report.

## 1. Read first

Read:

1. `AGENTS.md`
2. `docs/phases/phase_14k_2_global_shell_navigation/tasks.md`
3. `docs/phases/phase_14k_2_global_shell_navigation/acceptance.md`
4. `docs/phases/phase_14k_2_global_shell_navigation/prompt_gemini.md`
5. `docs/design/approved_ui_ux/README_APPROVED.md`
6. `docs/design/approved_ui_ux/design_vision/03_information_architecture_and_navigation.md`
7. `docs/design/approved_ui_ux/design_vision/04_components_specification.md`
8. `docs/design/approved_ui_ux/design_vision/10_backend_safety_and_template_guardrails.md`
9. `docs/design/approved_ui_ux/design_vision/12_french_ux_copy_dictionary.md`
10. `docs/design/approved_ui_ux/static_ui_prototype/prototype-map.html`
11. `docs/design/approved_ui_ux/static_ui_prototype/component-states.html`
12. `docs/design/approved_ui_ux/static_ui_prototype/404.html`
13. `docs/design/approved_ui_ux/static_ui_prototype/500.html`
14. `docs/design/approved_ui_ux/static_ui_prototype/privacy.html`
15. `docs/design/approved_ui_ux/static_ui_prototype/terms.html`

## 2. Verify phase boundary

Run:

```bash
git status --short
git diff --stat
git diff --name-only
```

Expected implementation changes should be limited to shell/legal/error templates, optional tiny CSS correction, and Phase 14K-2 reports/docs.

BLOCK if changed files include unexpected:

- `apps/**`
- `config/**`
- feature templates outside shell/legal/error scope
- dependency files
- `.env` files
- migrations
- Phase 14K-3 directory or work

If earlier phase files are still staged/uncommitted, BLOCK for mixed phase state.

## 3. Inspect implementation

Check these areas directly:

- `templates/base.html`
- `templates/404.html`
- `templates/500.html`
- privacy/terms templates changed by Gemini
- any partials introduced
- any CSS changes if present

Verify:

- approved `.tta-*` classes are used
- template blocks are preserved
- static asset loading is preserved
- no page content was rewritten outside scope
- route names are existing route names
- no invented `/dashboard/settings/`
- logout/auth behavior is not broken
- mobile nav has accessible behavior or fallback
- messages map to toast classes safely
- error pages do not leak debug details
- legal pages do not invent false legal promises

## 4. Required commands

Run all:

```bash
source .venv/bin/activate
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test --settings=config.settings.local --parallel 1
npm run css:build
python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
git diff --check
```

If changes are staged, also run:

```bash
git diff --cached --check
```

## 5. Required security greps

Run:

```bash
grep -R "cdn.tailwindcss.com" templates config static -n || true
grep -R "React\|Next.js\|next/\|createRoot\|vue\|angular\|Vite" package.json templates static apps -n 2>/dev/null || true
grep -R "FranceTravailClient\|search_offers\|api.francetravail" apps/*/admin.py apps/*/views.py templates -n 2>/dev/null || true
grep -R "OpenRouterClient\|OPENROUTER\|run_llm\|client.chat\|_make_request" apps/*/admin.py apps/*/views.py templates -n 2>/dev/null || true
grep -R "file.url\|cv.file.url\|upload.file.url\|raw_text\|raw_request_json\|raw_response_text\|raw_response_json" templates apps -n 2>/dev/null || true
grep -R "<int:" apps templates config -n 2>/dev/null || true
git diff -- . ':!.env' ':!.env.*' | grep -iE "sk-or-|Bearer [A-Za-z0-9_.-]{20,}|OPENROUTER_API_KEY=.*[^=]|FRANCE_TRAVAIL_CLIENT_SECRET=.*[^=]|EMAIL_HOST_PASSWORD=.*[^=]" || echo "OK: no obvious secrets in diff"
```

Classify hits carefully:

- Existing skill taxonomy mentions like React/Next/Vite are not automatically blocking.
- Existing raw text/internal model/test references are not automatically blocking.
- New forbidden implementation introduced by Phase 14K-2 is blocking.

## 6. Optional route sanity inspection

Use these commands if useful:

```bash
find config apps -maxdepth 3 -name 'urls.py' -type f | sort
python manage.py show_urls --settings=config.settings.local 2>/dev/null | head -80 || true
```

If `show_urls` is unavailable, do not install anything. Inspect URL files manually.

## 7. Manual review expectation

If you can run the server safely, inspect pages manually or explain that browser inspection was not performed. At minimum, verify by template inspection that:

- `/` should still render through base shell
- `/jobs/` should still render through base shell
- login/signup templates should still extend base correctly
- privacy/terms templates are still reachable by existing routes
- 404/500 templates are safe

## 8. Verdict rules

PASS only if:

- changed files are within scope
- no mixed-phase staged files
- no Phase 14K-3 work
- no templates outside shell/legal/error were redesigned
- base shell preserves existing blocks and asset loading
- nav uses existing routes only
- messages/toasts are safe
- legal/error pages are safe
- all required checks pass
- no new forbidden architecture/security pattern exists

BLOCK if:

- implementation is mostly fine but repo state/scope/checks need cleanup
- commands were skipped without good reason
- manual route/template confidence is insufficient

FAIL if:

- major architecture violation
- app code/provider/LLM/API behavior changed
- secrets exposed
- CV files/raw text exposed
- forbidden frontend stack introduced

## 9. Write report

Create/update:

```text
docs/phases/phase_14k_2_global_shell_navigation/codex_report.md
```

Use `codex_report_template.md`.

Include:

- PASS/BLOCKED/FAIL
- changed files
- scope verification
- route/nav verification
- message/toast verification
- legal/error verification
- commands run and outputs summary
- security grep classification
- blocking issues if any
- required fix instructions

Do not commit.
