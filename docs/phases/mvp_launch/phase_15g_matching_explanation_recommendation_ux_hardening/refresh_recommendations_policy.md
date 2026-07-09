# Phase 15G Refresh Recommendations Policy

## User-facing behavior

Add a button:

```text
Actualiser mes recommandations
```

The button should allow the authenticated candidate to recompute recommendations after CV/profile/skills change.

## Architecture

Allowed flow:

```text
POST view
→ recommendation service or Celery task
→ local PostgreSQL reads
→ redirect with message
```

Forbidden:

```text
POST view
→ OpenRouter call directly
POST view
→ France Travail API
Template
→ business logic
```

## Route guidance

Use existing app/URL style. Suggested route if no better one exists:

```text
POST /dashboard/recommendations/refresh/
```

Name suggestion:

```text
recommendations:refresh
```

## Tests

- Authenticated POST calls service or queues task.
- Anonymous request is redirected to login.
- GET is not allowed or safely redirects without mutation.
- Button includes CSRF token.
- No provider/client import in view.
