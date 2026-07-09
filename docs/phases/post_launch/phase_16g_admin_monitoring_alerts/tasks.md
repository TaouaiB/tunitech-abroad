# Phase 16G — Admin Monitoring and Alerts — tasks.md

## Goal

Give the solo owner/admin enough visibility to operate the live product safely.

## In-scope apps/areas

```text
admin dashboards
core health checks
jobs/cvs/skills/search diagnostics display
admin alert service
admin file access logging
email alert queueing
```

## Tickets

### TTA-16G-001 — Owner operations dashboard

Priority: P0  
Type: admin/service/frontend/test

Acceptance:

```text
Staff/superuser can see active users, CV uploads, parse status counts, active/public/matchable jobs, ingestion last run, normalization failures, recommendation failures, email failures, Celery heartbeat.
Uses service-layer diagnostic outputs where possible.
No secrets displayed.
No raw full CV text displayed.
```

### TTA-16G-002 — Data quality dashboard

Priority: P0  
Type: admin/service/frontend/test

Acceptance:

```text
Displays jobs with zero/weak skills, hidden public eligibility reasons, unknown skill candidates, CV parse warnings, low-confidence fields, zero-result search buckets.
Links to safe admin objects only.
No public file paths exposed.
```

### TTA-16G-003 — Protected admin CV download

Priority: P0  
Type: privacy/security/admin/test

Acceptance:

```text
CV download is owner/superuser-only or strict staff permission.
Served through protected Django view/service, not public media.
Uses CVUpload.all_objects only in admin/internal service.
AdminFileAccessLog records admin_user, object_public_id, action, reason, IP/user agent where available.
No filesystem path leaked.
```

### TTA-16G-004 — AdminAlertService

Priority: P0  
Type: service/task/email/test

Acceptance:

```text
Alerts support Celery heartbeat missing, ingestion failure, parse-failure-rate spike, job-count drop, zero visible jobs, DB/Redis unavailable, 500 spike, disk usage issue if measurable.
Destination email read from ADMIN_ALERT_EMAIL.
No hardcoded real address except .env.example variable name.
Deduplication prevents spam.
Alert send failures are recorded.
```

### TTA-16G-005 — AdminOpsDigestService

Priority: P1  
Type: service/task/email/test

Acceptance:

```text
Digest summarizes new users, CV uploads, parse success/failure, active/public/matchable jobs, ingestion counts, unknown skills, zero-result searches, email failures, LLM cost if enabled.
Runs on configured schedule if enabled.
No raw CV text or secrets in digest.
```

### TTA-16G-006 — Health and anomaly checks

Priority: P0  
Type: service/command/task/test

Acceptance:

```text
Health check service can be called by admin dashboard and alert tasks.
Active/public job count drop detection exists.
If job count drops after 16B freshness changes, alert/report explains before/after counts.
Diagnostics failure does not break public site.
```

## Out of scope

```text
No multi-role enterprise admin.
No organization/team accounts.
No support ticketing system.
No public user-facing analytics dashboard.
```
