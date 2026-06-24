# Phase 15I — Production Readiness and Deployment Plan

## Purpose

Phase 15I prepares TuniTech Abroad for deployment. It does **not** deploy the app and does **not** touch a real server.

This phase exists because Phase 15H fixed local blockers, but production still needs launch safeguards:

- production environment variable policy
- costly LLM automation disabled by default
- rate limiting / abuse-control plan
- monitoring and health-check plan
- backup and restore policy
- privacy final review
- legal wording final pass
- static/private media deployment rules
- email/OAuth/domain checklist
- Phase 15J deployment runbook outline
- final smoke-test checklist

## Agent workflow for this phase

Use:

1. **Gemini** for implementation.
2. **GLM 5.2** for review/verification.
3. **Codex is not used** until token refresh.
4. Final acceptance still comes from the senior architect review.

## Hard boundary

Do not deploy. Do not SSH into a server. Do not buy a domain. Do not create Cloudflare/Hetzner resources. Do not paste real secrets.

Phase 15I produces safe repo changes only.
