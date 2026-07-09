# Browser Manual Test Policy

Use browser/manual testing when a phase changes visible behavior, OAuth, forms, admin pages, dashboard pages, search pages, or email template rendering.

Minimum manual checks:

```text
anonymous public pages load
login/signup pages load
dashboard requires auth
forms show validation errors safely
HTMX partials still render if used
admin-only pages reject anonymous/non-staff users
no raw debug tracebacks in production-like mode
```

Do not block backend-only phases on full UI polish.
