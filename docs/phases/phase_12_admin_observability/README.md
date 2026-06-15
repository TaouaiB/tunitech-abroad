# Phase 12 — Admin Operations and Observability

## Purpose

Phase 12 makes TuniTech Abroad operable through Django Admin and a lightweight health endpoint.

This phase is not UI polish, deployment, payments, recruiters, or new product features. It is operational visibility for the MVP that already exists.

## Source of truth

Use the planning documents in `docs/planning/` plus current code. Key phase scope:

- Phase 12: admin operations and observability.
- Django Admin is acceptable for MVP.
- Admin must monitor users, CVs, jobs, ingestion, skills, matches, recommendations, LLM, and email events.
- Health checks must cover database and Redis.
- Services own business logic. Views/admin actions/tasks must delegate.

## Folder contents

```text
docs/phases/phase_12_admin_observability/
├── README.md
├── tasks.md
├── prompt.md
├── acceptance.md
├── agent_report_template.md
├── codex_verify_prompt.md
└── preflight.md
```

## Required order

1. Baha must commit Phase 11 first.
2. Baha must ensure PostgreSQL is reachable before giving this to the agent.
3. Gemini/Antigravity implements Phase 12 only.
4. Gemini must run PostgreSQL-backed tests, not SQLite-only tests.
5. Codex verifies and may repair Phase 12 only.
6. Baha reruns final acceptance locally before commit.

## Important lesson from Phase 11

The agent must not claim PASS if PostgreSQL tests were blocked. A SQLite smoke test can be mentioned as extra evidence only, never as final acceptance.

The final report must clearly distinguish:

- `PASS`: PostgreSQL-backed acceptance ran and passed.
- `BLOCKED`: PostgreSQL, Redis, Docker/Podman, or permissions blocked required acceptance.
- `FAIL`: code/tests ran and failed.

## Phase boundary

Do not start Phase 13 polish or Phase 14 deployment. Do not redesign public UI. Do not add external monitoring SaaS. Do not add Prometheus/Sentry unless explicitly requested later. This phase is Django Admin + internal service health only.
