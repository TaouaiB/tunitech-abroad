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

## Phase 16C checks

```text
Run parser against sample CVs.
Confirm bad name strings are rejected.
Confirm low-confidence fields require user confirmation.
Confirm no real test CV appears in git status.
```
