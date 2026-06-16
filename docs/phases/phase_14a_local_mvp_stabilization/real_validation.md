# Real External Validation

This phase requires real external validation, but only in controlled service/command paths.

Do not print secret values.

## Real OpenRouter validation

### Preconditions

```bash
python manage.py shell --settings=config.settings.local -c "from django.conf import settings; print('LLM_ENABLED=', getattr(settings, 'LLM_ENABLED', None)); print('HAS_OPENROUTER_API_KEY=', bool(getattr(settings, 'OPENROUTER_API_KEY', '')))"
```

If key is missing or LLM disabled, report:

```text
BLOCKED_REAL_LLM: OpenRouter credentials/config not available
```

### Required implementation behavior

The codebase must provide either:

- a safe management command, or
- a documented shell command, or
- a service-level integration test guarded by an env flag

that makes at most 2 real OpenRouter calls.

Suggested command name if missing:

```bash
python manage.py llm_smoke_test --kind cv_extraction --settings=config.settings.local
```

Minimum real test payload:

```text
Aymen Ben Salah
Junior Full Stack Developer
Tunis, Tunisia | +216 55 123 456 | aymen.bensalah.test@example.com
LinkedIn: linkedin.com/in/aymen-bensalah-test | GitHub: github.com/aymen-bensalah-test | Portfolio: aymen-dev.example.com
Skills: JavaScript, React, Node.js, Django, PostgreSQL, Docker
Experience: Junior Web Developer Intern, DigitalBridge Labs, March 2025 - August 2025
Education: Licence en Informatique, Private University of Tunis
Languages: French B2, English B2
```

Required assertions:

- Response parsed as structured data or validated text according to existing service contract.
- Candidate identity fields are present.
- Skills list is present.
- Experience/project/education/language keys exist if schema supports them.
- Usage log count increases or real run is recorded.
- No secret values in output.

## Real France Travail validation

### Preconditions

```bash
python manage.py shell --settings=config.settings.local -c "from django.conf import settings; print('HAS_FT_CLIENT_ID=', bool(getattr(settings, 'FRANCE_TRAVAIL_CLIENT_ID', ''))); print('HAS_FT_CLIENT_SECRET=', bool(getattr(settings, 'FRANCE_TRAVAIL_CLIENT_SECRET', '')))"
```

If credentials are missing, report:

```text
BLOCKED_REAL_FRANCE_TRAVAIL: credentials not available
```

### Required implementation behavior

The codebase must provide a small real sync command. Suggested command name if missing:

```bash
python manage.py sync_france_travail_jobs --limit 10 --settings=config.settings.local
```

Equivalent existing command is acceptable if it satisfies all rules.

Required rules:

- Max 10 offers.
- No endless pagination.
- Creates/updates `IngestionRun`.
- Creates/updates `RawJobRecord`.
- Normalizes into `NormalizedJob` synchronously or enqueues normalization then runs it in test/smoke mode.
- Public `/jobs/` search remains local PostgreSQL only.
- No credential values printed.

Required post-check:

```bash
python manage.py shell --settings=config.settings.local -c "from apps.jobs.models import RawJobRecord, NormalizedJob; print('RAW=', RawJobRecord.objects.count()); print('NORMALIZED=', NormalizedJob.objects.count()); print('ACTIVE=', NormalizedJob.objects.filter(status='active').count())"
```

## Classification of external validation results

- `PASS`: real LLM and real France Travail validation both completed successfully.
- `BLOCKED_REAL_LLM`: LLM code may pass mocked tests, but real OpenRouter validation did not run due to missing/unavailable config/API.
- `BLOCKED_REAL_FRANCE_TRAVAIL`: ingestion code may pass mocked tests, but real France Travail validation did not run due to missing/unavailable config/API.
- `FAIL`: credentials are present but validation fails due to code bug.
