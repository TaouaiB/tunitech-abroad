# Public Job Eligibility Policy

## Eligibility states

### PUBLIC_MATCHABLE

Show in public job search and allow matching.

Use when:
- job is active
- job is clearly IT
- job has materialized technical skills
- not commercial/outreach/non-IT

Examples:
- Data Engineer GCP
- Tech Lead / DevOps
- Développeur Java/Angular
- Développeur .NET / C# Fullstack
- Consultant Cybersécurité Sénior with audit/risk/security delivery evidence

### PUBLIC_LIMITED_PENDING_ANALYSIS

Show only if the job is clearly IT and analysis is genuinely pending or newly imported.

UI:
- show `Analyse technique en cours`
- do not show detailed match CTA until matchability exists
- do not show fake score as confident

### ADMIN_REVIEW_ONLY

Hide from public list, but keep in admin.

Use when:
- job is IT-looking but has zero skills after extraction/recovery
- classification conflict exists
- technical evidence is ambiguous

### EXCLUDED

Hide from public list and public detail.

Use when:
- commercial/business development
- franchise/commercial network
- education/outreach/mediation
- generic business transformation consulting without hands-on technical delivery
- non-IT sector role

## Public detail behavior

If an excluded/admin-review-only job URL is opened directly:
- return 404 for normal users
- admin can still inspect via Django admin

## Matchability

Do not allow quick match / detailed match when:
- job is not publicly matchable
- job has zero materialized job skills
- job is excluded/admin-review-only
- analysis is still pending

## Badge behavior

Deduplicate badge values case-insensitively after placeholder filtering.

Example:
`CDD · Internship · Internship`
becomes:
`CDD · Internship`

## Wording behavior

Use `Compétences en cours d'analyse` only when analysis is truly pending.

Do not show it for:
- excluded jobs
- admin-review-only jobs
- analysis finished but zero skills
