# Phase 16A Manifest — Production Stabilization

## Goal

Fix production trust issues before product expansion.

## Allowed apps/areas

```text
accounts
core
jobs
cvs
matching
llm
```

## Deliverables

```text
- HTTPS awareness behind Caddy
- Google OAuth verified-email account linking
- robots.txt and sitemap.xml
- safe external job description rendering
- PDF magic-byte validation
- match formula correction
- LLM disabled-result cleanup
- homepage real latest jobs
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
