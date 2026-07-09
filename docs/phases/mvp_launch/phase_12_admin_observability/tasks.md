# Phase 12 Tasks — Admin Operations and Observability

## Phase goal

Make the system operable through Django Admin and health checks.

The MVP should be inspectable without opening a Python shell for normal operational questions:

- Are jobs ingesting?
- Which CVs failed parsing?
- Which unknown skills need review?
- Which LLM calls failed or cost too much?
- Which emails failed?
- Can staff trigger safe reprocessing actions?
- Is database/Redis health visible?

## Hard scope boundaries

Allowed:

- Django Admin registrations and actions.
- Lightweight health endpoint.
- Admin/service tests.
- Minimal service helpers required for admin actions and health checks.
- Minor model admin improvements.
- Read-only or safe retry/reprocess actions.

Forbidden:

- Phase 13 polish: public UI redesign, French copy pass, responsive layout overhaul, error pages.
- Phase 14 deployment: production settings, hosting, domain, HTTPS, worker deployment.
- New external monitoring providers.
- Live France Travail calls from public search or admin list pages.
- Direct OpenRouter calls from admin list pages.
- Admin actions that contain business logic instead of calling services/tasks.
- Admin display of full CV text, full raw profile PII, secrets, OAuth tokens, API keys.

---

## TTA-1201 — Preflight and audit current operational surface

Type: audit / safety

Tasks:

1. Read `AGENTS.md`.
2. Read this phase folder.
3. Read relevant planning docs in `docs/planning/`.
4. Run preflight from `preflight.md`.
5. Inspect existing admin modules in all apps.
6. Inspect service/task names before adding admin actions.
7. Create a short implementation checklist in `docs/phases/phase_12_admin_observability/agent_report.md` as work progresses.

Acceptance:

- Agent reports whether PostgreSQL and Redis are reachable.
- Agent does not claim PASS if Docker/PostgreSQL/Redis blocked required tests.
- No code implementation starts before auditing existing admin registrations and services.

---

## TTA-1202 — Complete admin registration coverage

Type: admin

Tasks:

Register or improve admin coverage for operational MVP models across:

- `apps.accounts`
- `apps.profiles`
- `apps.skills`
- `apps.jobs`
- `apps.cvs`
- `apps.matching`
- `apps.recommendations`
- `apps.llm`
- `apps.notifications`
- `apps.privacy`
- `apps.analytics`
- `apps.core` if `SystemSetting` or similar exists

Admin classes should include useful combinations of:

- `list_display`
- `search_fields`
- `list_filter`
- `readonly_fields`
- `date_hierarchy` where useful
- `ordering`
- `list_select_related` where useful

Privacy/security rules:

- Do not expose full CV file links publicly.
- Do not display full CV raw text in list pages.
- Do not display secrets or tokens.
- UUID `public_id` is safe for admin display; internal IDs are acceptable inside Django Admin only, but do not add public routes using integer IDs.
- Use `CVUpload.all_objects` only in admin/privacy/internal contexts where soft-deleted records must be visible.

Acceptance:

- Staff can inspect core MVP model records through admin.
- LLM request logs and email events are visible with statuses/errors.
- Failed CV parse and failed ingestion states are filterable.
- Unknown/unmatched skills are filterable/reviewable.

---

## TTA-1203 — Admin actions must delegate to services/tasks

Type: admin actions / service boundary

Tasks:

Add safe admin actions where useful. Inspect existing service/task names and call them; do not invent parallel logic.

Candidate actions:

- Requeue/reparse selected CV uploads.
- Refresh recommendations for selected users/profiles.
- Retry or reprocess selected raw job records / normalized jobs if existing services support it.
- Mark selected unmatched skills as reviewed/ignored if the model supports it.
- Trigger skill alias/canonical review through a service if needed.

Rules:

- Admin actions must be thin wrappers.
- Admin actions must call services or enqueue Celery tasks.
- Admin actions must show a clear success/error message using Django admin messages.
- Admin actions must not call OpenRouter directly.
- Admin actions must not call France Travail live except existing ingestion admin action explicitly designed for ingestion; normal public search remains local DB only.
- Long work should enqueue Celery tasks, not run synchronously in admin.

Acceptance:

- Tests prove representative admin actions call the intended service/task.
- Admin actions handle missing/invalid state gracefully.
- No large business logic appears inside `admin.py`.

---

## TTA-1204 — HealthCheckService and health endpoint

Type: service / endpoint

Tasks:

Implement or harden:

```text
apps/core/services/health.py
```

Contract:

```python
HealthCheckService.check() -> dict
```

Expected shape:

```python
{
    "status": "ok" | "degraded",
    "database": "ok" | "error",
    "redis": "ok" | "error",
}
```

Add a lightweight endpoint, preferably:

```text
/health/
```

Response:

