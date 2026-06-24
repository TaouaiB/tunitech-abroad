# Phase 15F Test Plan

## Unit tests

### JSON parser

Test cases:

```text
valid raw JSON object
JSON inside markdown code fences
JSON with prose before and after
JSON with whitespace/newlines
empty string
non-object JSON list
truncated JSON
malformed JSON with trailing comma
```

Expected:

- extractable objects parse;
- unsafe malformed output is rejected;
- no silent fake data.

### Invalid JSON retry

Mock provider sequence:

```text
first response: invalid JSON
second response: valid JSON
```

Expected:

```text
status = success
status_reason = invalid_json_retry_success
attempt_count incremented
circuit not opened
```

Mock provider sequence:

```text
first response: invalid JSON
second response: invalid JSON
```

Expected:

```text
status = failed or validation_error
status_reason = invalid_json_retry_failed
circuit not opened
```

### Circuit breaker

Provider timeout/network/429/5xx/auth errors should be able to open circuit.

Invalid JSON/schema validation/non-IT/empty skills must not open circuit.

### Skipped consistency

Assert:

```text
provider_circuit_open => tokens = 0
skipped + tokens > 0 => reason is not provider_circuit_open
skipped rows always have status_reason
```

## Command tests

Use mocked services/provider. Do not call OpenRouter in tests.

Test:

- command reports selected/fetched/normalized/enriched/materialized/public counters;
- command fails when `--min-llm-success` is not met;
- command fails when public zero/matchable zero is nonzero;
- command blocks `--force-provider-call` outside local/debug mode;
- command does not print secrets.

## Integration smoke locally

Run small real-provider canary manually:

```bash
python manage.py run_llm_e2e_pipeline   --preset broad_it   --limit-per-keyword 2   --max-total 10   --force-llm-count 10   --force-provider-call   --min-llm-success 8   --apply   --settings=config.settings.local
```

Then check latest enrichment status:

```bash
python manage.py shell --settings=config.settings.local <<'PY'
from django.db.models import Count
from apps.llm.models import JobEnrichment

qs = JobEnrichment.objects.order_by('-created_at')[:50]
ids = [e.id for e in qs]
for row in JobEnrichment.objects.filter(id__in=ids).values('status', 'status_reason').annotate(c=Count('id')).order_by('status', 'status_reason'):
    print(row)
PY
```

## Regression checks

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test --settings=config.settings.local --parallel 1
npm run css:build
python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
git diff --check
```

Security grep:

```bash
git diff -- . ':!.env' ':!.env.*' | grep -iE "sk-or-|Bearer [A-Za-z0-9_.-]{20,}|OPENROUTER_API_KEY=.*[^=]|FRANCE_TRAVAIL_CLIENT_SECRET=.*[^=]|EMAIL_HOST_PASSWORD=.*[^=]" || echo "OK: no obvious secrets in diff"
```
