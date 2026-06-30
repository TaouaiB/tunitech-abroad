# Phase 11 Tasks — Privacy Deletion and Compliance Flows

## Current phase

Phase 11 only: Privacy deletion and compliance flows.

## Architectural rules

- Views stay thin. Views validate HTTP/form concerns and call services.
- Business logic belongs in services.
- Celery tasks call services only.
- Models store data and do not perform deletion orchestration, email sending, external API calls, or LLM calls.
- Privacy services may call CV/recommendation/matching cleanup services, but must not duplicate their business rules.
- Public URLs use `public_id` UUIDs, never internal integer IDs.
- CV files are private and must never be publicly exposed.
- `CVUpload.objects` must exclude soft-deleted CVs.
- `CVUpload.all_objects` is allowed only in privacy/admin/deletion/internal tasks.
- No real secrets in code, docs, logs, tests, or reports.

## TTA-1101 — Pre-flight audit and phase alignment

Type: audit

Tasks:

1. Read existing implementation before changing code:
   - `apps/privacy/`
   - `apps/cvs/`
   - `apps/profiles/`
   - `apps/matching/`
   - `apps/recommendations/`
   - `apps/notifications/`
   - `apps/analytics/`
   - `config/urls.py`
   - dashboard urls/views/templates
2. Identify existing models:
   - `ConsentRecord`
   - `UserEvent`
   - `CVUpload`
   - `CVParsedData`
   - `CandidateProfile`
   - `ProfileSkill`
   - `MatchResult`
   - `QuickMatchSession`
   - `JobRecommendation`
   - `RecommendationRun`
   - `SavedJob`
   - `EmailPreference`
   - `EmailEvent`
   - `EmailBatch`
   - `EmailUnsubscribeToken`
   - `LLMUsageLog` or equivalent
   - django-allauth email/social account models
3. Reuse existing app structure. Do not create duplicate apps if `apps.privacy` already exists.
4. Confirm Phase 10 routes still work. Do not break email preferences or unsubscribe.

Acceptance:

- The agent report lists existing relevant models/services/routes discovered.
- No duplicate privacy app is created.
- No future phase work is started.

## TTA-1102 — Privacy and Terms pages

Type: feature

Routes:

```text
/privacy/
/terms/
```

Tasks:

1. Add thin views for Privacy Policy and Terms pages.
2. Add templates with MVP-safe French content.
3. Content must include:
   - TuniTech Abroad processes account, profile, CV, job interaction, match, recommendation, email preference, and consent data.
   - CV files are private.
   - User can delete CV.
   - User can request account/data deletion.
   - Recommendation emails are opt-in and can be unsubscribed.
   - No guaranteed employment, visa, relocation, or legal advice.
   - France Travail job data is ingested/stored locally; public search does not call France Travail live.
4. Add navigation/footer links if a base footer/nav exists. Keep simple.
5. Add route tests and template tests.

Acceptance:

- `/privacy/` returns HTTP 200 for anonymous users.
- `/terms/` returns HTTP 200 for anonymous users.
- Templates do not expose secrets or admin details.
- Text does not promise employment, visa, relocation, or legal outcomes.

## TTA-1103 — Consent service hardening

Type: service

Expected service:

```text
apps/privacy/services/consent.py
ConsentService.record(user, consent_type, consent_text, consent_version, request_meta=None) -> ConsentRecord
```

Tasks:

1. Inspect existing `ConsentRecord` model before changing it.
2. Ensure `ConsentService.record()` exists and is the only normal way views/services record consent.
3. Supported consent types for MVP:
   - `cv_processing`
   - `email_digest`
   - `terms`
   - `privacy_policy`
   - `cookie_session_notice`
4. Store stable consent text/version. Do not store huge raw documents.
5. Store minimal request metadata only if fields exist already or are safely added:
   - IP address hash or short string if already supported
   - user agent summary if already supported
   - source path/action
6. Do not log full user profile or CV text.
7. Integrate with CV upload consent if Phase 6 only validates checkbox but does not record consent.
8. Integrate with email digest preference changes if Phase 10 only toggles preference but does not record consent.

Acceptance:

- Recording consent is idempotent enough for repeated user actions without duplicate side effects causing errors.
- CV upload with consent creates or updates a `ConsentRecord` for `cv_processing`.
- Enabling weekly digest creates or updates a `ConsentRecord` for `email_digest`.
- Disabling digest is handled by the email preference service and should not create a false opt-in consent.
- Tests cover consent service and integration points.

## TTA-1104 — Harden CV deletion

Type: service/view/task-safe cleanup

Expected service:

```text
apps/cvs/services/deletion.py
CVDeletionService.delete_cv(user, cv_public_id) -> ServiceResult
```

