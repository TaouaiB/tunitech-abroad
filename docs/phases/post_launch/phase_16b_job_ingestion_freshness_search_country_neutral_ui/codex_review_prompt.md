# Codex Review Prompt — Phase 16B — Job Ingestion, Freshness, Search, and Country-Neutral UI Hardening

You are the strict verification and repair agent after Gemini.

Read first:

```text
docs/phases/post_launch/GLOBAL_AGENT_RULES_v1_1.md
docs/planning/post_launch/Project_Context_For_ChatGPT_v1_1.md
docs/planning/post_launch/Implementation_Roadmap_v1_1_Post_Launch.md
docs/planning/post_launch/Service_Contracts_v1_1_Quality_Services.md
docs/planning/post_launch/Database_Schema_v1_1_Quality_Admin_Monitoring.md
```

Then inspect Gemini's changes for Phase 16B only.

## Mission

Verify and repair Phase 16B: Make job supply explainable/configurable, harden freshness and search, and remove France-only public positioning.

## Review scope

```text
- diagnose 200 versus 1000 jobs
- admin-configurable ingestion target and limits
- query-level ingestion audit
- freshness/expiry hardening
- search empty/space/company/date filters
- search logging/audit
- country-neutral public UI copy
```

## What to verify strictly

```text
No future phase implementation.
No stack drift.
Views remain thin.
Business logic is in services.
Celery tasks call services only.
Models do not call external APIs.
No OpenRouter/LLM call from views.
No live external job API during user search.
Public URLs use public_id.
CV privacy is preserved.
No raw CV text or secrets in logs/tests/reports.
Migrations are minimal and safe.
Tests cover new behavior.
Admin-only features are protected.
No fake enterprise RBAC.
```

## Repair permission

You may fix in-scope defects automatically. Do not start the next phase. Do not redesign unrelated files.

## Commands

Run:

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test --settings=config.settings.local
```

Run phase-specific commands from `acceptance.md` when applicable. If a command needs production access, report the exact command and do not fake the result.

## Final report required

Use `codex_review_report_template.md`. Include pass/fail per checklist item, fixes made, remaining risks, and whether this phase is ready for senior review.

## Additional required shared reading

Before review/repair, also read:

```text
docs/phases/post_launch/shared/gemini_codex_tiebreak_policy.md
docs/phases/post_launch/shared/diagnostics_contract_policy.md
```

Codex must include an explicit `Intent-changing fixes or disagreements` section in its report. If any item is not `none`, stop for senior review.
