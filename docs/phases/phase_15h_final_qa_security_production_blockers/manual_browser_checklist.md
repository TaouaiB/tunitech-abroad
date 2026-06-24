# Phase 15H Manual Browser Checklist

Run after automated checks pass.

## Saved jobs

- Open `/dashboard/saved-jobs/`.
- Confirm no card displays:
  - `Classified as non-IT or explicitly excluded`
  - `excluded_non_it`
  - `low_confidence`
  - `provider_blocked`
  - `validation_error`
  - `reserved`
  - `unclassified`
- Active saved jobs display normally.
- Unavailable/removed/excluded jobs are hidden or show generic `Offre indisponible`.
- Remove/unsave still works.

## Public jobs relevance

- Open `/jobs/?q=django&sort=relevance`.
- Django jobs appear before unrelated jobs.
- Open `/jobs/?q=python&sort=relevance`.
- Python jobs appear before unrelated jobs.
- Open `/jobs/?sort=relevance` with no query.
- Page falls back safely without pretending keyword relevance exists.

## Operations dashboard

- Open `/admin/operations/` as staff.
- Confirm LLM usage logs and enrichment records are clearly labelled.
- Cost/call numbers are understandable.
- `Other/unclassified` is not hiding obvious known statuses.
- Non-staff cannot access.

## User-facing internal text grep

Run:

```bash
grep -R "Classified as non-IT\|explicitly excluded\|excluded_non_it\|low relevance\|low confidence\|provider_blocked\|reserved\|unclassified" templates apps -n 2>/dev/null || true
```

Any public template/view match is a blocker.
Admin/test/docs matches may be acceptable if reviewed.