- JSON only.
- HTTP 200 if all required checks are OK.
- HTTP 503 if database or Redis check fails.
- No secrets.
- No detailed stack traces.
- No user-specific data.

Implementation notes:

- DB check should use Django database connection/cursor.
- Redis check can use configured Django cache or Redis client already used by project.
- Handle exceptions and return safe error labels only.

Acceptance:

- Tests cover healthy DB/Redis.
- Tests cover DB failure.
- Tests cover Redis/cache failure.
- `/health/` does not require login.
- Response contains no secret values.

---

## TTA-1205 — Ingestion/job observability

Type: admin observability

Tasks:

Improve admin visibility for job ingestion/normalization/freshness models:

- Job sources.
- Raw job records.
- Normalized jobs.
- Any ingestion run/status/error models if present.
- Job freshness/status fields.
- Payload hash/source job ID visibility.

Rules:

- Admin list pages must not make live France Travail calls.
- Admin list pages must not parse huge raw payloads by default.
- If raw payload is available, keep it read-only and not in list display.
- Failed and stale records must be filterable.

Acceptance:

- Failed/stale/expired jobs are visible/filterable in admin.
- Admin can identify raw-to-normalized linkage.
- Tests verify at least one failed ingestion/normalization style record is visible/filterable or registered.

---

## TTA-1206 — CV/profile observability

Type: admin observability

Tasks:

Improve admin visibility for:

- Candidate profiles and completeness.
- Profile skills and source.
- CV uploads: parse status, errors, active/deleted state, timestamps.
- CV parsed data: safe metadata only, not full raw CV text in list display.

Rules:

- CV files remain private.
- Do not add public media URLs.
- Do not expose raw CV text in admin list pages.
- Staff-only Django Admin may inspect detail records as needed, but avoid accidental list leakage.

Acceptance:

- Failed CV parse is visible/filterable.
- Soft-deleted CVs are visible only where admin/internal view needs them.
- Admin action to reparse/requeue selected CVs delegates to task/service.

---

## TTA-1207 — Skills and unknown skill review

Type: admin observability / admin action

Tasks:

Improve review workflow for:

- Canonical skills.
- Skill aliases.
- Unmatched/unknown skill candidates.

Possible actions depending on current models:

- Mark unknown skill candidate as reviewed/ignored.
- Create alias/canonical link via service if current model supports it.
- Bulk change status only if model fields support it.

Rules:

- Do not build a full custom UI.
- Do not add external skill API.
- Do not overbuild moderation workflows.

Acceptance:

- Unknown skill candidates are searchable/filterable.
- Review status is visible.
- Representative admin action is tested.

---

## TTA-1208 — LLM, email, privacy, analytics observability

Type: admin observability

Tasks:

Improve admin visibility for:

- LLM request logs: purpose, model, status, cache/cost/token indicators if present, error summary.
- Email batches/events/unsubscribe tokens/preferences: delivery status, failures, idempotency.
- Deletion requests and consent records.
- User events/basic analytics.

Rules:

- Never display OpenRouter API key.
- Never display OAuth secrets.
- Do not add live OpenRouter retry from admin in this phase unless an existing service safely supports it.
- Do not include full private text in list displays.

Acceptance:

- Staff can filter failed LLM/email/deletion records.
- UserEvent records are searchable/filterable without PII-heavy list columns.
- Tests verify model admin registration for representative logs.

---

## TTA-1209 — Admin access tests

Type: tests

Tasks:

Add tests proving:

- Staff can access Django Admin.
- Non-staff cannot access Django Admin.
- Unauthenticated users are redirected away from admin.
- Representative registered model admin pages load.
- Representative admin actions call service/task and produce admin message.

Acceptance:

- Use PostgreSQL-backed Django tests.
- Tests must not use `objects.create_user` if project type checking rejects it; use project helper/factory or `User.objects.create(...)` with password setup if needed.
- `Found 0 test(s)` is failure.

---

## TTA-1210 — Final report and no-artifact cleanup

Type: reporting

Tasks:

Create:

```text
docs/phases/phase_12_admin_observability/agent_report.md
```

It must include:

- Completed tickets.
- Files changed.
- Commands run with exact outputs/summaries.
- PostgreSQL/Redis/Docker status.
- Tests discovered and passed.
- Any blocked commands.
- Phase boundary confirmation.
- Remaining risks.

Cleanup checks:

- No `.env` committed.
- No secrets printed.
- No `__pycache__` / `.pyc`.
- No `.sqlite3` files.
- No `celerybeat-schedule*`.
- No accidental `task.md`.
- No stale `.save` reports.

Acceptance:

- Report says PASS only if PostgreSQL-backed acceptance passed.
- Report says BLOCKED if Docker/PostgreSQL/Redis prevented required checks.
- Report says FAIL if code/tests failed after repair loops.
