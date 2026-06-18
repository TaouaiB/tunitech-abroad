# Admin Operations (Phase 14J)

## Overview
This document outlines the current Django Admin model coverage and operations configured during Phase 14J to ensure safe and observable platform management.

## Admin Model Coverage & Safety

### Accounts/Users
- **Admin Class**: `UserAdmin`
- **List Display**: Includes `date_joined`, `last_login`, active/staff status.
- **Search & Filters**: Search by email/username. Filters for active, staff, superuser, date joined, last login.
- **Readonly Fields**: `date_joined`, `last_login`.
- **Safety**: Password hashes are managed safely via `DefaultUserAdmin`.

### Profiles/CVs
- **Admin Classes**: `CandidateProfileAdmin`, `CVUploadAdmin`, `CVParsedDataAdmin`.
- **Filters**: Added `french_level`, `english_level`, `uploaded_at`, `deleted_at`, `StuckCVFilter`.
- **Readonly Fields**: Public IDs, timestamps, parsing metrics.
- **Safety**:
  - Raw CV text (`raw_text`) is strictly excluded from `CVParsedDataAdmin`.
  - The actual `file` field in `CVUploadAdmin` is excluded to prevent public URL exposure in admin list views.
- **Admin Actions**: `reparse_cvs` securely delegates reparsing to the `parse_cv` Celery task.

### Jobs/Ingestion
- **Admin Classes**: `JobSourceAdmin`, `IngestionRunAdmin`, `RawJobRecordAdmin`, `NormalizedJobAdmin`, `NormalizedJobSkillAdmin`.
- **List Display**: Enhanced with error counts/summaries, timestamps (`first_seen_at`, `last_seen_at`), remote type, and status.
- **Filters**: Normalization status, source, job type, remote type, country.
- **Safety**: Payload hashes and complex JSONs are kept readonly or hidden from main lists.
- **Admin Actions**:
  - `reprocess_raw_jobs` delegates to `normalize_raw_job_record` Celery task.
  - `mark_jobs_stale` and `mark_jobs_expired` delegate selected status changes to `JobAdminOperationsService.mark_selected_jobs_status`.

### Skills
- **Admin Classes**: `SkillAdmin`, `SkillAliasAdmin`, `UnmatchedSkillCandidateAdmin`.
- **Admin Actions**: `ignore_candidates` and `map_candidates` securely delegate to `UnmatchedSkillReviewService`.

### Matching/Recommendations
- **Admin Classes**: `MatchResultAdmin`, `JobRecommendationAdmin`, `RecommendationRunAdmin`, `SavedJobAdmin`.
- **List Display**: Shows `fit_score`, `match_confidence`, run statuses, and `stored_recommendations_count`.
- **Filters**: Status, computed/started dates.
- **Admin Actions**: `refresh_recommendations` delegates to `refresh_user_recommendations` Celery task.

### Privacy/Notifications
- **Admin Classes**: `DeletionRequestAdmin`, `ConsentRecordAdmin`, `EmailBatchAdmin`, `EmailEventAdmin`, `EmailPreferenceAdmin`, `EmailUnsubscribeTokenAdmin`.
- **Safety**: Raw unsubscribe tokens are excluded from `EmailUnsubscribeTokenAdmin`.
- **Admin Actions**: `process_deletion_requests` securely delegates to `process_account_deletion` Celery task.

### LLM
- **Admin Classes**: `LLMRequestLogAdmin`, `JobEnrichmentAdmin`.
- **List Display**: Request logs show purpose/model/status/user/token counts/latency. Enrichment logs show public ID, job, status, model, token count, estimated cost, attempts, and creation time.
- **Filters/Search**: Request logs filter by status/purpose/provider and search user email/purpose/model. Enrichment logs filter by status/model/date and search public ID/job title/company/payload hash.
- **Readonly Fields**: Token, cost, status, timestamp, validation, and error summary fields are readonly.
- **Safety**: Raw API payloads, raw enrichment requests, and raw LLM responses are excluded from list displays. `JobEnrichmentAdmin` excludes `raw_request_json`, `raw_response_text`, and `raw_response_json` from the admin form.

## Test Coverage Status
- `apps/core/tests/test_14j_admin.py` covers admin operations access boundaries, stable metric keys, sensitive admin field exclusions, LLM enrichment raw payload exclusions, deletion request task delegation, and normalized job status service delegation.
- Manual browser coverage is still required for all admin list/detail screens.

## Manual Admin Signoff
The final phase requires a human operator to verify the Django Admin directly in Chrome, confirming that raw CV texts, public file URLs, and sensitive unsubscribe tokens/API keys do not leak into the UI.
