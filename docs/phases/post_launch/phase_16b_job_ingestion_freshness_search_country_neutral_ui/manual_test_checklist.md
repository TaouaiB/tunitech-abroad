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

## Phase 16B checks

```text
Search with empty query.
Search with spaces only.
Search by company.
Search by exact published date.
Search by published range.
Check pagination preserves filters.
Open public pages and confirm no marketing copy says France-only.
Confirm job location can still show France as address data.
```
