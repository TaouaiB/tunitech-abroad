# Phase 16C Manifest — CV Parser Quality Framework

## Goal

Make CV parsing measurable and prevent confident garbage such as name="je me suis".

## Allowed apps/areas

```text
cvs
profiles
skills
```

## Deliverables

```text
- CVNameExtractionService
- confidence/warnings
- private CV audit corpus
- audit_cv_parser command
- parser metrics and regression loop
- correction capture foundation
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
