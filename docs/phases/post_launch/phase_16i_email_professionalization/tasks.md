# Phase 16I — Email Professionalization — tasks.md

## Goal

Professionalize transactional/admin emails after recommendation and intelligence quality are stable.

## In-scope apps/areas

```text
notifications
allauth template overrides
email rendering services
digest service if enabled
admin alert email templates
```

## Tickets

### TTA-16I-001 — Verification email template

Priority: P0  
Type: email/template/test

Acceptance:

```text
French professional verification email exists.
Plain-text fallback exists.
Brand is TuniAtlas.
No France-only public marketing copy.
No secrets/debug data.
```

### TTA-16I-002 — Password reset email template

Priority: P0  
Type: email/template/test

Acceptance:

```text
French professional password reset email exists.
Plain-text fallback exists.
Secure reset link behavior unchanged.
No secrets/debug data.
```

### TTA-16I-003 — Admin alert email templates

Priority: P0  
Type: email/template/service/test

Acceptance:

```text
Admin alert emails summarize severity, type, counts, and recommended action.
No raw CV text.
No secrets.
No private file paths.
Recipient comes from ADMIN_ALERT_EMAIL.
```

### TTA-16I-004 — Optional CV parsed notification

Priority: P1  
Type: email/service/template/test

Acceptance:

```text
Only sent if feature enabled and user has verified email/consent where needed.
Does not include raw extracted personal data beyond safe summary.
Links user to dashboard/profile confirmation.
```

### TTA-16I-005 — Weekly digest gate and template

Priority: P1  
Type: email/service/template/test

Acceptance:

```text
Weekly digest remains disabled unless recommendation quality is acceptable.
Only verified opted-in active users receive digest.
Digest reads stored recommendations, not heavy live recomputation.
Unsubscribe/preferences footer exists.
Plain-text fallback exists.
```

## Out of scope

```text
No marketing automation platform.
No complex email campaign builder.
No digest before recommendation quality is acceptable.
```
