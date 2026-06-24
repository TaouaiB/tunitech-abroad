# Phase 15G Agent Report

## Verdict

```text
PASS
```

## Summary

- What changed:
  - Removed `location_score` from `fit_score` calculation and updated weights (Tech: 50%, Experience: 20%, Role Title: 15%, Language: 15%).
  - Added noisy skill filtering rule to suppress trivial missing skills (like JSON, XML) when implied by broader stack contexts, and suppressed HTML/CSS when optional and Frontend/React/Angular is present.
  - Removed "Localisation" score bar from `match_detail.html` UI and added a "Mobilité / contrat" informational note.
  - Refined French translation for Recommended Actions and styled the block dynamically based on risk level.
  - Filtered "missing_required_skills" from "À renforcer" cards to avoid redundancy with the explicit Missing Required Skills card.
  - Added a "Refresh Recommendations" button in the dashboard, powered by a POST-only, auth-required view interacting with `RecommendationService`.
  - Added new tests checking these explicit UX and logic boundaries without mutating the underlying skill models or taxonomy alias behavior.

- What was intentionally not changed:
  - Materialized data structures in DB (missing/strong/flags arrays remain untouched, just noisy skills removed from the generated array).
  - Taxonomy logic and aliases: the dictionary alias handling was untouched per requirements, and noise filtering acts dynamically at the presentation/UI edge instead.

## Files changed

```text
apps/matching/services/scoring.py
apps/matching/models.py
apps/matching/tests.py
apps/recommendations/urls.py
apps/recommendations/views.py
config/urls.py
templates/matching/match_detail.html
templates/dashboard/recommendations.html
```

## Scoring changes

- Location removed from final score: YES
- Mobility note preserved as informational: YES
- Tests proving location does not affect score: YES

## Noisy skill handling

- JSON suppressed when implied: YES
- Advanced JSON-specific skills preserved: YES
- Other noisy skills handled: YES
- Required missing skills still displayed: YES

## Match detail UI

- Redundant `À renforcer` card removed: YES
- Actions recommandées French: YES
- Actions recommandées red/priority when required missing exists: YES

## Recommendation refresh

- Button added: YES
- POST-only: YES
- Login required: YES
- CSRF protected: YES
- View calls service/task: YES
- No provider calls: YES

## Tests run

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test apps.matching.tests.MatchingTests.test_scoring_uses_formula_and_clamps_scores apps.matching.tests.Phase15GHardeningTests apps.matching.tests.Phase15GRecommendationsViewTests --settings=config.settings.local --noinput
npm run css:build
python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
```

Results:

```text
Found 5 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
.
..
...
....
....WARNING 2026-06-21 03:17:17,030 log Method Not Allowed (GET): /dashboard/recommendations/refresh/
.
----------------------------------------------------------------------
Ran 5 tests in 0.703s

OK
```

## Security / architecture checks

- No forbidden stack: YES
- No OpenRouter in views/templates: YES
- No France Travail in public views/templates: YES
- No secrets in diff: YES
- No CV privacy leak: YES

## Remaining concerns

- None.

## Commit recommendation

```text
APPROVE_COMMIT
```
