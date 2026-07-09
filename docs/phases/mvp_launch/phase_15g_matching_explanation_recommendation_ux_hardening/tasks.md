# Phase 15G Tasks — Matching Explanation and Recommendation UX Hardening

## Task 0 — Preflight

Run before editing:

```bash
cd ~/Projects/tunitech-abroad
source .venv/bin/activate

git status --short --branch
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
```

Do not block for unrelated unstaged files, but do not overwrite user work. Report pre-existing files clearly.

## Task 1 — Inspect matching and recommendation flow

Inspect, without changing behavior yet:

- Matching scoring service.
- Match detail view.
- Match result/presentation helpers.
- Recommendation services and views.
- Templates rendering match detail, saved jobs, and recommendations.
- Tests around matching, recommendations, job cards, and dashboard pages.

Find where these are produced:

- final fit score
- technical score
- experience score
- language score
- location score
- role/title score
- strengths
- required missing skills
- optional missing skills
- recommended actions
- recommendation refresh or saved recommendations

Architecture rule: identify service/presentation layer and avoid pushing business logic into templates.

## Task 2 — Remove location from final score

Change final scoring so location/mobility does not reduce the final fit score.

Required behavior:

- Final fit score should be composed from technical, experience, language, and role/title only.
- Existing `location_score` may remain stored/displayed only if needed, but it must not affect final fit score.
- Prefer replacing the visible `Localisation` score bar with a non-scored `Mobilité / contrat` note.
- Do not fake a 100% location score.
- Do not silently hide all location context. Users still need to know that the job is in France and may require mobility/visa/contract checks.

Suggested copy:

```text
Mobilité / contrat
Poste basé en France. Vérifiez la mobilité, le visa, l'alternance/PFE ou les conditions de télétravail avant de postuler.
```

Tests must prove location no longer changes the final score.

## Task 3 — Suppress noisy/foundational skills from missing/recommendation display

Create or update a service/presentation helper that filters noisy skills from user-facing missing/optional/recommendation lists.

Do not delete these skills from taxonomy or job materialization.

Baseline noisy/foundational list:

```text
JSON
XML
YAML
CSV
Markdown
HTTP
HTTPS
Agile
Scrum
Documentation
Technical Documentation only when generic/no evidence-specific
Office tools
Microsoft Office
Pack Office
```

Contextual implied coverage rule:

- Suppress `JSON` as missing/optional if candidate has any of:
  - JavaScript
  - TypeScript
  - Node.js
  - REST API / API REST / RESTful API
  - Frontend development
  - Backend development
  - Full-stack development
  - Django / Flask / FastAPI / Express / Spring / ASP.NET

Similar rule:

- Suppress `HTML`/`CSS` only if the job marks them optional and the candidate has stronger frontend skills, but do not overdo this. Keep `HTML5` and `CSS3` as strengths when present.
- Do not suppress real advanced/specific variants such as:
  - JSON Schema
  - JSON-LD
  - jq
  - OpenAPI
  - Swagger
  - XML Schema / XSD
  - XPath / XSLT

Required example:

For candidate strengths:

```text
JavaScript, TypeScript, REST API, Node.js
```

Job optional skills:

```text
JSON, Kubernetes, Jenkins, Nexus Repository, Ionic, Cypress, GitLab, Jira, Confluence
```

Displayed optional to strengthen must not include `JSON`.

## Task 4 — Remove redundant `À renforcer` card

Remove the redundant match detail card:

```text
À renforcer
Compétences obligatoires non détectées
```

The required missing skills section already communicates this. Do not leave an empty or vague red card.

If required skills are missing, the page should show:

- `Compétences requises manquantes` with the actual skills, e.g. `Angular`.
- `Actions recommandées` styled as priority/warning.

## Task 5 — Improve recommended actions

Move recommendation-action copy generation to service/presentation helper if not already there.

Required French copy:

When required missing skills exist:

```text
Actions recommandées
Priorité : ajoutez Angular à votre plan d'apprentissage.
Mettez à jour votre CV si vous avez déjà utilisé Angular.
```

When no required missing skills but optional skills exist:

```text
Actions recommandées
Votre profil couvre les compétences principales. Renforcez les compétences optionnelles pour améliorer votre score.
```

When match is strong:

```text
Actions recommandées
Votre profil est bien aligné avec cette offre. Vérifiez les conditions de mobilité/contrat puis postulez sur la source.
```

Styling:

- If required missing skills exist, use the same red/priority visual language as `Compétences requises manquantes`.
- If only optional skills are missing, use amber/neutral.
- If no meaningful gaps, use green/positive.

No English copy should remain in this area.

## Task 6 — Add refresh recommendations button

Add a visible button on the recommendations page/dashboard area:

```text
Actualiser mes recommandations
```

or:

```text
Recalculer les recommandations
```

Required behavior:

- POST-only.
- CSRF protected.
- Login required.
- View stays thin.
- View calls a recommendation service.
- Service recomputes from local PostgreSQL only.
- No France Travail provider call.
- No OpenRouter/LLM call.
- On success, redirect back with a success message.
- On error, redirect back with an error message and do not crash.

Implementation options:

- If existing recommendation generation is fast, call service synchronously.
- If existing app already has Celery infrastructure for this, enqueue task that calls service. Do not overbuild if not already needed.

Tests:

- GET to refresh endpoint is not allowed or redirects safely without mutation.
- Anonymous user cannot refresh.
- POST authenticated calls service.
- Button appears in template.

## Task 7 — Tests

Add/repair tests for:

- Location removed from final score.
- Mobility note exists but is non-scored.
- JSON is suppressed when implied by JavaScript/TypeScript/REST API/Node.js.
- Angular remains as required missing.
- No redundant `À renforcer / Compétences obligatoires non détectées` block.
- Actions recommended copy is French.
- Actions recommended styling changes based on required missing skills.
- Refresh recommendations button endpoint is POST-only and calls service/task.
- Public safety remains unchanged: no public/matchable zero-skill jobs if current test fixtures cover this.

## Task 8 — Verification

Run:

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test --settings=config.settings.local --parallel 1
npm run css:build
python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
git diff --check
```

Security greps:

```bash
grep -R "OpenRouterClient\|OPENROUTER\|run_llm\|client.chat\|_make_request" apps/*/views.py templates -n 2>/dev/null || true
grep -R "FranceTravailClient\|search_offers\|api.francetravail" apps/*/views.py templates -n 2>/dev/null || true
grep -R "file.url\|cv.file.url\|upload.file.url\|raw_text\|raw_response_text\|raw_response_json" templates apps -n 2>/dev/null || true
git diff -- . ':!.env' ':!.env.*' | grep -iE "sk-or-|Bearer [A-Za-z0-9_.-]{20,}|OPENROUTER_API_KEY=.*[^=]|FRANCE_TRAVAIL_CLIENT_SECRET=.*[^=]|EMAIL_HOST_PASSWORD=.*[^=]" || echo "OK: no obvious secrets in diff"
```

## Task 9 — Agent report

Create:

```text
docs/phases/phase_15g_matching_explanation_recommendation_ux_hardening/agent_report.md
```

Use the provided template.
