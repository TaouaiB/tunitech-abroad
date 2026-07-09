# Phase 14H-C — Tailwind Production Build Pipeline

## Goal
Replace the Tailwind Play CDN with a real local Tailwind build pipeline for Django static files.

This phase is about production-readiness and deployment hardening only. It must not redesign the UI, change product behavior, or introduce a frontend framework.

## Non-negotiable stack rules
- Keep Django templates.
- Keep HTMX.
- Keep Alpine.js only where already needed.
- No React, Next.js, Angular, Vue, SPA, Vite app shell, or frontend rewrite.
- No Tailwind CDN in production templates.
- Do not touch matching logic, ingestion logic, CV parsing logic, LLM logic, or deployment infrastructure beyond static asset build plumbing.

## Deliverables
- `package.json` with Tailwind build/watch scripts.
- Tailwind config scanning Django templates and Python files where Tailwind classes are generated.
- Source CSS entry file with Tailwind directives.
- Generated static CSS file committed to the repo.
- `templates/base.html` updated to load the local compiled CSS with `{% static %}`.
- Tests or assertions proving the CDN is removed and local CSS is referenced.
- Developer docs for local CSS build and deploy expectations.

## Agent rule
Work automatically through Phase 14H-C only. Do not commit. Do not deploy. Do not start Phase 14H-D or any later phase.
