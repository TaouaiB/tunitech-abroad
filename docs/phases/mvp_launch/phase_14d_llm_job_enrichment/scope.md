# Phase 14D Scope

## In scope

1. Add an offline job enrichment data model/status layer.
2. Store raw LLM response and validated enrichment output separately.
3. Validate LLM output with strict schema and evidence checks.
4. Track status: `pending`, `processing`, `success`, `failed`, `validation_error`, `skipped`.
5. Track model/token/cost usage per enrichment run.
6. Add feature flags:
   - global enrichment enabled/disabled
   - recommendation use of enriched data enabled/disabled
7. Add Celery task for enrichment.
8. Add management command to enqueue/process local jobs.
9. Update matching/recommendations to use enriched data only when feature flag allows it.
10. Update user-facing copy so website feels polished and does not expose internal parser/debug labels.
11. Add tests with real-like France Travail examples:
    - Ciril Java/Quarkus/PostgreSQL/Oracle
    - alternance fullstack JS
    - photography seller
    - weak/vague Web Developer
    - Salesforce
    - Data Scientist
    - DevOps/Cloud
    - QA automation
    - ERP/Sage/PeopleSoft

## Out of scope

- No deployment.
- No commits.
- No full UI redesign.
- No React/Next/Vue/SPA.
- No live France Travail API calls from user search/match/recommendation views.
- No LLM scoring of candidates.
- No profile experience/education LinkedIn-style sections in this phase.
- No CV parsing changes unless a test proves a direct dependency.
- No deleting `manage.py`.

## Existing Phase 14C code

Phase 14C deterministic classification can remain as fallback/pre-filter/admin signal, but it must not create ugly public UI copy and must not override successful LLM enrichment.
