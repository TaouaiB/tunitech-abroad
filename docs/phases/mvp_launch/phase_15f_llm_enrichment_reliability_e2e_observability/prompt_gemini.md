# Gemini / Antigravity Prompt — Phase 15F

You are implementing Phase 15F for TuniTech Abroad.

## Role

Act as a strict senior Django engineer. Work automatically through all tickets in this phase, but do not start the next phase.

## Mission

Harden the LLM enrichment pipeline after a real 100-job E2E test showed:

```text
latest 100 enrichment rows:
success = 64
skipped = 34
failed = 2
reached provider = 72
tokens=0 pre-skips = 28
many skipped rows had status_reason = provider_circuit_open
public safety passed with PUBLIC_ZERO=0 and MATCHABLE_ZERO=0
```

The public pipeline is safe, but LLM reliability and observability need hardening.

## Mandatory rules

- Use Django, Django ORM, PostgreSQL, Redis/Celery patterns already in the app.
- Do not use React, Next.js, FastAPI, MongoDB, SQLAlchemy, or SPA architecture.
- Do not call OpenRouter from views, templates, models, or admin display methods.
- Do not call France Travail live from public search.
- Views must stay thin.
- Business logic goes in services.
- Celery tasks call services only.
- Models store data only.
- No real secrets in docs/logs/tests.
- `.env` must not be touched except reading settings normally.
- Do not change matching score logic.
- Do not redesign UI.
- Do not fake skills.
- Do not bulk-promote all unmatched skill candidates.

## Required implementation

Implement the tickets in `tasks.md`:

1. Inspect current LLM flow.
2. Add explicit status reason constants.
3. Harden JSON parsing.
4. Retry invalid JSON once.
5. Fix circuit breaker so invalid JSON does not open provider circuit.
6. Clarify skipped semantics.
7. Add local-only force-provider-call mode.
8. Add one local E2E pipeline command.
9. Add tests.
10. Run verification.
11. Prepare an agent report.

## Important behavior

Invalid JSON means the provider responded but the output was malformed. It must not be treated as provider unavailable.

Provider circuit breaker should open only for:

```text
network error
timeout
HTTP 429
HTTP 401/403 config/auth problem
HTTP 5xx
quota/credits unavailable
provider unavailable
```

Invalid JSON, schema validation errors, non-IT results, and empty skill output are row-level outcomes and must not open the provider circuit.

## E2E command requirement

Add one management command, recommended:

```bash
python manage.py run_llm_e2e_pipeline
```

It must be able to run:

```bash
python manage.py run_llm_e2e_pipeline   --preset broad_it   --limit-per-keyword 10   --max-total 100   --max-pages-per-keyword 2   --force-llm-count 100   --force-provider-call   --min-llm-success 95   --apply   --settings=config.settings.local
```

The command must print truthful counters and fail hard if the configured LLM target is not met. It must not print PASS if the LLM target failed.

## Tests

Tests must mock provider calls. Do not call OpenRouter in automated tests.

Add tests covering:

- JSON code fence parsing;
- JSON with leading/trailing prose;
- invalid JSON retry success;
- invalid JSON retry failure;
- invalid JSON does not open circuit;
- provider outage opens circuit;
- skipped reason consistency;
- E2E command counters/failures with mocked provider;
- public zero/matchable zero remains safe.

## Verification commands

Run:

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test --settings=config.settings.local --parallel 1
npm run css:build
python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
git diff --check
```

Also run any targeted tests you create.

## Report

Fill `agent_report.md` using the template. Include:

- files changed;
- architecture notes;
- invalid JSON behavior;
- circuit breaker behavior;
- E2E command usage;
- test results;
- any remaining risk.

Do not commit or push unless explicitly asked.
