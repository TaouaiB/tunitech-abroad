# Gemini Prompt — Phase 14K-7 Final UI QA, Polish Freeze, and Release Readiness

You are Gemini acting as implementation/QA agent for TuniTech Abroad.

Current phase: **Phase 14K-7 — Final UI QA, Polish Freeze, and Release Readiness**.

You are not verification-only. You must use this loop:

```text
inspect -> verify -> fix in-scope issues -> enhance only within approved design docs -> test -> repeat until PASS/REPAIRED_PASS
```

Do not block for staged/unstaged/mixed working-tree state. Do not block for generated CSS changes, whitespace, missing report file, or small fixable template/copy/accessibility issues.

Block only for real architecture, product, security, privacy, dependency, or scope-expansion problems.

Do not commit.

---

## 1. Read first

Read these files before editing:

```text
AGENTS.md
docs/phases/phase_14k_7_final_ui_qa_polish_freeze/tasks.md
docs/phases/phase_14k_7_final_ui_qa_polish_freeze/acceptance.md
docs/design/approved_ui_ux/README_APPROVED.md
docs/design/approved_ui_ux/design_vision/03_information_architecture_and_navigation.md
docs/design/approved_ui_ux/design_vision/04_components_specification.md
docs/design/approved_ui_ux/design_vision/05_page_specs_public.md
docs/design/approved_ui_ux/design_vision/06_page_specs_private_dashboard.md
docs/design/approved_ui_ux/design_vision/07_jobs_matching_recommendations_deep_spec.md
docs/design/approved_ui_ux/design_vision/08_forms_auth_cv_profile_spec.md
docs/design/approved_ui_ux/design_vision/09_accessibility_responsive_empty_states.md
docs/design/approved_ui_ux/design_vision/10_backend_safety_and_template_guardrails.md
docs/design/approved_ui_ux/design_vision/11_page_by_page_final_blueprint.md
docs/design/approved_ui_ux/design_vision/12_french_ux_copy_dictionary.md
```

Also inspect relevant static prototypes under:

```text
docs/design/approved_ui_ux/static_ui_prototype/
```

---

## 2. Inspect current repo state

Run:

```bash
git status --short
find templates -maxdepth 5 -type f | sort
find apps -path '*/templates/*' -type f | sort
grep -R "app_name =" apps/*/urls.py config/urls.py -n || true
grep -R "url '.*'\|{% url\|public_id\|hx-\|x-data\|file.url\|raw_text\|matching:quick_match" templates apps/*/urls.py -n 2>/dev/null || true
```

Treat existing staged/unstaged files as normal worktree state. Do not block because of staging.

---

## 3. Scope

This is final UI QA/hardening only.

You may fix small issues in:

```text
templates/base.html
templates/404.html
templates/500.html
templates/core/home.html
templates/account/*.html
templates/jobs/**/*.html
templates/dashboard/**/*.html
templates/cvs/partials/cv_status.html
templates/cvs/partials/cv_parsed_summary.html
templates/matching/**/*.html
templates/recommendations/**/*.html
templates/privacy/**/*.html
apps/privacy/templates/privacy/*.html
static/src/css/app.css
static/css/app.css
docs/phases/phase_14k_7_final_ui_qa_polish_freeze/agent_report.md
```

Do not edit:

```text
apps/**/models.py
apps/**/views.py
apps/**/services/**
apps/**/tasks.py
apps/**/forms.py
apps/**/admin.py
apps/**/urls.py
config/**
requirements*.txt
pyproject.toml
package.json
package-lock.json
migrations
tests
.env
.env.*
```

Do not redesign from scratch. Do not expand features. Do not create routes.

---

## 4. What to verify and fix

Verify and repair only small in-scope issues across:

