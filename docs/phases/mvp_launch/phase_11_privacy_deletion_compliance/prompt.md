# Phase 11 Implementation Prompt — Privacy Deletion and Compliance Flows

You are the implementation agent for TuniTech Abroad. Work inside the existing Django repository only.

## Role

Act as a senior Django engineer. Implement Phase 11 only. You may work automatically through all tickets in this phase. Do not ask for approval between tickets. You must not start Phase 12.

## Read first

Read these files before editing code:

```text
AGENTS.md
README.md
.env.example
config/settings/base.py
config/settings/local.py
docs/phases/phase_11_privacy_deletion_compliance/tasks.md
docs/phases/phase_11_privacy_deletion_compliance/acceptance.md
```

Then inspect existing apps:

```text
apps/privacy/
apps/cvs/
apps/profiles/
apps/matching/
apps/recommendations/
apps/notifications/
apps/analytics/
apps/accounts/
config/urls.py
```

Also read planning docs if available under `docs/planning/`:

```text
BRD v1
PRD v1
Implementation Roadmap v1
Service Contracts v1
Page + URL + View Map v1
Data Flow / Sequence Diagrams v1
Database Schema v1
```

## Non-negotiable stack and architecture rules

Use only:

- Django
- Django ORM
- PostgreSQL
- Redis/Celery if tasks are needed
- django-allauth
- Django templates
- HTMX only if already used/needed
- Tailwind classes only if already used

Do not use:

- React
- Next.js
- Angular
- FastAPI
- MongoDB
- SQLAlchemy
- SPA architecture

Architecture rules:

- Views stay thin.
- Business logic goes in services.
- Celery tasks call services only.
- Models store data; models must not call external APIs, send email, or orchestrate deletion.
- No OpenRouter/LLM calls from views or privacy deletion code.
- No France Travail live calls during normal user search.
- User job search reads local PostgreSQL only.
- Public URLs use UUID `public_id`, never internal integer IDs.
- CV files are private and must not be publicly exposed.
- `CVUpload.objects` excludes soft-deleted CVs.
- `CVUpload.all_objects` is only allowed for admin/privacy/deletion/internal tasks.
- Never commit, print, log, or document real secrets.

## Phase 11 goal

Implement privacy-safe deletion and consent handling:

- Privacy Policy page
- Terms page
- Consent recording for CV processing and email digest opt-in
- Harden delete CV
- Delete account request page and flow
- AccountDeletionService
- Privacy deletion Celery task
- Cleanup services/tasks where safe
- Tests and regression coverage

## Phase 11 hard boundary

Allowed:

- Functional privacy/account/CV deletion code
- Minimal templates/routes required for privacy flows
- Model/migration for deletion requests if missing
- Tests
- Minimal admin registration only if needed for the new deletion request model and consistent with existing admin patterns

Forbidden:

- Do not implement Phase 12 admin dashboard/health checks/observability.
- Do not implement deployment settings.
- Do not polish the whole UI.
- Do not add new job ingestion features.
- Do not call France Travail from public search.
- Do not change deterministic score formula.
- Do not change recommendation ranking except data cleanup during deletion.
- Do not add new LLM features.
- Do not enable scheduled production jobs.

## Implementation tickets

Implement all tickets in `tasks.md`:

- TTA-1101 Pre-flight audit and phase alignment
- TTA-1102 Privacy and Terms pages
- TTA-1103 Consent service hardening
- TTA-1104 Harden CV deletion
- TTA-1105 Account deletion request model and page
- TTA-1106 AccountDeletionService
- TTA-1107 Celery privacy tasks
- TTA-1108 Privacy dashboard/account UX
- TTA-1109 UserEvent anonymization/deletion
- TTA-1110 Tests and regression coverage
- TTA-1111 Security and boundary audit

## Implementation guidance

### Reuse existing structure

Do not create duplicate apps. If `apps.privacy` exists, extend it. If `apps.cvs.services.deletion` exists, harden it rather than replacing randomly.

### Deletion request model

Prefer `DeletionRequest` in `apps.privacy.models` unless an equivalent model already exists. Use UUID `public_id` for any user-facing request references.

Suggested statuses:

```python
PENDING = "pending"
PROCESSING = "processing"
COMPLETED = "completed"
FAILED = "failed"
CANCELLED = "cancelled"
```

Add `attempt_count`, `error_message`, `requested_at`, `processed_at`, and optional summary counts.

### Account deletion service

Implement:

```python
AccountDeletionService.request_deletion(user)
AccountDeletionService.process_request(deletion_request)
```

`request_deletion` should be idempotent: return existing pending/processing request if one exists.

`process_request` should be retry-safe. It should disable login early and delete/anonymize private user data. If hard-deleting the user breaks FK constraints, anonymize the user and set unusable password + inactive.

Do not delete global jobs, raw job records, normalized jobs, job sources, skills, skill aliases, system settings, or ingestion data.

### CV deletion

Preserve the Phase 6 privacy rules:

- CV files are private.
- Soft-deleted CVs are excluded from `CVUpload.objects`.
- `CVUpload.all_objects` is allowed only for deletion/internal/admin tasks.

Delete physical files safely. Missing files should not produce a fatal user-facing failure if database cleanup can complete.

### Consent recording

Use `ConsentService.record()` from services. Views/services should not create `ConsentRecord` directly unless in tests/factories.

Record:

- `cv_processing` when user uploads CV with consent.
- `email_digest` when user enables weekly digest.

Do not record a positive email digest consent when the user disables the digest.

### Views/templates

Private views must require login. Views should call services and redirect/render. Do not put deletion logic in views.

Suggested routes:

```text
/privacy/
/terms/
/dashboard/account/
/dashboard/settings/delete-account/
```

Use French copy, but keep it simple and functional.

### Celery tasks

Tasks must be thin:

```python
@shared_task
def process_account_deletion(deletion_request_id):
    deletion_request = DeletionRequest.objects.get(...)
    return AccountDeletionService.process_request(deletion_request)
```

No long deletion orchestration in task body.

### Tests

Add meaningful tests in `apps/privacy/tests.py` or a tests package. Make sure they are discovered.

Required: `python manage.py test apps.privacy --settings=config.settings.local` must not say `Found 0 test(s)`.

## Autonomous repair loop

After implementation, run acceptance commands from `acceptance.md`.

If any command fails:

1. Read the full traceback/log.
2. Identify the root cause.
3. Fix the smallest correct cause.
4. Rerun the failed command.
5. Rerun the full acceptance set after fixes.
6. Repeat up to 8 repair loops.

You must not claim success if:

- PostgreSQL-backed tests were blocked.
- `Found 0 test(s)` appears for the phase app.
- `makemigrations --check --dry-run` reports missing migrations.
- Hidden 500s appear in manual route logs.
- A stale failed/blocked `agent_report.md` remains after fixes.
- `.env` or real secrets are in Git output.

## Required final report

Create or update:

```text
docs/phases/phase_11_privacy_deletion_compliance/agent_report.md
```

Use the template from `agent_report_template.md`.

The final report must include:

1. Summary of completed tickets.
2. Exact files changed/created.
3. Model/migration changes.
4. Service changes.
5. Route/template changes.
6. Tests added/changed.
7. Exact commands run and outputs summarized.
8. Boundary grep results.
9. Any blocked checks with exact cause.
10. Remaining risks/manual checks.

## Stop condition

Stop after Phase 11 is implemented and acceptance has passed or a blocker is clearly reported. Do not start Phase 12.
