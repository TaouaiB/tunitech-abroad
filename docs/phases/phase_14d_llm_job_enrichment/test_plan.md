# Phase 14D Test Plan

## Unit tests

### JobEnrichment model

- default status is pending
- status choices include pending, processing, success, failed, validation_error, skipped
- raw response fields can be stored separately from validated output
- token/cost fields default safely
- one job has at most one enrichment row

### LLM schema validation

- valid response passes
- invalid JSON fails gracefully
- missing evidence skill rejected
- fake evidence skill rejected
- soft skills rejected
- invalid enum rejected
- required/optional arrays normalized

### Feature flags

- `JOB_ENRICHMENT_ENABLED=False` prevents task execution or marks skipped
- `JOB_RECOMMENDATIONS_USE_ENRICHED_DATA=False` keeps deterministic fallback
- `JOB_RECOMMENDATIONS_USE_ENRICHED_DATA=True` uses successful enrichment

### Cost tracking

- mocked LLM usage metadata is persisted
- missing usage metadata does not crash
- daily limit prevents extra tasks

## Service tests

### Ciril Java job

Input description contains:

- Java
- Oracle
- PostgreSQL
- Quarkus
- C is a plus
- 3 years
- 1 day/week remote

Expected:

- required skills: Java, Oracle DB, PostgreSQL, Quarkus
- optional skills: C
- years_experience_min: 3
- remote_policy: hybrid
- confidence: high or medium

### Alternance Fullstack JS

Expected:

- role family: web_mobile or it_training_apprenticeship depending implementation
- skills: React, TypeScript, Node.js
- seniority: intern
- opportunity/job type remains apprenticeship

### Photography seller

Expected:

- not recommended to IT candidate
- no developer compatibility score
- no user-visible “non-IT” phrase

### Weak Web Developer

Input has title “Web Developer” but vague description and no stack.

Expected:

- analysis limited
- no fake normal score
- no “Aucune compétence spécifique” failure block on public page

## Integration tests

- management command dry-run prints candidate counts only
- management command enqueue mode creates/enqueues tasks without secrets
- Celery task changes status pending → processing → success
- Celery task changes processing → validation_error when validation fails
- Celery task changes processing → failed when LLM call fails after retries

## View tests

Patch/mock LLM client and assert no calls occur when requesting:

- `/jobs/`
- job detail
- match detail
- dashboard recommendations
- dashboard search pages

## Regression tests

- CV raw text not exposed
- CV file URL not exposed
- no live France Travail call in user-facing request path
- no raw internal flags rendered in templates
- no React/Next/Vue added
