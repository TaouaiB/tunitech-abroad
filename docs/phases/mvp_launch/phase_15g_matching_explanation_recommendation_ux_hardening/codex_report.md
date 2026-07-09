# Phase 15G Codex Verification Report

## Verdict

```text
REPAIRED_PASS
```

## What I reviewed

- `AGENTS.md`
- Phase 15G task, scoring, noisy-skill, refresh, acceptance, and agent report files
- Matching scoring service, match result persistence, match views, and match detail template
- Recommendation dashboard view, recommendation service/query flow, refresh view/URL, and templates
- Matching and recommendation tests
- Current git diff and untracked phase/report artifacts

## Architecture compliance

```text
No forbidden stack introduced: YES
No OpenRouter from views/templates/models/admin display: YES
No France Travail live from public search/match/recommendation views: YES
Views thin: YES
Services own business logic: YES
No matching overbuild: YES
No UI redesign: YES
No secrets exposed: YES
```

## Functional verification

- Location removed from final score: YES
- Mobility note non-scored: YES
- JSON noisy-skill suppression: YES
- Advanced JSON-specific skills preserved: YES
- Required missing Angular still shown: YES
- Redundant `À renforcer` / `Compétences obligatoires non détectées` block removed: YES
- Actions recommandées French and priority-styled: YES
- Refresh recommendation button/endpoint: YES

## Tests run

```text
git status --short --branch
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test apps.matching apps.recommendations --settings=config.settings.local --parallel 1
python -m py_compile apps/matching/tests.py apps/matching/services/scoring.py apps/recommendations/views.py
python manage.py test --settings=config.settings.local --parallel 1
npm run css:build
python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
git diff --check
python manage.py test apps.matching.tests.Phase15GHardeningTests apps.matching.tests.Phase15GRecommendationsViewTests --settings=config.settings.local --parallel 1
grep -R "OpenRouterClient\|OPENROUTER\|run_llm\|client.chat\|_make_request" apps/*/views.py templates -n 2>/dev/null || true
grep -R "FranceTravailClient\|search_offers\|api.francetravail" apps/*/views.py templates -n 2>/dev/null || true
grep -R "file.url\|cv.file.url\|upload.file.url\|raw_text\|raw_response_text\|raw_response_json" templates apps -n 2>/dev/null || true
git diff -- . ':!.env' ':!.env.*' | grep -iE "sk-or-|Bearer [A-Za-z0-9_.-]{20,}|OPENROUTER_API_KEY=.*[^=]|FRANCE_TRAVAIL_CLIENT_SECRET=.*[^=]|EMAIL_HOST_PASSWORD=.*[^=]" || echo "OK: no obvious secrets in diff"
```

Results:

```text
System check identified no issues (0 silenced).
No changes detected
Focused matching/recommendations suite: Ran 112 tests, OK
Full suite: Ran 540 tests, OK
CSS build: Done in 870ms
collectstatic dry run: 2 static files copied, 134 unmodified
git diff --check: PASS after trailing-whitespace repair
Focused Phase 15G suite: Ran 8 tests, OK
OpenRouter/France Travail view/template greps: no matches
Secret grep: OK: no obvious secrets in diff
CV/privacy grep: matched existing services/tests/admin exclusions and model fields; no Phase 15G template leak found
```

## Repairs made by Codex

- Removed unreachable duplicate scoring code and trailing whitespace.
- Fixed the recommendation dashboard header markup after adding the refresh form.
- Renamed the match-detail risk card heading from `À renforcer` to `Points de vigilance` and kept `missing_required_skills` out of human risk labels so the redundant required-gap card text does not reappear.
- Expanded Phase 15G tests to cover mobility note/no scored location bar, JSON suppression with `JSON Schema` preserved, Angular required gap display, French priority actions, red priority styling, POST-only/authenticated refresh behavior, service delegation, and CSRF refresh button rendering.

## Remaining concerns

- The worktree contains pre-existing untracked artifacts outside my repair scope, including root `agent_report.md`, `docs/reports/`, `var/`, and the Phase 15G package files. I did not remove or reset them.
- `npm run css:build` reports the standard Browserslist `caniuse-lite is outdated` notice, but the build completed successfully.
- The broad CV/privacy grep intentionally matches existing service/model/test/admin references to raw fields; I found no Phase 15G UI leak or new privacy exposure.

## Commit recommendation

```text
APPROVE_COMMIT
```
