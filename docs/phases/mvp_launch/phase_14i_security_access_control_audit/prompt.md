# Phase 14I Gemini/Antigravity Implementation Prompt

Read `AGENTS.md` first.

Then read:

```text
docs/phases/phase_14i_security_access_control_audit/README.md
docs/phases/phase_14i_security_access_control_audit/tasks.md
docs/phases/phase_14i_security_access_control_audit/acceptance.md
docs/phases/phase_14i_security_access_control_audit/preflight.md
docs/phases/phase_14i_security_access_control_audit/regression_security_checks.md
docs/phases/phase_14i_security_access_control_audit/security_access_matrix_template.md
docs/phases/phase_14i_security_access_control_audit/agent_report_template.md
```

Implement Phase 14I only: Security and Access Control Audit.

Required outputs:

```text
docs/audits/security_access_matrix.md
docs/audits/security_findings_14i.md
security/access-control tests for private route auth, two-user IDOR attempts, CV privacy, admin boundaries, HTMX ownership, dangerous GET mutations, public_id routing, and external-call isolation
security fixes inside current phase scope only
```

Hard rules:

```text
Do not deploy.
Do not commit.
Do not start Phase 14J.
Do not redesign UI.
Do not add new product features.
Do not change stack.
Do not introduce React, Next.js, Angular, Vue, FastAPI, MongoDB, SQLAlchemy, Vite, or SPA architecture.
Use Django templates, HTMX, Tailwind only.
Views stay thin.
Business logic belongs in services.
No LLM/OpenRouter calls from views.
No France Travail live calls from public search.
Public URLs use UUID public_id, never internal integer IDs.
CV files remain private.
No raw CV text in templates/admin lists.
No secrets in docs/logs/tests/reports.
```

Execution pattern:

1. Run the preflight commands.
2. Inventory routes and create the security matrix.
3. Add failing tests for gaps before fixing where practical.
4. Fix root causes within scope.
5. Rerun all acceptance checks.
6. Fill the agent report template.
7. Stop.

Final report must include:

```text
changed files
tests added/changed
commands run with results
grep results and explanations
findings fixed
remaining risks
manual browser/admin checks still required
FINAL_VERDICT: BLOCKED_HUMAN_SECURITY_SIGNOFF unless Baha already completed manual Chrome/admin signoff
```
