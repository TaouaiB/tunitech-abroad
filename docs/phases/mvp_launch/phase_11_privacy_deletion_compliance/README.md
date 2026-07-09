# Phase 11 — Privacy Deletion and Compliance Flows

## Purpose

Phase 11 hardens the MVP privacy surface for TuniTech Abroad. Implement only privacy deletion and compliance flows. Do not start Phase 12 admin/observability, Phase 13 polish, or Phase 14 deployment.

## Source of truth

Before coding, read the planning documents in `docs/planning/` if they exist in the repository, especially:

- PRD v1 — Privacy and Data Rights Requirements
- BRD v1 — Privacy and Compliance Basics
- Implementation Roadmap v1 — Phase 11
- Service Contracts v1 — Privacy Services, service dependency rules, view-to-service map
- Data Flow / Sequence Diagrams v1 — Account deletion sequence if available
- Page + URL + View Map v1 — `/privacy`, `/terms`, `/dashboard/account`, `/dashboard/settings/delete-account/`

## Phase boundary

Allowed in Phase 11:

- Privacy Policy page
- Terms page
- Consent recording hardening
- CV processing consent recording integration
- Email digest consent recording integration
- Delete CV flow hardening
- Delete account request flow
- Account deletion service and Celery task
- Cleanup tasks for expired quick matches and orphaned CV files
- Tests for privacy deletion, consent, routes, templates, and task delegation

Forbidden in Phase 11:

- No Phase 12 admin observability work except minimal model registration if needed for privacy model visibility already required by existing patterns.
- No deployment settings.
- No UI polish beyond functional templates.
- No new job ingestion features.
- No live France Travail calls during public job search.
- No OpenRouter/LLM calls from views or privacy deletion logic.
- No scoring or recommendation algorithm changes except deleting/staling user-owned data as required.
- No React, Next.js, Angular, FastAPI, MongoDB, SQLAlchemy, or SPA work.

## How to use this package

1. Copy this whole folder into the repository:

```text
docs/phases/phase_11_privacy_deletion_compliance/
```

2. Start Antigravity/Gemini in the repository root.
3. Give the model `prompt.md` as the implementation prompt.
4. The agent may work automatically through all Phase 11 tickets.
5. The agent must stop after Phase 11 and must not start Phase 12.
6. After the agent finishes, paste its `agent_report.md`, `git status --short`, changed files list, and test output back to ChatGPT for strict review.

## Required final files after implementation

The implementation should leave or create a final report at:

```text
docs/phases/phase_11_privacy_deletion_compliance/agent_report.md
```

Do not leave stale `.save` files, `__pycache__`, `.pyc`, SQLite files, review zips, or celerybeat schedule files in the working tree.
