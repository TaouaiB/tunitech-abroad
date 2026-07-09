# Phase 16A — Production Stabilization — tasks.md

## Goal

Fix production trust, security, and correctness issues before product expansion.

## Execution order inside this phase

Do tickets 16A-001 through 16A-005 first as a blocking security/correctness sub-batch. Do not move to 16A-006 through 16A-008 until those pass tests/manual checks.

## In-scope apps/areas

```text
config/settings/production.py
accounts/allauth adapter/services
core SEO/robots/sitemap
jobs templates/rendering
cvs upload validation
matching scoring services
llm disabled behavior
homepage latest jobs
```

## Tickets

### TTA-16A-001 — Production HTTPS awareness

Priority: P0  
Type: deployment/security/config

Implement production settings through Git, not manual server editing:

```python
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https"
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

Acceptance:

```text
Django recognizes HTTPS behind Caddy.
OAuth callback URLs are generated as https://tuniatlas.com/...
Secure cookies enabled in production settings.
Local settings are not broken.
No secrets printed or committed.
```

### TTA-16A-002 — Google OAuth verified-email linking

Priority: P0  
Type: auth/security/service/test

Fix duplicate-account behavior for same verified email across email/password and Google OAuth.

Acceptance:

```text
Existing verified local email can safely link Google social login.
Unverified provider email does not silently link.
No duplicate user is created for same verified email.
Clear user message when linking is unsafe.
Logic belongs in accounts adapter/service layer, not templates.
Tests cover verified collision, unverified collision, and new OAuth user.
```

### TTA-16A-003 — robots.txt and sitemap.xml

Priority: P0  
Type: SEO/backend/test

Acceptance:

```text
/robots.txt returns 200.
/sitemap.xml returns 200.
No dashboard/admin/private/CV URLs exposed in sitemap.
Canonical host is tuniatlas.com.
Tests or smoke checks verify both routes.
```

### TTA-16A-004 — Safe external job description rendering

Priority: P0  
Type: security/frontend/test

Remove unsafe rendering of external job descriptions.

Acceptance:

```text
No arbitrary HTML from external source renders as trusted HTML.
Line breaks are preserved safely.
XSS regression test covers script/img/onerror payload.
Job detail remains readable.
```

### TTA-16A-005 — PDF magic-byte validation

Priority: P0  
Type: security/privacy/backend/test

Acceptance:

```text
Fake .pdf filename with non-PDF content is rejected.
Wrong content type is rejected.
Oversized file is rejected.
Valid PDF is accepted.
File pointer is reset after validation before save/parse.
No full CV content logged.
```

### TTA-16A-006 — Match formula correction

Priority: P0  
Type: matching/service/test

Formula:

```text
technical 45%
experience 20%
role/title 15%
language 10%
location 10%
```

Acceptance:

```text
MatchScoringService uses exact 45/20/15/10/10 weights.
Location score affects final score.
LLM cannot affect final score.
Tests assert exact formula with known component values.
```

### TTA-16A-007 — LLM disabled result cleanup

Priority: P1  
Type: llm/service/test

Acceptance:

```text
LLM disabled mode returns explicit disabled result.
No fake success is recorded.
No fake extraction contaminates production data.
Usage logging remains accurate.
Tests cover LLM disabled path.
```

### TTA-16A-008 — Homepage real latest jobs

Priority: P1  
Type: frontend/service/test

Acceptance:

```text
Homepage uses real latest public jobs through service/query layer.
If no jobs exist, honest empty state is shown.
No stale static/demo job cards remain.
No homepage query calls external API.
```

## Out of scope

```text
No ingestion redesign.
No CV parser rewrite.
No skill taxonomy overhaul.
No full UI redesign.
No email template redesign.
No ML/DL.
```
