# Browser Checklist — Phase 16C — CV Parser Quality Framework

Use this only for browser-visible changes. Do not introduce a heavy browser test framework unless already present.

## Basic browser checks

```text
Homepage loads.
Job search loads.
Job detail loads by UUID public_id.
Dashboard requires login.
Admin pages require staff/superuser.
Forms show validation errors safely.
No raw exception page in production-like settings.
Mobile viewport does not have catastrophic breakage.
```

## Notes

For backend-only phases, record `not applicable` with reason in the agent report.
