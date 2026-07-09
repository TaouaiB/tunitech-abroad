# Codex Verification Prompt — Phase 15F

You are verifying Phase 15F for TuniTech Abroad.

Start from the current branch after Gemini/agent implementation. Your job is to inspect, repair in-scope issues, and verify. Do not start the next phase.

## Mission

Strictly verify that the LLM enrichment pipeline is hardened and observable.

The previous 100-job local E2E test produced:

```text
success = 64
skipped = 34
failed = 2
reached provider = 72
tokens=0 pre-skips = 28
many skipped rows had status_reason = provider_circuit_open
PUBLIC_ZERO = 0
MATCHABLE_ZERO = 0
```

Phase 15F must fix the LLM reliability/observability issues without changing the public product architecture.

## Architecture rules

- Django only.
- Django ORM only.
- No React/Next/FastAPI/MongoDB/SQLAlchemy.
- No OpenRouter calls from views/templates/models/admin display.
- No France Travail live calls from public search.
- Services own business logic.
- Celery tasks call services only.
- Public URLs remain UUID-based.
- CV privacy untouched.
- No real secrets printed or committed.

## What to verify

### Invalid JSON handling

Verify:

- malformed JSON is detected;
- markdown-wrapped JSON can be parsed safely;
- leading/trailing prose can be parsed safely when a JSON object is extractable;
- invalid JSON retries once;
- retry success becomes success;
- retry failure becomes failed or validation_error with clear reason;
- raw output is stored internally but not exposed publicly.

### Circuit breaker behavior

Verify:

- invalid JSON does not open provider circuit;
- schema validation failure does not open provider circuit;
- non-IT/empty skills does not open provider circuit;
- timeout/network/429/5xx/auth/quota errors can open provider circuit;
- `provider_circuit_open` rows have tokens = 0.

### Skipped reason clarity

Verify:

- skipped rows have actionable `status_reason` values;
- skipped rows with tokens > 0 do not use `provider_circuit_open`;
- skipped rows with tokens = 0 explain whether they were budget/circuit/duplicate/local eligibility skips.

### E2E command

Verify one command exists for local E2E testing.

It must:

- ingest from France Travail;
- normalize;
- force N LLM provider calls when local `--force-provider-call` is set;
- materialize LLM skills;
- run cleanup/reclassify;
- print truthful counters;
- fail if configured LLM success/provider-call target is not met;
- fail if `PUBLIC_ZERO` or `MATCHABLE_ZERO` are nonzero;
- not print secrets.

### Tests

Run the full suite and targeted LLM tests.

Commands:

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test --settings=config.settings.local --parallel 1
npm run css:build
python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
git diff --check
```

Run targeted tests, for example:

```bash
python manage.py test apps.llm apps.jobs.tests.test_15f_llm_e2e --settings=config.settings.local --parallel 1
```

Adjust module names to actual test files.

## Repair policy

You may fix in-scope issues yourself.

Do not block on small fixable issues.

Block only for:

- architecture violation;
- provider call from views/templates/models;
- real secrets exposed;
- public search calls external API;
- matching formula changed without approval;
- UI redesign;
- tests still failing after repair;
- migration introduced without clear need;
- LLM E2E command lies about pass/fail.

## Required report

Create/update `docs/phases/phase_15f_llm_enrichment_reliability_e2e_observability/codex_report.md`.

Use `codex_report_template.md`.

Verdict options:

```text
PASS
REPAIRED_PASS
BLOCKED
FAIL
```

PASS only if all acceptance criteria are met.
