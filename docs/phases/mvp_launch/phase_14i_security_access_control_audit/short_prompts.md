# Phase 14I Short Prompts

## Short Gemini/Antigravity prompt

```text
Read AGENTS.md and docs/phases/phase_14i_security_access_control_audit/*.md. Implement Phase 14I only: Security and Access Control Audit. Create docs/audits/security_access_matrix.md and docs/audits/security_findings_14i.md. Add/fix tests for auth gates, two-user IDOR, CV privacy, admin boundaries, HTMX ownership, POST/CSRF safety, public_id routing, external-call isolation, and secret/log/template leaks. Fix only security/access-control issues inside this phase. Do not deploy, commit, redesign UI, add features, change stack, or start Phase 14J. Run all acceptance checks and security greps. Final verdict must be FAIL or BLOCKED_HUMAN_SECURITY_SIGNOFF until Baha completes manual Chrome/admin signoff.
```

## Short Codex verification prompt

```text
Start from Warp with codex-tunitech. Read AGENTS.md and docs/phases/phase_14i_security_access_control_audit/*.md. Verify Gemini's Phase 14I implementation only. Confirm audit docs exist and are specific, tests cover private route auth, two-user IDOR, CV privacy, admin boundaries, HTMX ownership, dangerous GET mutation safety, public_id rules, external-call isolation, and secret greps. Run PostgreSQL/Redis-backed checks: manage.py check, makemigrations --check --dry-run, full tests --parallel 1, git diff --check, and all security greps. Fix only Phase 14I security defects if needed, rerun checks, do not commit/deploy/start Phase 14J. Final verdict is FAIL if anything fails; otherwise BLOCKED_HUMAN_SECURITY_SIGNOFF until Baha completes manual Chrome/admin signoff. Do not write PASS without documented human signoff.
```
