# Boundaries

## Hard architecture rules

- Views stay thin.
- Business logic belongs in services.
- Celery tasks call services only.
- Models do not call external APIs.
- No OpenRouter/LLM calls from Django views.
- No France Travail live API calls during normal public/user job search.
- Public job search reads local PostgreSQL only.
- Public URLs use UUID `public_id`, never internal integer IDs.
- CV files are private and must not be publicly exposed.
- `CVUpload.objects` must exclude soft-deleted CVs.
- `CVUpload.all_objects` is only for admin/privacy/deletion/internal tasks.
- LLM may extract/explain/suggest/classify but must not decide final fit score.

## Fixing rule

If a bug is found:

1. Fix the smallest possible thing.
2. Stay within existing stack and architecture.
3. Add a regression test if practical.
4. Re-run the required checks.
5. Document it in the E2E report.

Do not use this phase to improve aesthetics beyond restoring broken styling.
