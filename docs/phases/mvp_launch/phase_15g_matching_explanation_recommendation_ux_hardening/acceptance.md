# Phase 15G Acceptance Criteria

## Product acceptance

- Location is removed from final match score.
- A non-scored mobility/contract note remains visible where useful.
- `JSON` does not appear as missing/optional to strengthen when candidate has JavaScript/TypeScript/REST API/Node.js or equivalent stronger skills.
- True required missing skills such as `Angular` still appear.
- Redundant `À renforcer / Compétences obligatoires non détectées` card is removed.
- `Actions recommandées` is French.
- `Actions recommandées` uses priority/red styling when required skills are missing.
- Refresh recommendations button exists and is understandable.

## Architecture acceptance

- Views stay thin.
- Business logic is in services/presentation helpers.
- Templates do not contain matching logic.
- No OpenRouter/LLM from views/templates/models/admin display.
- No France Travail API from public search/match/recommendation views.
- No forbidden stack.
- No broad UI redesign.
- No fake profile skill insertion.
- No deletion of taxonomy skills solely to hide noisy display.

## Test acceptance

Required tests:

- Final score unaffected by location.
- Mobility note displayed or prepared separately.
- Noisy skill filter hides JSON when implied.
- Noisy skill filter keeps advanced JSON-specific skills.
- Required missing `Angular` still shown.
- Removed redundant card is absent in rendered match page.
- Recommended actions are French and priority/red for required gaps.
- Refresh endpoint requires authentication.
- Refresh endpoint is POST-only or does not mutate on GET.
- Refresh endpoint calls service/task.

## Command acceptance

Must pass:

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test --settings=config.settings.local --parallel 1
npm run css:build
python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
git diff --check
```

Security greps must not show real leaks or forbidden calls.

## Commit acceptance

Commit only in-scope files and phase docs.

Do not commit:

```text
.env
agent_report.md at project root
docs/reports/
var/
staticfiles/
__pycache__/
.pytest_cache/
```