1. Global shell/navigation/footer/messages.
2. Homepage/auth pages.
3. Jobs list/detail/filters/cards/quick-match panel.
4. Dashboard home/sidebar/profile/CV/account/email preferences.
5. Recommendations/saved jobs/match history/match detail.
6. Privacy/terms/404/500.
7. Direct partials used by those pages.

Fix examples that are allowed:

- broken `{% url %}` tag
- missing `public_id`
- fake route link
- hardcoded source fallback when source missing
- small French copy drift
- missing empty-state fallback
- missing form label
- missing `aria-current` on pagination
- progress bar missing `role="progressbar"`
- unsupported prototype-only class where existing class is available
- trailing whitespace
- regenerated CSS after Tailwind build

Do not fix by editing backend. If a fix requires backend work, report BLOCKED with exact reason.

---

## 5. Canonical copy

Use these labels where relevant:

```text
Compatibilités
Compétences requises manquantes
Compétences optionnelles à renforcer
Points de vigilance
Test rapide
Bon potentiel
Très bon match
Match partiel
Faible compatibilité
Postuler sur la source
Postuler sur France Travail only if source is clearly France Travail
Source non précisée
Entreprise non précisée
Lieu non précisé
Description non disponible
```

---

## 6. Mandatory safety checks

No template may expose:

```text
file.url
cv.file.url
upload.file.url
raw_text
raw_request_json
raw_response_text
raw_response_json
internal integer IDs
secrets
```

No template/view/admin may introduce:

```text
FranceTravailClient
search_offers
api.francetravail
OpenRouterClient
OPENROUTER
run_llm
client.chat
_make_request
```

---

## 7. Required commands

After repairs, run:

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

Then run greps:

```bash
grep -R "cdn.tailwindcss.com" templates config static -n || true
grep -R "React\|Next.js\|next/\|createRoot\|vue\|angular\|Vite" package.json templates static apps -n 2>/dev/null || true
grep -R "FranceTravailClient\|search_offers\|api.francetravail" apps/*/admin.py apps/*/views.py templates -n 2>/dev/null || true
grep -R "OpenRouterClient\|OPENROUTER\|run_llm\|client.chat\|_make_request" apps/*/admin.py apps/*/views.py templates -n 2>/dev/null || true
grep -R "file.url\|cv.file.url\|upload.file.url\|raw_text\|raw_request_json\|raw_response_text\|raw_response_json" templates apps -n 2>/dev/null || true
grep -R "<int:" apps templates config -n 2>/dev/null || true
git diff -- . ':!.env' ':!.env.*' | grep -iE "sk-or-|Bearer [A-Za-z0-9_.-]{20,}|OPENROUTER_API_KEY=.*[^=]|FRANCE_TRAVAIL_CLIENT_SECRET=.*[^=]|EMAIL_HOST_PASSWORD=.*[^=]" || echo "OK: no obvious secrets in diff"
```

Classify broad existing hits instead of blocking automatically.

---

## 8. Route smoke

Run Django test-client route smoke with `HTTP_HOST='localhost'`.

Public pages:

```text
/
/jobs/
/accounts/login/
/accounts/signup/
/accounts/password/reset/
/privacy/
/terms/
```

Authenticated pages:

```text
/dashboard/
/dashboard/profile/
/dashboard/cv/
/dashboard/recommendations/
/dashboard/saved-jobs/
/dashboard/matches/
/dashboard/email-preferences/
/dashboard/account/
```

Object pages if records exist:

```text
/jobs/<job.public_id>/
/dashboard/matches/<match.public_id>/
```

If no object data exists, report that clearly. Do not create backend code just for smoke.

---

## 9. Final report

Create/update:

```text
docs/phases/phase_14k_7_final_ui_qa_polish_freeze/agent_report.md
```

Use the template structure from:

```text
docs/phases/phase_14k_7_final_ui_qa_polish_freeze/agent_report_template.md
```

Final verdict must be one of:

- `PASS`
- `REPAIRED_PASS`
- `BLOCKED`
- `FAIL`

Do not commit.
