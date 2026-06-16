# Codex Verification Prompt — Phase 14A Local MVP Stabilization

You are the strict reviewer and repair agent for TuniTech Abroad Phase 14A.

Run this after Gemini/Antigravity completes `docs/phases/phase_14a_local_mvp_stabilization/prompt.md`.

## Mission

Verify the agent's work independently. Do not trust `agent_report.md`. Re-run checks. Inspect code. Repair only defects within Phase 14A scope. Do not start a new phase.

## Read first

```text
AGENTS.md
docs/phases/phase_14a_local_mvp_stabilization/README.md
docs/phases/phase_14a_local_mvp_stabilization/scope.md
docs/phases/phase_14a_local_mvp_stabilization/boundaries.md
docs/phases/phase_14a_local_mvp_stabilization/tasks.md
docs/phases/phase_14a_local_mvp_stabilization/acceptance.md
docs/phases/phase_14a_local_mvp_stabilization/test_plan.md
docs/phases/phase_14a_local_mvp_stabilization/real_validation.md
docs/phases/phase_14a_local_mvp_stabilization/agent_report.md
```

Also inspect relevant planning docs under `docs/planning/`.

## Hard verification rules

- Do not mark PASS unless PostgreSQL-backed migrate and full `manage.py test` actually run and pass.
- Do not mark PASS if `Found 0 test(s)` appears.
- Do not mark PASS if real OpenRouter validation did not run successfully.
- Do not mark PASS if real France Travail validation did not run successfully.
- If external credentials/API are unavailable, report BLOCKED_EXTERNAL_VALIDATION, not PASS.
- If DB is unavailable, report BLOCKED_DB.
- If tests fail, repair root cause or report FAIL.
- Do not commit, merge, or push.
- Do not print secrets.

## Verification commands

```bash
cd ~/Projects/tunitech-abroad
source .venv/bin/activate
git status --short --branch
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py migrate --settings=config.settings.local
python manage.py shell --settings=config.settings.local -c "from django.db import connection; connection.ensure_connection(); print('DB_VENDOR=', connection.vendor)"
python manage.py test --settings=config.settings.local
```

If DB/Redis blocked, make one safe attempt:

```bash
docker compose up -d postgres redis || docker compose up -d || true
```

Then rerun failed DB/cache checks.

## Static architecture checks

```bash
grep -R "OpenRouter\|openrouter" apps --exclude-dir="__pycache__" -n || true
grep -R "FranceTravail\|france_travail" apps --exclude-dir="__pycache__" -n || true
grep -R "CVUpload.all_objects" apps --exclude-dir="__pycache__" -n || true
grep -R "recommendations/" templates apps --exclude-dir="__pycache__" -n || true
find . -path ./.venv -prune -o -type d -name "__pycache__" -print
find . -path ./.venv -prune -o -name "*.pyc" -print
find . -maxdepth 4 -name "*.sqlite3" -print
find . -maxdepth 4 -name "celerybeat-schedule*" -print
```

Interpret results; valid service-layer references are allowed.

## Review checklist

### CV parsing/profile

Verify:

- Deterministic extractor handles email, phone, name, location, LinkedIn, GitHub, portfolio/website.
- URL normalization handles missing scheme.
- PDF text extraction test exists.
- `CVParsedData` stores extracted values.
- CandidateProfile prefill only fills empty fields.
- Non-empty profile identity is not silently overwritten.
- Profile completeness recalculates.
- CV parse warnings are stored and visible enough for dashboard/CV page.

### Recommendations

Verify:

- Usable profile + active jobs creates stored recommendations.
- Incomplete profile blocked state is clear.
- No active jobs blocked state is clear.
- Dashboard reads stored recommendations.
- No heavy sync generation in template.
- No LLM scoring.
- No duplicate recommendations.

### Quick match

Verify:

- Different skill payload generates fresh result.
- No stale server-side reuse.
- No LLM call.
- No CV stored.
- Template has reset behavior for HTMX/back-forward cache.

### Error pages/routes

Verify:

- `/dashboard/recommendations/` is canonical.
- `/recommendations/` safe behavior exists.
- `DEBUG=False` 404 test exists and passes.
- Error templates expose no URLconf, traceback, settings, env, or secret names.

### LLM

Verify:

- OpenRouter calls isolated in `apps/llm/services` or equivalent service layer.
- Rate/cost/cache/logging behavior exists or code reports missing features honestly.
- Real smoke command/test exists and was run if credentials present.
- Failure does not break CV parsing or match page.
- LLM cannot change fit score.

### France Travail

Verify:

- Real small sync command exists or equivalent service smoke exists.
- Max 10 offer limit enforced.
- Raw records saved before normalization.
- Public search never calls FranceTravailClient.
- Credentials not printed.

## Repair authority

You may repair defects in this scope only.

Do not:

- Add unrelated features.
- Rewrite the project stack.
- Add SPA/frontend framework.
- Change public product scope.
- Commit or push.

## Final output

Update or create:

```text
docs/phases/phase_14a_local_mvp_stabilization/codex_verification_report.md
```

Include:

- Final classification.
- Commands run.
- Test results.
- External validation result.
- Defects found and fixed.
- Remaining blockers.
- Architecture violations found.

Allowed classifications:

```text
PASS
FAIL
BLOCKED_DB
BLOCKED_REDIS
BLOCKED_REAL_LLM
BLOCKED_REAL_FRANCE_TRAVAIL
BLOCKED_EXTERNAL_VALIDATION
```

`PASS` requires all local acceptance plus real OpenRouter plus real France Travail validation.
