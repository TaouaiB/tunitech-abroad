# Phase 15D Decision Policy

## For unmatched candidates

Use the curated decision files.

Allowed decisions:
- already_resolved
- alias_to_existing
- create_new_skill
- ignore
- keep_pending

Rules:
- `already_resolved`: reconcile status only; do not create duplicate aliases.
- `alias_to_existing`: add alias only if target canonical skill already exists or is also created in this phase.
- `create_new_skill`: create only approved canonical skills.
- `ignore`: permanent ignore rule or ignored status; do not delete.
- `keep_pending`: do nothing.

Never bulk import all unmatched candidates.

## For zero-skill active jobs

Classify:
- `recoverable_it`: clear technical evidence in description; run deterministic recovery.
- `needs_manual_review`: IT-looking but too vague; admin reviews manually.
- `excluded_non_it`: commercial, teaching, outreach, business transformation, sector consulting; no fake skills.
- `llm_failed_or_empty`: enrichment failed/empty; can retry later through controlled task, not from public view.

## Acceptance target

After recovery on the current local dataset:
- active zero-skill jobs should decrease from 15.
- strong zero-skill IT jobs should be 0 if their text contains recoverable evidence.
- no excluded_non_it job should get fake technical skills.
- no duplicate job skills.
