# Phase 14F Agent Report — Automated France Travail IT Ingestion

## Verdict

Choose one only:

```text
FAIL
BLOCKED_HUMAN_VISUAL_SIGNOFF
```

Never write PASS before Baha manual Chrome/admin signoff.

## Summary

- What was changed:
- What was intentionally not changed:

## Files changed

List files created/modified.

## Config/admin proof

- `JobIngestionConfig` created: yes/no
- `JobIngestionRun` created: yes/no
- Admin registered: yes/no
- Default `limit_per_keyword`: 
- Default `max_total_per_run`: 
- Default `nightly_max_total`: 
- Enrichment default enabled for fetched IT jobs: yes/no

## Command proof

- New command:
- Example dry run output:
- Example small real/mock run output:
- No hidden cap of 10: yes/no
- Pagination implemented: yes/no
- Deduplication implemented: yes/no

## Broad IT preset proof

List covered families and sample keywords.

## Enrichment proof

- Every fetched active eligible IT job queues enrichment by default: yes/no
- Existing success same hash skipped: yes/no
- Pending duplicate skipped: yes/no
- Enrichment can be disabled: yes/no
- LLM not in views: yes/no

## Expiry proof

- Expiry service/command:
- Old job becomes inactive/stale: yes/no
- Raw record kept: yes/no
- Public/recommendation query excludes inactive jobs: yes/no

## Admin/manual control proof

- Admin can adjust max total: yes/no
- Admin can adjust frequency: yes/no
- Admin can disable sync: yes/no
- Admin can disable enrichment: yes/no
- Admin can trigger/manual run safely: yes/no

## Commands run

Paste command and result:

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test apps.jobs apps.llm apps.matching apps.recommendations --settings=config.settings.local
python manage.py test --settings=config.settings.local
git diff --check
```

## Security/regression checks

- Secrets check:
- No live France Travail in user paths:
- No LLM in views:
- Raw private CV data check:
- Hidden cap check:
- Frontend stack check:

## Browser/admin/manual status

- Agent/headless tested: yes/no
- Baha manual Chrome/admin signoff: pending

## Remaining risks

Be honest.
