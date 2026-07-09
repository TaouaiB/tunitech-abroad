# Gemini Implementation Prompt — Phase 14K-6 Recommendations, Saved Jobs, Matches

You are Gemini acting as implementation agent for TuniTech Abroad.

Current phase: **Phase 14K-6 — Recommendations, Saved Jobs, Match History, Match Detail**.

Use this loop:

```text
inspect → implement/verify → fix in-scope issues → enhance only within approved design docs → test → repeat until PASS/REPAIRED_PASS
```

Do not stop at the first small issue. Fix in-scope template issues yourself.

Do not block for staged/unstaged/mixed working tree, generated CSS, missing report file, whitespace, small copy mismatch, or small template route issues that can be repaired with existing routes.

Block only for a real product/backend/security/privacy/dependency/future-phase problem.

Do not commit.

---

## 1. Read first

Read:

```text
AGENTS.md
docs/phases/phase_14k_6_recommendations_saved_matches/tasks.md
docs/phases/phase_14k_6_recommendations_saved_matches/acceptance.md
docs/design/approved_ui_ux/README_APPROVED.md
docs/design/approved_ui_ux/design_vision/03_information_architecture_and_navigation.md
docs/design/approved_ui_ux/design_vision/04_components_specification.md
docs/design/approved_ui_ux/design_vision/06_page_specs_private_dashboard.md
docs/design/approved_ui_ux/design_vision/07_jobs_matching_recommendations_deep_spec.md
docs/design/approved_ui_ux/design_vision/09_accessibility_responsive_empty_states.md
docs/design/approved_ui_ux/design_vision/10_backend_safety_and_template_guardrails.md
docs/design/approved_ui_ux/design_vision/11_page_by_page_final_blueprint.md
docs/design/approved_ui_ux/design_vision/12_french_ux_copy_dictionary.md
docs/design/approved_ui_ux/static_ui_prototype/recommendations.html
docs/design/approved_ui_ux/static_ui_prototype/saved-jobs.html
docs/design/approved_ui_ux/static_ui_prototype/match-history.html
docs/design/approved_ui_ux/static_ui_prototype/match-detail.html
```

Then inspect actual repo templates and URL names. Do not assume template paths.

Suggested inspection:

```bash
find templates -maxdepth 5 -type f | sort
find apps -path '*/templates/*' -type f | sort
grep -R "app_name =" apps/*/urls.py config/urls.py -n || true
grep -R "recommendation\|saved\|match\|quick_match\|public_id\|hx-" templates apps/*/urls.py -n 2>/dev/null || true
git status --short
```

---

## 2. Implementation scope

Allowed files:

- Existing recommendations templates.
- Existing saved jobs templates.
- Existing match history templates.
- Existing match detail/result templates.
- Small partials directly used by those pages.
- `static/css/app.css` after `npm run css:build`.
- `docs/phases/phase_14k_6_recommendations_saved_matches/agent_report.md`.

Do not modify backend Python, URL config, settings, migrations, dependencies, tests, `.env`, or future phase templates.

Do not redesign jobs, homepage, auth, dashboard home/profile/CV/account/email preference pages.

---

## 3. Implementation requirements

### Recommendations

Polish the recommendations page using the approved design. Preserve real context and existing routes only.

- Use cards/list layout.
- Show existing fit score/badges if available.
- Show existing reasons/missing skills if available.
- Add empty state if no recommendations.
- Preserve save/view/apply actions if present.
- No fake recommendation data.

### Saved jobs

- Use readable saved-job cards.
- Preserve unsave/save forms and HTMX behavior.
- Link to job detail using `public_id` only.
- Add empty state with CTA to jobs search.

### Match history

- Use readable history cards/table.
- Show score/status/date if available.
- Link to details using existing routes and public IDs only.
- Add empty state.

### Match detail

Use clear sections with approved French labels:

```text
Compatibilités
Compétences requises manquantes
Compétences optionnelles à renforcer
Points de vigilance
```

Also include score summary and next action area using existing data only.

Do not change score formula, matching logic, recommendation logic, saved jobs logic, or LLM behavior.

---

## 4. Required checks

Run after implementation and after repairs:

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

Run security greps:

```bash
grep -R "cdn.tailwindcss.com" templates config static -n || true
grep -R "React\|Next.js\|next/\|createRoot\|vue\|angular\|Vite" package.json templates static apps -n 2>/dev/null || true
grep -R "FranceTravailClient\|search_offers\|api.francetravail" apps/*/admin.py apps/*/views.py templates -n 2>/dev/null || true
grep -R "OpenRouterClient\|OPENROUTER\|run_llm\|client.chat\|_make_request" apps/*/admin.py apps/*/views.py templates -n 2>/dev/null || true
grep -R "file.url\|cv.file.url\|upload.file.url\|raw_text\|raw_request_json\|raw_response_text\|raw_response_json" templates apps -n 2>/dev/null || true
grep -R "<int:" apps templates config -n 2>/dev/null || true
git diff -- . ':!.env' ':!.env.*' | grep -iE "sk-or-|Bearer [A-Za-z0-9_.-]{20,}|OPENROUTER_API_KEY=.*[^=]|FRANCE_TRAVAIL_CLIENT_SECRET=.*[^=]|EMAIL_HOST_PASSWORD=.*[^=]" || echo "OK: no obvious secrets in diff"
```

Run route smoke for authenticated pages if practical using `HTTP_HOST='localhost'`. Inspect URLs first.

---

## 5. Report

Create/update:

```text
docs/phases/phase_14k_6_recommendations_saved_matches/agent_report.md
```

Use the report template. Include exact files changed, repairs, tests, grep classification, and stop confirmation.

Do not commit.
