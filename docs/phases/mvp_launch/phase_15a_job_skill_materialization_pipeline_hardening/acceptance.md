# Phase 15A Acceptance Criteria

Accepted only if all pass:

## Functional
- Provider/raw skill JSON creates `NormalizedJobSkill`.
- Successful `JobEnrichment.validated_output_json` creates `NormalizedJobSkill`.
- `Skill` and `SkillAlias` matching works.
- Unknowns create/update `UnmatchedSkillCandidate`.
- Duplicates are avoided.
- Required beats optional.
- `SkillSource.ADMIN` rows are preserved.
- Jobs do not remain `skill_extraction_status=pending` after successful processing.
- Active enriched-success jobs without job skills decrease after backfill.
- Matching/recommendations continue using canonical `job_skills`.

## Architecture
- Materialization logic lives in services.
- Celery tasks call services only.
- Models do not call providers.
- Views/templates do not call LLM/provider logic.
- LLM output is extraction evidence, not scoring authority.
- No scoring formula change.
- No forbidden stack.
- No raw secrets/provider payloads/CV text exposure.

## Command
A bounded idempotent backfill command exists, with dry-run.

Suggested:
```bash
python manage.py materialize_job_skills --active-only --limit 200
```

## Tests
Full suite passes. Tests cover rule/provider materialization, LLM materialization, alias matching, unmatched creation, dedupe, required-over-optional, admin preservation, LLM success materialization trigger, sync/normalization path, backfill idempotency, and matching still using `NormalizedJobSkill`.

## Checks
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

## Safety greps
```bash
grep -R "file.url\|cv.file.url\|upload.file.url\|raw_text\|raw_request_json\|raw_response_text\|raw_response_json" templates apps -n 2>/dev/null || true
grep -R "<int:" apps templates config -n 2>/dev/null || true
grep -R "OpenRouterClient\|OPENROUTER\|client.chat\|_make_request" apps/*/views.py apps/*/admin.py templates -n 2>/dev/null || true
grep -R "FranceTravailClient\|search_offers\|api.francetravail" apps/*/views.py templates -n 2>/dev/null || true
git diff -- . ':!.env' ':!.env.*' | grep -iE "sk-or-|Bearer [A-Za-z0-9_.-]{20,}|OPENROUTER_API_KEY=.*[^=]|FRANCE_TRAVAIL_CLIENT_SECRET=.*[^=]|EMAIL_HOST_PASSWORD=.*[^=]" || echo "OK: no obvious secrets in diff"
```

## Not accepted if
- LLM JSON is read directly by templates as the primary skill source.
- Provider/LLM calls happen in views/templates.
- Matching score formula is changed.
- Raw secrets or raw provider/LLM/CV data are exposed.
- Tests rely on real OpenRouter.
- Jobs remain mostly pending after materialization/backfill.
