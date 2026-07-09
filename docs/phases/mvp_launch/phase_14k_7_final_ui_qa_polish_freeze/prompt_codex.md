# Codex Prompt — Phase 14K-7 Final UI QA, Polish Freeze, and Release Readiness

You are Codex acting as senior verifier AND repair agent for TuniTech Abroad.

Current phase: **Phase 14K-7 — Final UI QA, Polish Freeze, and Release Readiness**.

You are not verification-only. You must verify, repair, improve only inside the approved design/system boundaries, test, and repeat until confident.

Use this loop:

```text
inspect -> verify -> fix in-scope issues -> enhance only within approved design docs -> test -> repeat until PASS/REPAIRED_PASS
```

Do not block for staged/unstaged/mixed working tree. Staging state is only a note. Do not commit anything.

Block only for real architecture, product, security, privacy, dependency, or scope-expansion issues.

---

## 1. Read first

Read:

```text
AGENTS.md
docs/phases/phase_14k_7_final_ui_qa_polish_freeze/tasks.md
docs/phases/phase_14k_7_final_ui_qa_polish_freeze/acceptance.md
docs/phases/phase_14k_7_final_ui_qa_polish_freeze/agent_report.md if present
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

Inspect static prototypes only as visual references:

```text
docs/design/approved_ui_ux/static_ui_prototype/
```

Do not copy fake data from prototypes.

---

## 2. Scope and allowed repair

Allowed repair files:

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
docs/phases/phase_14k_7_final_ui_qa_polish_freeze/codex_report.md
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

Exception: tests may be read, not changed.

Do not add features. Do not create routes. Do not alter matching/recommendation/CV/business logic. Do not make deployment changes.

---

## 3. Verification checklist

Inspect and repair only small in-scope issues across:

- global shell/nav/footer/messages
- homepage/auth pages
- public jobs list/detail/filters/cards
- dashboard home/sidebar/profile/CV/account/email preferences
- recommendations/saved jobs/match history/match detail
- privacy/terms/404/500
- direct partials used by these pages

Check:

- all `{% url %}` names exist
- no invalid global quick-match link
- all job/match/CV links use `public_id`
- no public integer IDs
- forms preserve CSRF/method/enctype/hidden fields/errors
- HTMX attributes preserved where existing
- Alpine behavior preserved where existing
- empty states exist
- fallback copy is safe and French
- progress bars and pagination are accessible
- no unsupported prototype-only classes if they break rendering
- CSS regenerated if templates need new Tailwind utilities

---

## 4. Canonical copy

Use only if relevant:

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

## 5. Mandatory checks

Run after repairs:

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

Security/architecture greps:

```bash
grep -R "cdn.tailwindcss.com" templates config static -n || true
grep -R "React\|Next.js\|next/\|createRoot\|vue\|angular\|Vite" package.json templates static apps -n 2>/dev/null || true
grep -R "FranceTravailClient\|search_offers\|api.francetravail" apps/*/admin.py apps/*/views.py templates -n 2>/dev/null || true
grep -R "OpenRouterClient\|OPENROUTER\|run_llm\|client.chat\|_make_request" apps/*/admin.py apps/*/views.py templates -n 2>/dev/null || true
grep -R "file.url\|cv.file.url\|upload.file.url\|raw_text\|raw_request_json\|raw_response_text\|raw_response_json" templates apps -n 2>/dev/null || true
grep -R "<int:" apps templates config -n 2>/dev/null || true
git diff -- . ':!.env' ':!.env.*' | grep -iE "sk-or-|Bearer [A-Za-z0-9_.-]{20,}|OPENROUTER_API_KEY=.*[^=]|FRANCE_TRAVAIL_CLIENT_SECRET=.*[^=]|EMAIL_HOST_PASSWORD=.*[^=]" || echo "OK: no obvious secrets in diff"
```

Classify broad existing taxonomy/test/backend hits as non-blocking if they are not introduced by this phase.

---

## 6. Route smoke

Use Django test client with `HTTP_HOST='localhost'`.

Public:

```text
/
/jobs/
/accounts/login/
/accounts/signup/
/accounts/password/reset/
/privacy/
/terms/
```

Authenticated:

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

Object routes if data exists:

```text
/jobs/<job.public_id>/
/dashboard/matches/<match.public_id>/
```

If local data does not exist, explain clearly. You may create temporary local smoke records only if safe and without migrations/backend changes. Clean them after smoke if practical.

---

## 7. Verdict rules

- `PASS`: no repair needed and all checks pass.
- `REPAIRED_PASS`: you fixed in-scope issues and all checks pass.
- `BLOCKED`: use only if fix requires product decision, backend change, dependency, privacy/security decision, or scope expansion.
- `FAIL`: use only for serious architecture/privacy/security failure or broken app after attempted repair.

Do not block for:

- staged/unstaged files
- generated CSS
- missing report file
- whitespace
- small copy mismatch
- small in-scope template issue

---

## 8. Final report

Create/update:

```text
docs/phases/phase_14k_7_final_ui_qa_polish_freeze/codex_report.md
```

Use:

```text
docs/phases/phase_14k_7_final_ui_qa_polish_freeze/codex_report_template.md
```

Report must include:

- final verdict
- exact files changed by Codex
- repairs performed
- commands and results
- route smoke results
- security grep classifications
- manual browser checklist for Baha
- final commit recommendation

Do not commit.
