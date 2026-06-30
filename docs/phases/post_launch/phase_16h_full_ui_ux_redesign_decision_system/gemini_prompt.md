# Gemini Prompt — Phase 16H — Full UI/UX Redesign and Decision System

Read first:

```text
docs/phases/post_launch/GLOBAL_AGENT_RULES_v1_1.md
docs/planning/post_launch/Project_Context_For_ChatGPT_v1_1.md
docs/planning/post_launch/Implementation_Roadmap_v1_1_Post_Launch.md
docs/planning/post_launch/PRD_v1_1_Product_Intelligence_Quality.md
docs/planning/post_launch/Service_Contracts_v1_1_Quality_Services.md
docs/planning/post_launch/Database_Schema_v1_1_Quality_Admin_Monitoring.md
```

Then read this phase folder:

```text
docs/phases/post_launch/phase_16h_*/tasks.md
docs/phases/post_launch/phase_16h_*/acceptance.md
docs/phases/post_launch/phase_16h_*/phase_manifest.md
docs/phases/post_launch/phase_16h_*/manual_test_checklist.md
docs/phases/post_launch/phase_16h_*/browser_checklist.md
```

## Mission

Reserved full public/dashboard UI rebuild after backend intelligence is stable. Not detailed yet.

## Phase scope

```text
- reserve full redesign phase
- no implementation now
- future separate UX strategy/wireframes/component docs required
```

## Special instruction for Phase 16H

Do not implement the full UI/UX redesign from this prompt. This phase is intentionally reserved. Only read existing UI, produce a UI discovery/report, and stop unless Baha provides a separate UI/UX redesign brief.


## Required architecture behavior

```text
Views stay thin.
Services own business logic.
Celery tasks call services only.
Models do not call external APIs.
No LLM calls from views.
No France Travail live API calls during user search.
Public routes use UUID public_id.
CV files stay private.
No secrets printed.
```

## Required commands before final report

Run the relevant subset and explain if a command is unavailable:

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test --settings=config.settings.local
```

## Final report required

Use `agent_report_template.md`. Include:

```text
completed tickets
files changed
migrations created
commands run
final test results
manual/browser checks
risks and follow-ups
phase-boundary confirmation
```

## Additional required shared reading

Before coding, also read:

```text
docs/phases/post_launch/shared/gemini_codex_tiebreak_policy.md
docs/phases/post_launch/shared/diagnostics_contract_policy.md
```
