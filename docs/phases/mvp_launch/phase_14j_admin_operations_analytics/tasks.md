# Phase 14J Tasks — Admin Operations and Analytics

## TTA-14J-01 — Admin inventory and gap review

Create or update:

- `docs/admin/admin_operations_14j.md`
- `docs/admin/admin_analytics_14j.md`

Document the current admin coverage for:

- accounts/users
- profiles
- CV uploads and parsed CV data
- skills and unmatched skills
- job sources, ingestion runs, raw jobs, normalized jobs, normalized job skills
- matching
- recommendations
- saved jobs
- LLM prompt/version/cache/usage/enrichment logs
- notifications/email preferences/email batches/email events/unsubscribe tokens
- privacy/consent/deletion requests
- analytics/user events
- core/system settings

Each entry must state:

- model
- admin class exists or missing
- list display quality
- search fields
- filters
- readonly fields
- sensitive fields hidden or exposed
- admin actions available
- safe service/task delegation status
- test coverage status

## TTA-14J-02 — Harden admin sensitive field handling

Ensure admin list/detail pages do not expose dangerous fields casually.

Rules:

- CV files must not become public links.
- `CVParsedData.raw_text` must not appear in list displays.
- Raw unsubscribe token values must not appear in list displays.
- LLM request/response payloads must not appear in list displays.
- Secrets/API keys/tokens must never appear in admin.
- Raw job payloads may be visible only in detail/readonly/debug-style fields, not in high-volume list displays.
- Admin should prefer `public_id`, owner email, status, timestamps, counts, and error summaries.

## TTA-14J-03 — Improve operational admin list displays and filters

Improve existing Django Admin registrations where needed.

Expected coverage:

### Users

- search by email
- filters for active/staff/superuser/date joined/last login if available
- useful readonly timestamps

### Profiles/CVs

- filter by profile completeness status, current level, target type, language level
- CV filters for parse_status, is_active, uploaded_at, deleted_at
- no raw CV text in list display
- no clickable public file URL
- failed/stuck parse visibility

### Jobs/Ingestion

- JobSource admin
- IngestionRun admin with status, trigger_type, counts, started/finished, error summary
- RawJobRecord admin with source, source_job_id, normalization_status, first/last seen, hash, error summary
- NormalizedJob admin with status, type, country/city, remote, experience, skill status, timestamps
- filters for stale/expired/active jobs
- search by title/company/source_job_id

### Skills

- Skill and SkillAlias search/filter
- UnmatchedSkillCandidate filters by status/source/occurrence_count
- admin actions should delegate to review services where possible

### Matching/recommendations/saved jobs

- MatchResult admin with user/job/score/confidence/timestamps
- RecommendationRun admin with status/counts/errors
- JobRecommendation admin with confidence/stale/saved status filters where available
- SavedJob admin with user/job/timestamp

### LLM

- Prompt/version/cache/usage/enrichment admin where models exist
- token/cost/status filters
- failed/skipped filters
- no API key visibility
- no raw payloads in list display

### Notifications/privacy/analytics

- EmailPreference admin
- EmailBatch admin
- EmailEvent admin
- EmailUnsubscribeToken admin with token hidden from list display
- ConsentRecord admin
- DeletionRequest admin
- UserEvent admin

## TTA-14J-04 — Add safe admin actions through services/tasks only

Add only admin actions that are safe, scoped, and useful.

Preferred actions:

- retry failed CV parses by enqueueing existing `parse_cv` task or service
- re-normalize selected raw job records by enqueueing existing normalization task/service
- mark selected normalized jobs stale/expired/archived only through a service if available
- refresh selected users' recommendations by enqueueing existing recommendation task/service
- re-send/retry failed email batch/event only if an existing idempotent service supports it
- process deletion requests only through privacy deletion service/task

Rules:

- admin action must not duplicate business logic
- admin action must not call external APIs directly
- admin action must not call OpenRouter directly
- admin action must not print secrets
- admin action must give count/status message to admin
- risky actions must be conservative or skipped with documentation

## TTA-14J-05 — Add lightweight admin operations dashboard if not already sufficient

Allowed implementation:

- Django admin-only view
- Django templates
- normal staff/superuser check
- service object such as `AdminMetricsService`

Suggested route:

- `/admin/operations/` or admin custom URL under existing admin site

Suggested metrics:

- users total
- new signups last 7 days
- active users last 7 days if events/last_login available
- CV uploads last 7 days
- CV parse failures last 7 days
- CV parses currently pending/processing older than threshold
- active jobs
- jobs ingested last 24 hours
- stale/expired jobs
- latest successful ingestion time
- latest failed ingestion time
- recommendation runs last 24 hours
- recommendation failures last 24 hours
- stale recommendations count if model supports it
- saved jobs count
- LLM calls today
- LLM estimated cost today if model supports it
- LLM failures today
- emails sent/failed last 24 hours
- pending deletion requests

Keep it simple. No charting library. No SPA. No candidate-facing redesign.

## TTA-14J-06 — Suspicious behavior visibility

Add lightweight admin visibility using existing `UserEvent`/models where possible.

Examples:

- many CV uploads by one user in short period
- many quick-match attempts
- many match-generation attempts
- repeated failed POSTs if events exist
- unusually high job detail views if events exist

If data is not available yet, document as `not available yet` in `docs/admin/admin_analytics_14j.md`. Do not invent tracking outside this phase unless a tiny existing UserEvent-based query is enough.

## TTA-14J-07 — Tests

Add tests for:

- normal user cannot access admin operations page
- anonymous user cannot access admin operations page
- staff/superuser can access admin operations page
- metrics service returns stable keys without exposing secrets
- admin actions delegate to services/tasks, not direct external clients
- CV admin list display excludes raw text/file URL
- LLM admin list display excludes secrets/raw payloads
- unsubscribe token raw value not listed
- admin docs exist and are non-empty

Use existing factories/helpers where available. Keep tests deterministic.
