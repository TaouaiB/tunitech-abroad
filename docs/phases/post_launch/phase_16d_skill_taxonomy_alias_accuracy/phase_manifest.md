# Phase 16D Manifest — Skill Taxonomy and Alias Accuracy

## Goal

Make canonical skill handling reliable and ML-ready without building ML now.

## Allowed apps/areas

```text
skills
profiles
matching
```

## Deliverables

```text
- ProfileSkill canonical FK audit/backfill
- alias expansion for .NET/C#/Node.js/PostgreSQL etc.
- audit_skill_aliases command
- unmatched skill admin review
- matching by skill_id
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