Tasks:

1. Inspect existing CV deletion implementation.
2. Ensure delete CV flow:
   - requires authentication
   - verifies ownership
   - uses `public_id`, not internal integer ID, in public/private user routes
   - deletes/removes the physical PDF file from private media storage when present
   - soft-deletes `CVUpload`
   - clears/deletes `CVParsedData`
   - removes or deactivates unconfirmed `ProfileSkill` rows sourced only from that CV
   - marks recommendations stale or removes user recommendations as appropriate
   - records a `UserEvent` or privacy audit event without leaking CV text/path
3. Normal application code must use `CVUpload.objects`.
4. Deletion/privacy/internal code may use `CVUpload.all_objects`.
5. Handle missing physical file gracefully: deletion should still complete and record an error summary if useful.
6. Add tests for physical file deletion and default manager exclusion.

Acceptance:

- User can delete own CV.
- User cannot delete another user's CV.
- Deleted CV is excluded from `CVUpload.objects`.
- Deleted CV is visible through `CVUpload.all_objects` only where appropriate.
- Physical file is removed or missing-file case is handled safely.
- No public URL for the CV file is created.

## TTA-1105 — Account deletion request model and page

Type: model/service/view

Expected route:

```text
/dashboard/account/
/dashboard/settings/delete-account/
```

Tasks:

1. Inspect existing `apps/privacy` models first.
2. Add or complete a deletion request model. Suggested model name:

```text
DeletionRequest
```

or reuse existing `AccountDeletionRequest` if already present.

3. Required fields:
   - `public_id` UUID
   - `user` FK to user, nullable only if needed after deletion/anonymization
   - `status`: `pending`, `processing`, `completed`, `failed`, `cancelled`
   - `requested_at`
   - `processed_at`
   - `error_message` short text, no sensitive dump
   - `attempt_count`
   - optional `completed_summary_json` with counts only
4. Add migration.
5. Add a dashboard account/settings page with a delete-account section.
6. Add a confirmation form requiring a deliberate confirmation field, for example typing `DELETE` or checking a confirmation checkbox.
7. POST creates a deletion request through `AccountDeletionService.request_deletion(user)`.
8. Do not immediately hard-delete the user in the view.
9. The view should redirect to a safe page or show request status.
10. Do not expose internal integer request IDs.

Acceptance:

- Authenticated user can access account settings.
- Anonymous user is redirected to login.
- Delete account POST creates a deletion request.
- Duplicate pending requests are idempotent and do not create endless duplicates.
- The view remains thin and calls service.

## TTA-1106 — AccountDeletionService

Type: service

Expected service:

```text
apps/privacy/services/account_deletion.py
AccountDeletionService.request_deletion(user) -> DeletionRequest
AccountDeletionService.process_request(deletion_request) -> DeletionRequest
```

Tasks:

1. Implement deletion as a transaction-aware service.
2. `request_deletion(user)`:
   - creates or returns a pending/processing request for the user
   - records `UserEvent` / audit event with safe metadata
   - optionally enqueues `process_account_deletion` Celery task if Celery wiring exists
3. `process_request(deletion_request)` must be idempotent and retry-safe.
4. Processing flow:
   - mark request `processing`
   - disable login early (`user.is_active = False`) so user cannot continue using account during processing
   - delete all user CV physical files
   - delete/clear `CVParsedData`
   - soft-delete or delete `CVUpload` records according to existing model design
   - delete profile skills
   - delete candidate profile
   - delete saved jobs
   - delete match results
   - delete recommendations and recommendation runs owned by/for the user where appropriate
   - delete quick match sessions for the user if authenticated sessions exist
   - delete email preferences
   - delete or anonymize notification email events as required by existing model constraints
   - delete or anonymize LLM usage logs tied to the user, preserving operational aggregate data only if necessary
   - anonymize/delete `UserEvent` data tied to the user
   - remove allauth social/email account records tied to the user if safe with cascades
   - anonymize the user record or delete it, depending on FK constraints and current project design
   - mark request `completed`
5. If hard-deleting the user is unsafe due to FK constraints, anonymize instead:
   - email becomes `deleted-user-<public_id>@deleted.local` or similar non-routable value
   - username/display fields cleared if present
   - password unusable
   - `is_active=False`
   - personal fields cleared
6. Do not delete global jobs, skills, job sources, ingestion runs, raw job records, normalized jobs, global skill taxonomy, or system settings.
7. Record summary counts only, not personal content.
8. On failure:
   - mark request `failed`
   - increment `attempt_count`
   - save short `error_message`
   - allow retry by processing the same request again

Acceptance:

