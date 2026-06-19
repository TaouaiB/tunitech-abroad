# Gemini Implementation Prompt — Phase 14K-3 Public Front Door and Auth

You are Gemini acting as implementation agent for TuniTech Abroad.

You must implement Phase 14K-3 only.

## Operating mode: implement + verify + repair loop

You must not stop at the first small failure.

Work in this loop:

```text
inspect → implement inside phase scope → run checks → fix in-scope issues → re-run checks → repeat until PASS/REPAIRED_PASS
```

Do not block for:

- staged vs unstaged files
- mixed working tree
- missing report file you can create
- trailing whitespace you can clean
- generated `static/css/app.css` changing after `npm run css:build`
- small copy/test mismatch you can fix safely
- small template route issue you can fix by using an existing route or removing the invalid link

Block only if the required fix needs:

- backend model/view/service/task/form/admin/URL/settings change
- new dependency
- product decision
- privacy/security decision
- new route
- forbidden architecture
- future-phase scope

Do not commit.

## Read first

Read these files before editing:

- `AGENTS.md`
- `docs/phases/phase_14k_3_public_frontdoor_auth/tasks.md`
- `docs/phases/phase_14k_3_public_frontdoor_auth/acceptance.md`
- `docs/design/approved_ui_ux/README_APPROVED.md`
- `docs/design/approved_ui_ux/design_vision/00_product_ux_principles.md`
- `docs/design/approved_ui_ux/design_vision/01_brand_and_visual_identity.md`
- `docs/design/approved_ui_ux/design_vision/03_information_architecture_and_navigation.md`
- `docs/design/approved_ui_ux/design_vision/04_components_specification.md`
- `docs/design/approved_ui_ux/design_vision/05_page_specs_public.md`
- `docs/design/approved_ui_ux/design_vision/08_forms_auth_cv_profile_spec.md`
- `docs/design/approved_ui_ux/design_vision/09_accessibility_responsive_empty_states.md`
- `docs/design/approved_ui_ux/design_vision/10_backend_safety_and_template_guardrails.md`
- `docs/design/approved_ui_ux/design_vision/11_page_by_page_final_blueprint.md`
- `docs/design/approved_ui_ux/design_vision/12_french_ux_copy_dictionary.md`
- `docs/design/approved_ui_ux/static_ui_prototype/prototype-map.html`
- `docs/design/approved_ui_ux/static_ui_prototype/index.html`
- `docs/design/approved_ui_ux/static_ui_prototype/login.html`
- `docs/design/approved_ui_ux/static_ui_prototype/signup.html`

Only read `docs/design/approved_ui_ux/static_ui_prototype/cv-checker.html` if a real existing route/template for that page exists in the current repo. Do not create a route for it.

## Discover current implementation

Before editing, run/discover:

```bash
find templates -maxdepth 4 -type f | sort
find apps -path '*/templates/*' -type f | sort
grep -R "app_name =" apps/*/urls.py config/urls.py -n || true
grep -R "name=.*home\|name=.*login\|name=.*signup\|name=.*password\|name=.*cv\|name=.*checker" apps/*/urls.py config/urls.py -n || true
git status --short
```

Use the actual current template paths. Do not guess.

## Scope to implement

### 1. Homepage / public front door

Redesign the existing homepage template using the approved prototype and `.tta-*` classes.

Requirements:

- Search-first hero.
- France-first value proposition.
- Clear target audience: Tunisian IT candidates, students, bootcamp graduates, internship/PFE seekers, junior/mid developers.
- GET search form to existing jobs list route, likely `{% url 'jobs:list' %}`.
- Use existing query parameter names if already used by the current jobs search. If unsure, use `q` only.
- Primary CTA: existing jobs list.
- Secondary CTA: only if it points to a real current route that does not require object context.
- Include `id="comment-ca-marche"` section.
- Explain the product loop: profile/CV → France jobs/internships → matching → missing skills → recommendations.
- Do not add fake stats unless they are clearly generic labels or already present in context.
- Do not redesign `/jobs/`; that is Phase 14K-4.

### 2. Auth / allauth pages

Improve existing auth templates using `.tta-*` classes.

