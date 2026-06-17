# Phase 14D Tasks

## TTA-14D-001 — Add JobEnrichment model

Create a dedicated `JobEnrichment` model with:

- status field: pending, processing, success, failed, validation_error, skipped
- raw LLM response fields
- validated output field
- validation errors field
- token/cost fields
- attempt/retry fields
- timestamps
- one-to-one relation to NormalizedJob

Create migration.

## TTA-14D-002 — Add feature flags/settings

Add settings and `.env.example` entries:

- `JOB_ENRICHMENT_ENABLED`
- `JOB_RECOMMENDATIONS_USE_ENRICHED_DATA`
- `JOB_ENRICHMENT_MODEL`
- `JOB_ENRICHMENT_DAILY_LIMIT`
- `JOB_ENRICHMENT_MAX_CHARS`
- `JOB_ENRICHMENT_MAX_RETRIES`

Defaults must be safe: enrichment disabled, recommendations not using enriched data.

## TTA-14D-003 — Build LLM enrichment service

Create service layer only:

- `apps/llm/services/job_enrichment.py` or equivalent
- builds prompt
- calls existing OpenRouter/LLM client abstraction
- parses JSON
- retries once on JSON parse failure at service/task level
- returns structured output and usage metadata

No view calls.

## TTA-14D-004 — Validate enrichment output

Create validation service/function that:

- validates schema
- validates allowed enum values
- validates evidence exists in original job text
- rejects skills without evidence
- filters soft skills
- separates required and optional skills
- returns validated output + validation errors

## TTA-14D-005 — Qualify jobs for enrichment

Create `job_qualifies_for_enrichment(job)` service.

Must consider:

- active job
- France job
- recent or active
- broad IT signal from title/ROME/description/deterministic fallback
- weak or generic deterministic extraction OR explicit force mode
- payload hash not already successfully enriched
- daily limit not exceeded

## TTA-14D-006 — Celery task

Add task:

- loads job
- creates/updates JobEnrichment status pending/processing/success/failed/validation_error/skipped
- calls enrichment service
- stores raw LLM response and validated output separately
- records token/cost usage
- retries safely

Task must call services only.

## TTA-14D-007 — Management command

Add command:

```bash
python manage.py enrich_jobs --limit 50 --only-qualifying --dry-run
python manage.py enrich_jobs --limit 50 --only-qualifying
python manage.py enrich_jobs --limit 5 --force --sync
```

Requirements:

- dry-run shows what would be processed
- normal mode enqueues Celery tasks
- sync mode is allowed only for local/admin testing, not views
- respects daily limit unless explicit force is used
- prints counts, not secrets

## TTA-14D-008 — Matching uses enrichment behind feature flag

When `JOB_RECOMMENDATIONS_USE_ENRICHED_DATA=True` and enrichment success exists:

- use enriched required/optional skills for scoring
- still deterministic score
- still compare candidate skills against normalized skill names

When flag false or no success enrichment:

- use existing deterministic fallback

## TTA-14D-009 — UI copy polish

Update public/user templates:

- no internal IT/non-IT labels
- no raw risk flags
- no parser wording
- hide empty stack blocks on public job cards
- show friendly status/copy when analysis is limited

## TTA-14D-010 — Tests

Add tests for:

- model statuses
- raw response stored separately from validated output
- feature flags
- token/cost logging
- evidence validation
- no LLM calls in views
- Ciril Java job enrichment
- photography seller job not recommended
- weak Web Developer job analysis limited
- recommendations using enriched data only when feature flag enabled

## TTA-14D-011 — Agent report

Fill `agent_report.md` using the template. Verdict must be FAIL or BLOCKED_HUMAN_VISUAL_SIGNOFF.