- Account deletion disables login.
- Account deletion removes CV files.
- Account deletion removes or anonymizes profile, CV parsed data, profile skills, saved jobs, match results, recommendations, email preferences, and personal events.
- Global job/skill/source data remains intact.
- Failed deletion can be retried.
- Service is covered by tests.

## TTA-1107 — Celery privacy tasks

Type: task

Expected tasks:

```text
process_account_deletion(deletion_request_id)
cleanup_expired_quick_matches()
delete_orphaned_cv_files()
```

Tasks:

1. Add privacy tasks under the existing privacy app or task layout.
2. Tasks must be thin and call services only.
3. `process_account_deletion` loads the deletion request and calls `AccountDeletionService.process_request()`.
4. `cleanup_expired_quick_matches` removes expired anonymous quick match sessions if the model has expiry fields.
5. `delete_orphaned_cv_files` scans private CV media and removes files no longer referenced by active/all CV records if safe. If safe implementation is too risky, implement a dry-run/report service first and document blocker.
6. Do not log CV filenames with user-identifying paths if avoidable.
7. Add task delegation tests with mocks.

Acceptance:

- Task calls service and returns stable result.
- Missing/deleted request ID is handled safely.
- Retry does not duplicate deletion side effects.
- No long business logic in task body.

## TTA-1108 — Privacy dashboard/account UX

Type: view/template

Routes:

```text
/dashboard/account/
/dashboard/settings/delete-account/
```

Tasks:

1. Add dashboard account page if missing.
2. Show safe account/privacy controls:
   - email address/account status
   - link to email preferences
   - link to CV management
   - link to Privacy Policy and Terms
   - delete account section
3. Add delete account confirmation page/form.
4. Use clear French MVP wording.
5. Do not show raw secrets, tokens, OAuth codes, raw CV text, or internal database IDs.
6. Add tests for route access, template rendering, and POST behavior.

Acceptance:

- Authenticated user can view account privacy settings.
- Delete account confirmation is deliberate.
- Delete account flow creates request and disables login after processing.
- Anonymous users cannot access private account pages.

## TTA-1109 — UserEvent anonymization/deletion

Type: service

Tasks:

1. Inspect `UserEvent` model fields and existing analytics service.
2. Implement deletion/anonymization behavior as part of `AccountDeletionService`.
3. Keep aggregate operational analytics if possible without user-identifying data.
4. Do not delete global job activity needed for operations unless it contains personal user data only.
5. Avoid logging raw query text if it may contain personal data.

Acceptance:

- After deletion, no `UserEvent` row remains linked to the deleted user, or linked user data is anonymized according to the model design.
- Tests assert that private event data is gone/anonymized.

## TTA-1110 — Tests and regression coverage

Type: tests

Required tests:

1. Privacy and Terms public pages return 200.
2. Account page requires login.
3. Delete account confirmation requires login.
4. Delete account POST requires deliberate confirmation.
5. Deletion request is idempotent for duplicate pending requests.
6. `process_account_deletion` task delegates to service.
7. `AccountDeletionService.process_request()` disables login.
8. Account deletion removes CV physical files.
9. Account deletion removes profile/private candidate data.
10. Account deletion removes saved jobs.
11. Account deletion removes match results.
12. Account deletion removes recommendations.
13. Account deletion removes email preferences or personal email preference data.
14. User events are anonymized/deleted.
15. Failed deletion is retryable.
16. CV deletion removes file.
17. Deleted CV not returned by default manager.
18. User cannot delete another user's CV.
19. CV processing consent is recorded.
20. Email digest consent is recorded only on opt-in.

Acceptance:

- `python manage.py test apps.privacy --settings=config.settings.local` discovers and runs tests.
- `Found 0 test(s)` is failure.
- Full suite passes.

## TTA-1111 — Security and boundary audit

Type: audit

Tasks:

1. Confirm no real secrets appear in code/docs/tests.
2. Confirm no raw CV text is logged.
3. Confirm no public route exposes internal integer IDs for privacy/deletion/CV.
4. Confirm `CVUpload.all_objects` appears only in admin/privacy/deletion/internal tests/tasks, not public runtime query code.
5. Confirm no OpenRouter/LLM calls from views or deletion services.
6. Confirm no France Travail live calls from public job search.
7. Confirm no Phase 12/13/14 scope added.
8. Clean artifacts:
   - `__pycache__`
   - `.pyc`
   - `.sqlite3`
   - `celerybeat-schedule*`
   - stale `agent_report.md.save`
   - accidental `task.md`
   - review zips

Acceptance:

- Boundary grep output is included in `agent_report.md`.
- Working tree contains only intentional Phase 11 files.
