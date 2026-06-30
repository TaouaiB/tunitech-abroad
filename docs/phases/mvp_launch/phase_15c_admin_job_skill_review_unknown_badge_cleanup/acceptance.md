# Phase 15C Acceptance Criteria

Accepted only if:

## Admin workflow
- Admin can find active jobs with no materialized skills.
- Admin can add/remove canonical `NormalizedJobSkill` rows manually.
- Admin actions re-run extraction/materialization through service layer only.
- Admin action for existing enrichment materialization does not call provider.

## Export/report
- A command/report exports jobs needing skill review.
- Output includes enough context for admin review.
- Command does not call provider or LLM.

## Unknown badge cleanup
- Public job card/detail no longer displays `Unknown`.
- Valid badges still display.

## Tests/checks
- Django tests pass.
- No migrations unless justified.
- CSS build and collectstatic pass.
- Safety greps pass.
- No secrets in diff.
- No forbidden stack.
- No matching formula change.
- No bulk unmatched import.
