# Phase 14K-4 — Public Jobs Experience

## Status

Not started until Baha explicitly runs the Gemini prompt.

## Purpose

Polish the public jobs browsing experience using the approved UI/UX design package and the Phase 14K design system already imported into the repository.

This phase must make the public job pages look professional and consistent without changing the backend architecture, search logic, ingestion logic, matching logic, or route structure.

## Product goal

A visitor should be able to:

1. Open `/jobs/`.
2. Understand this is a France-first IT jobs experience for Tunisian candidates.
3. Search/filter jobs using the existing local PostgreSQL-backed filters.
4. Read clean job cards with meaningful metadata and skill chips.
5. Use pagination without confusion.
6. Open a job detail page by UUID public ID.
7. Understand job details, extracted skills, source/apply action, and quick-match entry points.
8. See useful empty/loading states.
9. Use the page on mobile with a good filter experience.

## Approved design references

Agents must use these as source of truth:

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

## Allowed files

Implementation may modify only public jobs templates and generated CSS if rebuilt:

- `templates/jobs/**/*.html`
- `templates/jobs/*.html`
- `templates/matching/partials/**/*.html` only if the partial is directly rendered inside a public job detail/quick-match panel and only for visual/template polish
- `static/css/app.css` only if changed by `npm run css:build`
- `docs/phases/phase_14k_4_public_jobs_experience/agent_report.md`
- `docs/phases/phase_14k_4_public_jobs_experience/codex_report.md`

If the project stores jobs templates under another existing template directory, the agent may edit those existing job-list/job-detail/partial templates only after proving they are public jobs templates.

## Forbidden files and actions

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
- tests, unless Baha explicitly approves
- dependency files such as `requirements*.txt`, `pyproject.toml`, `package.json`, `package-lock.json`
- `.env`, `.env.*`, or any secret file
- dashboard/profile/CV/recommendations/match-history private pages
- homepage/auth templates from Phase 14K-3 unless a tiny shared regression caused by this phase must be repaired and documented

Do not:

- create a new route
- create `/cv-checker/`
- create a fake apply flow
- call France Travail from public pages
- call OpenRouter/LLM from templates or views
- expose CV files or raw CV text
- expose raw provider payloads
- introduce React, Next.js, Vue, Angular, Vite, SPA architecture, FastAPI, SQLAlchemy, MongoDB, or a new frontend dependency
- change search, filtering, ranking, ingestion, enrichment, matching, or recommendation business logic
- change scoring rules
- use internal integer IDs in public URLs

## Required behavior preservation

The implementation must preserve:

- existing URL names
- existing job list route
- existing job detail route
- existing UUID `public_id` behavior
- existing filter query parameter names
- existing search form behavior
- existing pagination behavior
- existing HTMX attributes and targets if already present
- existing save/unsave behavior if job cards/detail include it
- existing quick-match entry points if present
- existing CSRF tokens and method/action values
- existing permission checks and anonymous/authenticated behavior

## Required UI work

### Jobs list

Improve the public jobs list page using the approved design:

- Page header with clear title and supportive French copy.
- Search-first layout with filters presented clearly.
- Desktop layout: filter panel + job results.
- Mobile layout: filter drawer or clean stacked filter section using existing Alpine/HTMX if already available.
- Job cards using `.tta-card`, `.tta-job-card`, `.tta-badge`, `.tta-skill-chip`, `.tta-card-hover`, and utility fallbacks where needed.
- Clean metadata row: contract, location, remote/hybrid/on-site if available, source, publication date if available.
- Skill chips that avoid huge raw sentence chips.
- Empty state using `.tta-empty` when no jobs match.
- Pagination using `.tta-pagination` classes.
- Loading/skeleton state for HTMX if the current page already uses HTMX.
- Preserve all current filters and names.

### Job detail

Improve the public job detail page:

- Strong heading area with title, company/source, location, contract, remote info, and source/apply CTA.
- Body content with clear readable sections.
- Skills grouped clearly:
  - required skills
  - optional/extracted skills
  - empty/pending/failure states if already provided by context
- Use canonical French labels from `12_french_ux_copy_dictionary.md`.
- Action/sidebar panel for apply/save/quick match if current context already supports it.
- No new backend behavior.
- Apply copy must be safe:
  - use `Postuler sur la source` unless the current data explicitly identifies France Travail.
  - use `Postuler sur France Travail` only when the current source is France Travail.
- No public internal integer IDs.

### Job card variants and states

Agents must handle common data quality cases safely:

- missing title
- missing company
- missing location
- missing salary
- missing skills
- pending/enrichment statuses if exposed by context
- expired or inactive job state if visible

Do not invent data. Use fallbacks such as:

- `Offre IT sans titre` only if title is missing
- `Entreprise non précisée`
- `Lieu non précisé`
- `Compétences en cours d’analyse`
- `Aucune compétence spécifique extraite`

## Agent repair-loop behavior

Gemini and Codex must operate as:

`inspect → implement/verify → fix in-scope issues → enhance only within approved design docs → test → repeat until PASS or REPAIRED_PASS`

Do not stop at the first small issue if the fix is in scope and safe.

Do not block for:

- staged vs unstaged files
- mixed docs and implementation in the working tree
- missing report file that can be created
- trailing whitespace that can be cleaned
- small copy mismatch that can be safely fixed
- generated CSS changing after `npm run css:build`
- small template route mistake that can be repaired without adding URLs/views/models

Block only for:

- product decision needed
- missing context needed
- forbidden architecture change needed
- new route/model/service/view required
- dependency decision required
- secret/privacy risk
- CV exposure risk
- provider/LLM/France Travail live-call risk
- tests still failing after reasonable in-scope repair

## Required checks

Run and pass:

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

Run and classify:

```bash
grep -R "cdn.tailwindcss.com" templates config static -n || true
grep -R "React\|Next.js\|next/\|createRoot\|vue\|angular\|Vite" package.json templates static apps -n 2>/dev/null || true
grep -R "FranceTravailClient\|search_offers\|api.francetravail" apps/*/admin.py apps/*/views.py templates -n 2>/dev/null || true
grep -R "OpenRouterClient\|OPENROUTER\|run_llm\|client.chat\|_make_request" apps/*/admin.py apps/*/views.py templates -n 2>/dev/null || true
grep -R "file.url\|cv.file.url\|upload.file.url\|raw_text\|raw_request_json\|raw_response_text\|raw_response_json" templates apps -n 2>/dev/null || true
grep -R "<int:" apps templates config -n 2>/dev/null || true
git diff -- . ':!.env' ':!.env.*' | grep -iE "sk-or-|Bearer [A-Za-z0-9_.-]{20,}|OPENROUTER_API_KEY=.*[^=]|FRANCE_TRAVAIL_CLIENT_SECRET=.*[^=]|EMAIL_HOST_PASSWORD=.*[^=]" || echo "OK: no obvious secrets in diff"
```

## Supplemental route/browser checks

At minimum, smoke-check these routes using Django test client or browser:

- `/jobs/`
- one real job detail URL if a job exists locally
- `/` should still render after changes
- `/accounts/login/` should still render after changes

If there are no jobs locally, document that job detail smoke was skipped because no job exists.

## Completion output

Gemini must update:

- `docs/phases/phase_14k_4_public_jobs_experience/agent_report.md`

Codex must update:

- `docs/phases/phase_14k_4_public_jobs_experience/codex_report.md`

Reports must include final verdict and exact changed files.
