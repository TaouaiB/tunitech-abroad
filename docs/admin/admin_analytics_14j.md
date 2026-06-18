# Admin Analytics (Phase 14J)

## Overview
This document outlines the lightweight operational metrics exposed via the new Operations Dashboard (`/admin/operations/`).

## Available Metrics

The `AdminMetricsService` currently calculates the following real-time metrics using optimized Django ORM queries:

### Users & Profiles
- `users_total`: Total registered users.
- `new_signups_7d`: New user registrations over the past 7 days.
- `active_users_7d`: Users who logged in over the past 7 days.

### CV Processing
- `cv_uploads_7d`: Total CV uploads over the past 7 days.
- `cv_parse_failures_7d`: CVs uploaded in the past 7 days that failed parsing.
- `cv_parses_pending_stuck`: CVs stuck in `pending` or `processing` states for more than 15 minutes.

### Jobs & Ingestion
- `active_jobs`: Total normalized jobs currently marked as `active`.
- `jobs_ingested_24h`: Newly normalized jobs added in the last 24 hours.
- `stale_expired_jobs`: Normalized jobs marked as `stale` or `expired`.
- `latest_successful_ingestion`: Timestamp of the most recent `success` ingestion run.
- `latest_failed_ingestion`: Timestamp of the most recent `failed` ingestion run.

### Recommendations
- `recommendation_runs_24h`: Total recommendation pipeline runs initiated in the last 24 hours.
- `recommendation_failures_24h`: Recommendation pipeline runs that failed in the last 24 hours.
- `stale_recommendations`: Job recommendations currently marked as `stale`.
- `saved_jobs_count`: Total number of saved job bookmarks across all users.

### LLM & Emails
- `llm_calls_today`: LLM inference requests made today (since midnight).
- `llm_failures_today`: LLM inference requests that failed today.
- `JobEnrichmentAdmin` also exposes per-enrichment token count, estimated cost, status, attempts, and validation/error summaries without raw request/response payloads.
- `emails_sent_24h`: Total emails successfully dispatched in the past 24 hours.
- `emails_failed_24h`: Total emails that failed delivery in the past 24 hours.

### Privacy
- `pending_deletion_requests`: Number of account deletion requests currently awaiting processing.

## Missing/Unavailable Metrics
- **Cost Analytics**: `AdminMetricsService` does not yet calculate estimated LLM cost. Token counts are logged, but multiplying them by provider cost requires pricing maps which are not configured.
- **Detailed User Funnel Tracking**: Deep candidate-facing funnel analytics (e.g., job detail view counts, repeated failed match generation attempts) are not yet fully available as broad `UserEvent` queries would require a heavier telemetry structure. Currently, `AdminMetricsService` tracks only lightweight events.
- **Suspicious Behavior Rollups**: CV upload bursts, repeated quick-match attempts, repeated failed POSTs, and unusually high job-detail views are not available as dashboard metrics yet. Existing `UserEventAdmin` can be filtered manually by event type and date where events exist.

## Safety Notes
- The dashboard route is `/admin/operations/` and uses Django's `staff_member_required` guard.
- Dashboard metrics are aggregate counts/timestamps only. They do not include CV raw text, CV file URLs, raw unsubscribe tokens, secrets, API keys, OAuth tokens, or raw LLM payloads.
- Human Chrome signoff must still verify the Django Admin UI manually before Phase 14J can be accepted.
