# Agent Prompt — Phase 14D LLM-Assisted Job Enrichment Pipeline

You are working in the TuniTech Abroad Django project.

Read these files first:

- `docs/phases/phase_14d_llm_job_enrichment/README.md`
- `docs/phases/phase_14d_llm_job_enrichment/scope.md`
- `docs/phases/phase_14d_llm_job_enrichment/boundaries.md`
- `docs/phases/phase_14d_llm_job_enrichment/llm_schema_contract.md`
- `docs/phases/phase_14d_llm_job_enrichment/data_model.md`
- `docs/phases/phase_14d_llm_job_enrichment/feature_flags_and_costs.md`
- `docs/phases/phase_14d_llm_job_enrichment/tasks.md`
- `docs/phases/phase_14d_llm_job_enrichment/acceptance.md`
- `docs/phases/phase_14d_llm_job_enrichment/test_plan.md`
- `docs/phases/phase_14d_llm_job_enrichment/regression_security_checks.md`

## Mission

Implement Phase 14D only.

Phase 14C regex/classification approach was not reliable enough in real browser testing. Real France Travail jobs can contain useful technical stack in free-text descriptions while deterministic extraction misses it.

Build a controlled offline LLM enrichment pipeline that extracts structured job facts with evidence, stores raw and validated outputs, monitors status/tokens/cost, and allows matching/recommendations to use enriched data behind feature flags.

## Non-negotiable architecture rules

- No LLM calls from Django views.
- No LLM calls from templates.
- No LLM calls during normal user search or match requests.
- No France Travail live API calls during normal user search.
- LLM does not compute final fit score.
- Matching score remains deterministic.
- Celery tasks call services only.
- Views stay thin.
- Models do not call external APIs.
- Do not add React/Next/Vue/SPA.
- Do not commit.
- Do not deploy.

## Required implementation

1. Add a `JobEnrichment` model with status tracking:
   - `pending`
   - `processing`
   - `success`
   - `failed`
   - `validation_error`
   - `skipped`

2. Store raw LLM output separately from validated output:
   - raw request JSON
   - raw response text
   - raw response JSON
   - validated output JSON
   - validation errors JSON

3. Track usage/cost:
   - model
   - prompt tokens
   - completion tokens
   - total tokens
   - estimated cost USD

4. Add feature flags:
   - `JOB_ENRICHMENT_ENABLED`
   - `JOB_RECOMMENDATIONS_USE_ENRICHED_DATA`

5. Create LLM enrichment service with strict JSON schema and evidence validation.

6. Create Celery task that calls the service and updates `JobEnrichment` status.

7. Create management command `enrich_jobs` with dry-run, enqueue, sync local test mode, limit, and force options.

8. Update matching/recommendations to use enriched data only when feature flag allows it and enrichment status is success.

9. Update UX copy:
   - no user-visible IT/non-IT labels
   - no raw internal flags
   - no parser wording
   - hide empty stack blocks
   - show friendly labels like “Bon potentiel”, “À vérifier”, “Analyse limitée”

10. Add tests from `test_plan.md`.

## Required proof cases

At minimum, tests or proof command must cover:

- Ciril Java job: Java, Oracle, PostgreSQL, Quarkus extracted with evidence; C optional if text says un plus.
- Alternance Fullstack JS: React, TypeScript, Node.js extracted.
- Photography seller: no recommendation as IT job; user-facing copy does not say “non-IT”.
- Weak Web Developer: analysis limited; no fake normal score.
- Salesforce job: Salesforce/Apex extracted.
- DevOps/Cloud job: Docker/Kubernetes/cloud tools extracted if present.
- QA automation: Cypress/Selenium/Playwright extracted if present.
- ERP/Sage/PeopleSoft: ERP tools extracted if present.

## Final commands

Run:

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test apps.jobs apps.skills apps.matching apps.recommendations apps.llm --settings=config.settings.local
python manage.py test --settings=config.settings.local
```

Then run regression/security checks from `regression_security_checks.md`.

## Final report

Create or update:

```text
docs/phases/phase_14d_llm_job_enrichment/agent_report.md
```

Use `agent_report_template.md`.

Final verdict must be one of:

```text
FAIL
BLOCKED_HUMAN_VISUAL_SIGNOFF
```

Never write PASS before Baha manually validates in Chrome.
