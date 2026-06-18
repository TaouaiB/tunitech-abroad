# Phase 14J — Admin Operations and Analytics

## Status

Phase 14J starts only after Phase 14I Security and Access Control Audit has been accepted with manual Chrome/admin signoff.

## Goal

Make Django Admin and lightweight admin operations useful enough to operate TuniTech Abroad safely after deployment.

This phase is not about visual polish for candidates. It is about operational control, admin visibility, failure detection, and safe admin actions.

## Product context

TuniTech Abroad now has users, OAuth, profiles, CV upload/parsing, jobs, ingestion, matching, recommendations, saved jobs, LLM usage, email preferences, unsubscribe tokens, deletion flows, health checks, Celery, Beat, PostgreSQL, and Redis.

The next risk is not missing product features. The risk is operating blind:

- ingestion silently stops
- CV parsing fails and nobody notices
- recommendations go stale
- LLM cost grows without visibility
- emails fail silently
- deletion requests are not processed
- admin screens expose sensitive fields
- admin actions duplicate business logic instead of calling services/tasks

## Phase boundary

Allowed:

- improve Django Admin model registrations
- add admin list_display/search/filter/readonly fields
- add safe admin actions that call services or enqueue tasks
- add admin-only operations/analytics pages using Django templates
- add lightweight operational metrics service
- add tests for admin access, sensitive field handling, service delegation, and analytics numbers
- add docs for admin operations

Forbidden:

- no React/Next/Vue/Angular/Vite
- no custom SPA admin dashboard
- no deployment work
- no candidate-facing UI redesign
- no payment/recruiter/training-center features
- no new product matching logic
- no LLM scoring changes
- no France Travail calls from public search
- no raw CV text exposure
- no public CV file links
- no secrets in admin, logs, docs, tests, reports, or templates

## Required output

- improved admin operations for existing MVP systems
- `docs/admin/admin_operations_14j.md`
- `docs/admin/admin_analytics_14j.md`
- tests proving admin safety and delegation
- no deployment
- no commit by agent

## Final verdict rule

The agent/Codex verifier must not write PASS before Baha manually checks Django Admin in Chrome.

Allowed final verdicts before manual signoff:

- `FINAL_VERDICT: FAIL`
- `FINAL_VERDICT: BLOCKED_HUMAN_ADMIN_SIGNOFF`
