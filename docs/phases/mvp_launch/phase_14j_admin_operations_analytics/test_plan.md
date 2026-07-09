# Phase 14J Test Plan

## Admin access tests

- anonymous denied `/admin/`
- normal authenticated user denied `/admin/`
- staff/superuser allowed `/admin/`
- anonymous denied admin operations page if added
- normal authenticated user denied admin operations page if added
- staff/superuser allowed admin operations page if added

## Sensitive field tests

- `CVUploadAdmin.list_display` does not include `file`
- `CVParsedDataAdmin.list_display` does not include `raw_text`
- unsubscribe token admin list does not include raw `token`
- LLM admin list displays do not include API keys/secrets/raw payloads

## Admin action tests

For each action added:

- action calls service/task via mock/patch
- action does not call external client directly
- action handles empty queryset safely
- action messages result to admin

## Metrics tests

If `AdminMetricsService` is added:

- returns stable dictionary keys
- counts are deterministic with fixture data
- no key/value contains secret-looking names or raw text
- handles missing optional app/model data safely

## Docs tests

- `docs/admin/admin_operations_14j.md` exists and non-empty
- `docs/admin/admin_analytics_14j.md` exists and non-empty
