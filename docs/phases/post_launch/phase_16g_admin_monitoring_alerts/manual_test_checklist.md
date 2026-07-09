# Manual Test Checklist

Run these manually when the phase changes user/admin visible behavior.

```text
Check anonymous access.
Check authenticated access.
Check admin/staff restriction.
Check form validation.
Check no debug traceback.
Check no secret/raw CV text appears.
```

## Phase 16G checks

```text
Open admin dashboards as superuser.
Confirm non-staff blocked.
Download CV only as superuser/authorized admin.
Confirm access log row created.
Trigger test alert in safe mode.
```