Requirements:

- Login page polished.
- Signup page polished.
- Password reset/change/email confirmation pages if present and safe to style.
- Preserve allauth form behavior.
- Preserve `{% csrf_token %}`.
- Preserve hidden `next` fields and redirect behavior.
- Preserve social provider buttons/tags if present.
- Preserve form errors and non-field errors.
- Do not add django-widget-tweaks or a new package.
- Do not modify Python forms.
- If fields cannot easily receive `.tta-input` without a filter/package, style the form container and preserve native rendering rather than breaking form behavior.

### 3. Optional existing CV checker page

Only if a real existing public CV checker route/template already exists:

- Style the existing template.
- Preserve behavior.
- Do not introduce public CV file exposure.
- Do not create any new route or view.

If no real route/template exists, do nothing for CV checker and document it.

## Allowed files

Allowed to edit existing templates in these areas:

- homepage/public core templates, for example:
  - `templates/core/*.html`
  - `apps/core/templates/core/*.html`
- auth/allauth templates, for example:
  - `templates/account/*.html`
  - `templates/socialaccount/*.html`
  - `templates/allauth/**/*.html` if present
- `static/css/app.css` only if regenerated by `npm run css:build`
- `docs/phases/phase_14k_3_public_frontdoor_auth/agent_report.md`

If actual current repo uses different public/auth template paths, you may edit those existing paths but must document them.

## Forbidden

Do not modify:

- `apps/**/models.py`
- `apps/**/views.py`
- `apps/**/services/**`
- `apps/**/tasks.py`
- `apps/**/forms.py`
- `apps/**/admin.py`
- `apps/**/urls.py`
- `config/**`
- migrations
- tests
- dependencies
- `.env` files
- jobs list/detail templates
- dashboard/profile/CV/recommendation/matching templates
- Phase 14K-4+ files

Do not add new routes or views.

## Specific route safety rules

Do not use:

```django
{% url 'matching:quick_match' %}
```

That route is job-scoped and requires `public_id`.

Before adding any link, verify the route exists and does not require missing arguments.

If no safe existing route exists for a CTA, remove that CTA rather than inventing a route.

## Required checks

After implementation, run:

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

Then run:

```bash
grep -R "cdn.tailwindcss.com" templates config static -n || true
grep -R "React\|Next.js\|next/\|createRoot\|vue\|angular\|Vite" package.json templates static apps -n 2>/dev/null || true
grep -R "FranceTravailClient\|search_offers\|api.francetravail" apps/*/admin.py apps/*/views.py templates -n 2>/dev/null || true
grep -R "OpenRouterClient\|OPENROUTER\|run_llm\|client.chat\|_make_request" apps/*/admin.py apps/*/views.py templates -n 2>/dev/null || true
grep -R "file.url\|cv.file.url\|upload.file.url\|raw_text\|raw_request_json\|raw_response_text\|raw_response_json" templates apps -n 2>/dev/null || true
grep -R "<int:" apps templates config -n 2>/dev/null || true
git diff -- . ':!.env' ':!.env.*' | grep -iE "sk-or-|Bearer [A-Za-z0-9_.-]{20,}|OPENROUTER_API_KEY=.*[^=]|FRANCE_TRAVAIL_CLIENT_SECRET=.*[^=]|EMAIL_HOST_PASSWORD=.*[^=]" || echo "OK: no obvious secrets in diff"
```

Classify broad pre-existing grep hits; do not treat existing skill names or tests as blockers unless this phase introduced them.

## Repair loop requirement

If a command fails:

1. Read the error.
2. If the fix is inside allowed template/static/report scope, fix it.
3. Re-run the failed command and any relevant checks.
4. Continue until all required checks pass.

Do not hand off a tiny template/copy/route/whitespace issue to Baha.

## Final report

Create/update:

`docs/phases/phase_14k_3_public_frontdoor_auth/agent_report.md`

Use the template:

`docs/phases/phase_14k_3_public_frontdoor_auth/agent_report_template.md`

Final status must be one of:

- PASS
- REPAIRED_PASS
- BLOCKED
- FAIL

Do not commit.
