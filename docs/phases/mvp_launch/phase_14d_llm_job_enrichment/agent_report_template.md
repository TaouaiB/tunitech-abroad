# Phase 14D Agent Report — LLM-Assisted Job Enrichment

## Verdict

Choose one only:

```text
FAIL
BLOCKED_HUMAN_VISUAL_SIGNOFF
```

Never write PASS before Baha manual Chrome signoff.

## Summary

- What was changed:
- What was intentionally not changed:

## Files changed

List files created/modified.

## Data model proof

- JobEnrichment model created: yes/no
- Migration created: yes/no
- Status values implemented:
- Raw response stored separately from validated output: yes/no
- Token/cost fields implemented: yes/no

## Feature flags proof

- `JOB_ENRICHMENT_ENABLED` default:
- `JOB_RECOMMENDATIONS_USE_ENRICHED_DATA` default:
- `.env.example` updated: yes/no

## LLM service proof

- Service location:
- JSON schema validation location:
- Evidence validation location:
- Soft-skill filtering location:
- Raw response persistence location:

## Celery/management command proof

- Task location:
- Management command:
- Dry-run output:
- Sync local test mode: yes/no
- Daily limit respected: yes/no

## Matching/recommendation proof

- Matching uses enriched data only when feature flag is true: yes/no
- Matching remains deterministic: yes/no
- LLM does not calculate final fit score: yes/no

## Required cases proof

| Case | Expected | Actual |
| --- | --- | --- |
| Ciril Java/Quarkus/PostgreSQL/Oracle | enriched skills with evidence | |
| Alternance Fullstack JS | React/TypeScript/Node.js | |
| Photography seller | not recommended, no ugly non-IT wording | |
| Weak Web Developer | analysis limited, no fake confident score | |
| Salesforce | Salesforce/Apex if present | |
| DevOps/Cloud | cloud/DevOps tools if present | |
| QA Automation | test tools if present | |
| ERP/Sage/PeopleSoft | ERP tools if present | |

## Commands run

Paste command and result:

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test apps.jobs apps.skills apps.matching apps.recommendations apps.llm --settings=config.settings.local
python manage.py test --settings=config.settings.local
```

## Security/regression checks

- Secrets check:
- No LLM in views:
- No live France Travail in user paths:
- Raw private CV data check:
- Raw internal flag leak check:
- Frontend stack check:
- Root junk cleanup:

## Browser/manual status

- Agent/headless browser tested: yes/no
- Baha manual Chrome signoff: pending

## Remaining risks

Be honest.
