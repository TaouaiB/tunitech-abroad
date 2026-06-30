# Phase 16B Manifest — Job Ingestion, Freshness, Search, and Country-Neutral UI Hardening

## Goal

Make job supply explainable/configurable, harden freshness and search, and remove France-only public positioning.

## Allowed apps/areas

```text
jobs
core
analytics
```

## Deliverables

```text
- diagnose 200 versus 1000 jobs
- admin-configurable ingestion target and limits
- query-level ingestion audit
- freshness/expiry hardening
- search empty/space/company/date filters
- search logging/audit
- country-neutral public UI copy
```

## Required files in this phase folder

```text
phase_manifest.md
tasks.md
gemini_prompt.md
codex_review_prompt.md
acceptance.md
manual_test_checklist.md
browser_checklist.md
review_checklist.md
rollback_plan.md
agent_report_template.md
codex_review_report_template.md
```

## Boundary

This phase must not implement the next phase.
