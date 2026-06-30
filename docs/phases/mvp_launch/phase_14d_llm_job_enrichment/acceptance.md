# Phase 14D Acceptance Criteria

## Backend acceptance

- `JobEnrichment` model exists with status field and required status values.
- Raw LLM response is stored separately from validated output.
- Validation errors are stored and visible in admin or reportable through shell/admin.
- Token/cost metadata is recorded per enrichment attempt.
- Feature flags exist and default to safe values:
  - enrichment disabled
  - recommendations not using enriched data
- Enrichment service never runs from views.
- Celery task calls service only.
- Management command can dry-run and enqueue local jobs.
- Payload hash prevents duplicate enrichment of unchanged job text.

## LLM contract acceptance

- LLM response must be JSON-only.
- Skills without evidence are rejected.
- Evidence must correspond to job text.
- Soft skills are not stored as technical skills.
- Required vs optional skills are separated.
- Ciril Java job produces Java, Oracle, PostgreSQL, Quarkus with evidence.
- Optional C is optional only when text says it is a plus.

## Recommendation acceptance

When `JOB_RECOMMENDATIONS_USE_ENRICHED_DATA=True`:

- successful enrichment is used for matching.
- final score remains deterministic.
- missing skills are based on enriched skills.

When flag is false:

- old deterministic fallback path is used.
- no enrichment data changes recommendation behavior.

## UX acceptance

Public/user pages must not show internal parser/debug wording.

Forbidden user-visible phrases:

- non-IT
- IT signal
- skill signal
- parser
- generic_only
- excluded_non_it
- no_required_skills_extracted
- low_confidence_job_skills
- validation_error
- raw LLM

Public job list/details:

- no match score for anonymous users.
- if detected/enriched skills exist, show them cleanly.
- if no stack is available, hide the stack block or use neutral “Voir les détails de l’offre”; do not show “Aucune compétence spécifique” as a failure.

Logged-in recommendations/match detail:

- show friendly labels: Bon potentiel, Potentiel moyen, À vérifier, Faible alignement, Analyse limitée.
- show “Compétences présentes”, “Compétences à renforcer”, “Points à vérifier”.
- do not show raw flags.

## Tests acceptance

Required tests must prove:

- status transitions
- raw/validated output separation
- token/cost logging
- feature flag behavior
- no LLM calls in views
- no live France Travail calls in user views
- evidence validation rejection
- enriched Ciril job result
- photography seller excluded/not recommended
- weak Web Developer does not show fake confident score

## Final acceptance status

Even if all tests pass, final status is:

```text
BLOCKED_HUMAN_VISUAL_SIGNOFF
```

until Baha validates in Chrome.
