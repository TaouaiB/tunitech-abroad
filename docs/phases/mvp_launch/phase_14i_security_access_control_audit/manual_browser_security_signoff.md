# Phase 14I Manual Browser/Admin Security Signoff

Automated tests are not enough. Baha must manually check the following before accepting Phase 14I.

## Required setup

Create or identify:

```text
User A: normal authenticated user with CV, profile, saved job, recommendation, match result
User B: normal authenticated user with separate CV/profile/saved job/match
Admin: staff/superuser account
Non-staff user: normal user
```

Run locally:

```bash
source .venv/bin/activate
python manage.py runserver --settings=config.settings.local
```

Run worker/beat only if needed for flows:

```bash
celery -A config worker -l info
celery -A config beat -l info
```

## Browser checks

### 1. Anonymous user

- Open `/dashboard/` in an incognito window.
- Open `/dashboard/cv/`.
- Open `/dashboard/recommendations/`.
- Open `/dashboard/saved-jobs/`.
- Open `/dashboard/email-preferences/`.

Expected:

```text
redirect to login or safe denial
no private data shown
```

### 2. User A cannot access User B private objects

While logged in as User A, paste known User B URLs if available:

```text
CV status URL
match detail URL
match explanation POST endpoint through UI/devtools if possible
saved job mutation endpoint if object-specific
recommendation refresh endpoint if object-specific
account deletion flow if token/object-specific
```

Expected:

```text
403/404/safe redirect
no User B data shown
no mutation to User B data
```

### 3. CV privacy

As User A:

- Open CV page.
- Inspect page source.
- Search for `/media/`, `file.url`, original storage filename, `raw_text`, `extracted_text`.
- Confirm no direct downloadable CV link exists unless it is a protected view with owner check.

Expected:

```text
no public file URL
no raw extracted CV text rendered
```

### 4. Admin boundary

- Log in as normal non-staff user and open `/admin/`.
- Log in as staff/superuser and open `/admin/`.
- Inspect CV, LLM, email, OAuth-related admin list pages.

Expected:

```text
normal user denied
admin allowed
admin list pages do not expose real secrets/raw CV text/full tokens
```

### 5. Dangerous GET mutation smoke

Try opening mutation-looking URLs directly with GET where possible:

```text
save/unsave job
delete CV
refresh recommendations
generate match explanation
email preference update
delete account request
```

Expected:

```text
GET does not mutate state
POST required
CSRF enforced
```

### 6. Public job search isolation

Open `/jobs/` and search.

Expected:

```text
search works from local PostgreSQL
no live France Travail call appears in logs for normal search
```

## Manual signoff result

Record in `docs/audits/security_findings_14i.md`:

```text
Manual signoff date:
Tester:
Browser:
Anonymous route checks: PASS/FAIL
Two-user IDOR checks: PASS/FAIL
CV privacy source inspection: PASS/FAIL
Admin boundary checks: PASS/FAIL
Dangerous GET mutation checks: PASS/FAIL
Public search external-call isolation: PASS/FAIL
Notes:
```

Until this is done, Phase 14I verdict remains:

```text
BLOCKED_HUMAN_SECURITY_SIGNOFF
```
