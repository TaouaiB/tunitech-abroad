# Phase 14I Tasks — Security and Access Control Audit

## Scope

Audit, test, and fix security/access-control defects inside the current MVP only.

Do not redesign UI. Do not deploy. Do not add new product features. Do not start Phase 14J.

---

## TTA-14I-01 — Build route and access matrix

Create:

```text
docs/audits/security_access_matrix.md
```

The matrix must list each relevant route with:

```text
route
view name
method(s)
authentication required?
owner-only required?
staff/superuser required?
public_id or internal id used?
mutation?
CSRF required?
service called
risk category
existing test coverage
result: OK / FIXED / NEEDS_FOLLOW_UP
```

Minimum route groups:

```text
public pages
allauth/account pages
dashboard pages
CV routes and status polling
profile routes
recommendation routes and refresh endpoints
matching routes and explanation endpoints
saved jobs routes
email preference routes
privacy/delete-account routes
admin routes
health route
HTMX partial endpoints
```

Acceptance:

- Matrix exists.
- Matrix identifies private owner-only resources.
- Matrix identifies all mutation endpoints.
- Matrix flags routes still needing human browser verification.

---

## TTA-14I-02 — Anonymous/authenticated route protection tests

Add or improve tests proving:

```text
anonymous users cannot access dashboard/private routes
authenticated normal users cannot access admin
inactive users do not retain private access where Django auth should block them
logout clears private access
public pages remain public
```

Acceptance:

- Tests cover dashboard, CV, profile, recommendations, matches, saved jobs, email preferences, account/privacy private pages.
- Public pages still return expected public responses.

---

## TTA-14I-03 — IDOR and ownership tests

Add tests with at least two users:

```text
user A cannot view user B's CV status
user A cannot delete user B's CV
user A cannot view user B's match detail
user A cannot generate/explain user B's match
user A cannot view or mutate user B's saved jobs
user A cannot alter user B's email preferences
user A cannot trigger user B's recommendation refresh
user A cannot access or trigger user B's account deletion flow
```

Expected behavior may be 403, 404, or safe redirect, but it must not leak object existence or private data.

Acceptance:

- Two-user IDOR tests exist.
- Ownership is checked before private reads and before all mutations.
- HTMX endpoints have the same ownership rules as normal views.

---

## TTA-14I-04 — CV privacy audit and tests

Verify and test:

```text
CV files are not publicly served by template links
file.url is not exposed in templates
raw_text/extracted_text is not rendered to users
soft-deleted CVs are excluded from normal CVUpload.objects paths
CVUpload.all_objects is used only where justified: admin/privacy/deletion/internal task/reparse flows
owner checks exist for CV status and delete
invalid/non-PDF uploads are rejected
oversize uploads are rejected
empty/unreadable PDF handled safely
filenames are sanitized or not trusted
```

Acceptance:

- Tests prove deleted CV is not used by matching/recommendations/profile flows where applicable.
- Tests prove private CV pages do not expose direct media URLs.
- Greps for `file.url`, `raw_text`, and `extracted_text` are reviewed, and every remaining hit is documented as safe or fixed.

---

## TTA-14I-05 — Public ID and integer ID audit

Audit URL patterns, forms, templates, redirects, and HTMX attributes.

Rules:

```text
Public job detail uses UUID public_id.
Public match detail uses UUID public_id.
CV status/delete uses UUID public_id or signed token, not raw pk.
No user-owned private object should be addressed by raw integer ID in user-facing routes/forms unless protected by a signed token and ownership check.
Internal integer IDs may remain in Django Admin and internal service code.
```

Acceptance:

- `grep -R "<int:" apps templates config -n` reviewed.
- Remaining integer routes are admin/internal-only or documented safe.
- Tests prove integer-ID public routes do not exist for jobs/matches/CVs.

---

## TTA-14I-06 — POST, CSRF, and dangerous GET mutation audit

Verify:

```text
state-changing actions use POST
CSRF protection remains enabled
GET requests do not delete, save, unsave, refresh, trigger match generation, trigger LLM explanation, alter preferences, or request account deletion
forms include csrf_token where needed
HTMX POSTs include CSRF token/header via existing base setup
```

Acceptance:

- Tests exist for dangerous GET requests returning safe response without mutation.
- Mutation views use POST-only patterns.
- CSRF is not disabled except in justified internal-only cases. Any exception must be documented.

---

## TTA-14I-07 — External-call isolation audit

Verify:

```text
No OpenRouter/LLM calls from Django views.
No France Travail client calls from public search/list view or templates.
No live France Travail calls during normal /jobs/ search.
No external API calls from models.
Celery tasks call services only.
```

Acceptance:

- Grep results are documented.
- Any violations are fixed.
- Tests or import-level checks prevent future view-level OpenRouter/France Travail regressions.

---

## TTA-14I-08 — Admin/staff boundary audit

Verify:

```text
non-staff users cannot access /admin/
staff access behaves through Django Admin only
superuser-only operations remain superuser-only where appropriate
admin list displays do not expose raw CV text, secrets, API keys, OAuth tokens, unsubscribe token raw values, or full LLM payloads unnecessarily
admin actions call services when mutating business data
```

Acceptance:

- Tests cover non-staff admin denial.
- Admin list_display/search/filter choices are reviewed for sensitive data exposure.
- Findings documented in security findings report.

---

## TTA-14I-09 — Secrets and log safety audit

Audit:

```text
.env is gitignored
.env.example contains variable names only
settings read secrets from environment
no real keys in code/docs/tests/reports
logs do not print full CV raw text
logs do not print OpenRouter/France Travail/OAuth secrets
error pages do not expose secrets under production settings
```

Acceptance:

- `git diff` secret grep passes.
- Any suspicious matches are reviewed and documented.
- `.env` remains untracked.

---

## TTA-14I-10 — Fix blockers inside scope only

Fix only security/access-control defects found by the audit.

Allowed fixes:

```text
add missing login_required/auth mixins
add owner filters
switch raw pk route to public_id/signed token
change unsafe GET mutation to POST
move misplaced business/security logic into service
remove direct file URL display
remove sensitive admin list fields
add tests
add audit docs
```

Forbidden fixes in this phase:

```text
new product features
admin analytics dashboard
visual redesign
deployment changes
new external integrations
new country support
LLM feature expansion
matching formula redesign except to remove data leak/security issue
```

---

## TTA-14I-11 — Final security findings report

Create:

```text
docs/audits/security_findings_14i.md
```

Required sections:

```text
summary
files changed
routes audited
tests added
findings fixed
findings accepted as safe with reason
remaining risks
manual browser/admin signoff checklist
commands run
final agent verdict
```

Acceptance:

- Findings report is specific, not vague.
- Every grep warning is either fixed or explained.
- Remaining risks are clear and not hidden.
