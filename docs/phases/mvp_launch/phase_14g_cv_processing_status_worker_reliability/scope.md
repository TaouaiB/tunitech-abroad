# Scope — Phase 14G

## In scope

1. Improve CV upload/status UX.
2. Make CV processing states understandable.
3. Add HTMX polling for status if not already robust.
4. Show clear failure and retry guidance.
5. Add worker health/queue visibility for local/admin use.
6. Add tests for CV status transitions and privacy.
7. Document local commands for Django + Redis + Celery worker.
8. Keep the existing deterministic/LLM CV parsing behavior unchanged unless a bug blocks status reliability.

## Out of scope

- New matching algorithm.
- New recommendation scoring.
- New LLM prompt design.
- Deployment automation.
- Render worker/cron setup.
- New frontend stack.
- React/Vue/SPA.
- Public CV file access.
- Resume builder or CV editor.
- Multi-CV comparison features.
