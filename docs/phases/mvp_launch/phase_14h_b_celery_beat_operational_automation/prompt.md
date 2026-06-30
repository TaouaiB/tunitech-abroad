# Phase 14H-B Prompt — Celery Beat Schedule + Operational Automation

You are implementing Phase 14H-B for TuniTech Abroad.

Read first:

- `AGENTS.md`
- `docs/phases/phase_14h_b_celery_beat_operational_automation/scope.md`
- `docs/phases/phase_14h_b_celery_beat_operational_automation/tasks.md`
- `docs/phases/phase_14h_b_celery_beat_operational_automation/boundaries.md`
- `docs/phases/phase_14h_b_celery_beat_operational_automation/acceptance.md`
- `docs/phases/phase_14h_b_celery_beat_operational_automation/regression_security_checks.md`

Goal:
Populate Celery Beat operational schedules safely so the app can maintain jobs, recommendations, and privacy cleanup without manual commands.

Hard rules:

- Do not commit.
- Do not deploy.
- Do not start Tailwind build.
- Do not configure production deployment scripts.
- Do not start Phase 14H-C or Phase 14I.
- Do not change matching scoring.
- Do not call France Travail or OpenRouter from Django views.
- Do not expose CV files or raw CV text.
- Do not introduce forbidden stack choices.

Implementation requirements:

1. Replace the empty `CELERY_BEAT_SCHEDULE` with a safe schedule for existing operational tasks.
2. Schedule existing tasks only. Do not invent task names that do not exist.
3. Use conservative schedule times and names.
4. Ensure ingestion/enrichment respects existing config and budgets.
5. Add tests verifying schedule presence and task-name validity.
6. Add/update worker+beat local playbook if needed.
7. Run all required checks.
8. Produce an agent report.

Final verdict must be exactly:

- `FINAL_VERDICT: FAIL`
- `FINAL_VERDICT: BLOCKED_HUMAN_VISUAL_SIGNOFF`
