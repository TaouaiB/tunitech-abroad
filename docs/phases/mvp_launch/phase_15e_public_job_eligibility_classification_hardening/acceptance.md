# Phase 15E Acceptance Criteria

Accepted only if:

## Classification
- Real IT jobs are not classified as `excluded_non_it` because of generic business/client/sector words.
- Commercial/outreach/franchise/business-consulting roles are excluded.
- `réseau informatique` is treated differently from `réseau de franchise`.
- `cybersécurité` technical jobs are treated differently from cyber sales/outreach roles.

## Eligibility
- Central service determines public visibility and matchability.
- Public list excludes excluded/admin-review-only jobs.
- Direct public detail for excluded/admin-review-only jobs 404s for normal users.
- Admin can still inspect all jobs.

## Matching/CTA
- Non-matchable jobs cannot run quick/detailed match.
- Jobs with zero materialized skills do not show detailed analysis CTA.
- `Compétences en cours d'analyse` only appears for true pending analysis.

## Presentation
- Duplicate badges are removed.
- Placeholder badges remain hidden.

## Commands/tests
- `reclassify_jobs` dry-run/apply/idempotent behavior works.
- Full tests pass.
- CSS build and collectstatic dry-run pass.
- Safety greps pass.
- No secrets in diff.
