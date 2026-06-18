# Test Plan — Phase 14F

## Unit tests

### Config model

- default config has `limit_per_keyword=50`.
- default config has `max_total_per_run=1000`.
- default config has `nightly_max_total=2000`.
- default config has `enqueue_enrichment=True`.
- admin can override values.

### Broad preset

- includes developer/backend/frontend/mobile.
- includes data/BI.
- includes DevOps/cloud.
- includes cyber.
- includes QA.
- includes support/systems/network.
- includes DBA.
- includes ERP/CRM.
- includes project/product/BA.
- includes internship/apprenticeship.

### Ingestion service

Mock France Travail client.

- Fetches multiple keywords.
- Paginates when more pages exist.
- Stops at `limit_per_keyword`.
- Stops at `max_total`.
- Deduplicates repeated source job IDs across keywords.
- Saves RawJobRecord.
- Normalizes when enabled.
- Does not normalize when disabled.
- Records created/updated counts.
- Records errors without crashing entire run.

### Enrichment queueing

Mock enrichment task.

- Queues enrichment for every fetched active eligible IT job by default.
- Does not queue when config disables enrichment.
- Does not queue duplicate pending/success same hash.
- Respects enrichment limit per run.
- Non-IT obvious false positive is not queued or is marked skipped according to service decision.

### Expiry service

- Active old job not seen for configured days becomes inactive/stale.
- Recently seen job stays active.
- RawJobRecord is not deleted.
- Inactive jobs excluded from recommendation query.

### Command tests

- `sync_france_travail_it_jobs --dry-run` does not write data.
- `--limit-per-keyword 50` is honored, not reduced to 10.
- `--max-total 1000` is honored.
- `--config default` loads DB config.
- invalid preset fails clearly.

## Integration tests

- End-to-end mocked run: fetch raw jobs -> normalize -> queue enrichment -> create run log.
- Expiry command changes stale jobs to inactive.
- Recommendation query only sees active normalized jobs.

## Regression tests

- Existing `sync_france_travail_jobs` tests continue to pass.
- Phase 14D enrichment tests continue to pass.
- Phase 14E account/profile/privacy tests continue to pass.

## Required command suite

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test apps.jobs apps.llm apps.matching apps.recommendations --settings=config.settings.local
python manage.py test --settings=config.settings.local
```
