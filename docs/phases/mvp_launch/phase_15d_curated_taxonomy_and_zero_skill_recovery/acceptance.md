# Phase 15D Acceptance Criteria

Accepted only if:

## Taxonomy
- Seed is idempotent.
- No duplicate canonical skills.
- No duplicate normalized aliases.
- Only approved decisions are applied.
- No bulk unmatched import.

## Ignore/reconcile
- Ignored terms do not keep appearing as pending candidates.
- Already-resolved candidates can be reconciled.
- Keep-pending candidates are untouched.
- No rows are deleted.

## Zero-skill recovery
- Active zero-skill IT jobs with clear evidence are recovered.
- Strong zero-skill recoverable jobs become zero or are explicitly justified.
- False-positive/non-IT/commercial/outreach jobs do not get fake technical skills.
- Commands support dry-run/apply.
- Recovery is idempotent.

## Architecture/safety
- Services own logic.
- Admin actions call services.
- No OpenRouter/France Travail calls from views/admin/templates.
- No matching formula change.
- No UI redesign.
- No migrations unless justified.

## Checks
- Full tests pass.
- CSS build passes.
- collectstatic dry-run passes.
- safety greps pass.
- no secrets in diff.
