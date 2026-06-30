# Short Prompts — Phase 14J

## Gemini / Antigravity short prompt

```text
Read AGENTS.md and docs/phases/phase_14j_admin_operations_analytics/*.md. Implement Phase 14J only: Admin Operations and Analytics. Improve Django Admin operational visibility, safe filters/search/list displays, sensitive-field handling, service/task-delegated admin actions where useful, and optional lightweight admin-only metrics page/service. Create docs/admin/admin_operations_14j.md and docs/admin/admin_analytics_14j.md. Add tests for admin access boundaries, sensitive field protection, admin action delegation, metrics stability, and docs existence. Do not deploy, commit, redesign public UI, add product features, change stack, expose secrets/CV raw text/CV file URLs/raw tokens/LLM payloads, or start Phase 14K. Run all acceptance checks and security greps. Final verdict must be FAIL or BLOCKED_HUMAN_ADMIN_SIGNOFF until Baha completes manual Django Admin signoff.
```

## Codex verification short prompt

```text
Start from Warp with codex-tunitech. Read AGENTS.md and docs/phases/phase_14j_admin_operations_analytics/*.md. Verify Gemini's Phase 14J implementation only. Confirm docs/admin/admin_operations_14j.md and docs/admin/admin_analytics_14j.md exist and are specific. Verify admin access boundaries, sensitive field handling, admin action service/task delegation, optional metrics page/service safety, no forbidden stack, no deployment, no Phase 14K work, no public UI redesign, no OpenRouter/France Travail direct calls from views/admin actions, no secrets/CV raw text/CV file URL/raw token/LLM payload exposure. Run manage.py check, makemigrations --check --dry-run, full tests --parallel 1, git diff --check, frontend/static checks if templates changed, and all security greps. Fix only Phase 14J defects if needed, rerun checks, do not commit/deploy/start Phase 14K. Final verdict is FAIL if anything fails; otherwise BLOCKED_HUMAN_ADMIN_SIGNOFF until Baha completes manual Django Admin signoff. Do not write PASS without documented human signoff.
```
