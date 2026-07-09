# Phase 10 — Email

## Purpose

This package gives Gemini/Antigravity the controlled instructions for **Phase 10 — Email** in TuniTech Abroad.

Phase 10 implements email-related MVP scope only:

- email event logging
- email batch logging
- unsubscribe tokens
- email preference management page
- idempotent email sender service
- opt-in weekly recommendation digest
- weekly digest Celery task
- digest templates
- tests and acceptance verification

## Hard boundary

Do not implement Phase 11 privacy deletion, Phase 12 admin/observability, Phase 13 polish, or Phase 14 deployment.

Do not add recruiter dashboards, paid reports, real provider integration dashboards, product polish, or production deployment work.

## Required usage

From the project root:

```bash
cd ~/Projects/tunitech-abroad
```

1. Ensure Phase 9 was committed and pushed.
2. Copy this folder into:

```text
docs/phases/phase_10_email/
```

3. Paste `docs/phases/phase_10_email/prompt.md` into Gemini/Antigravity.
4. Let the agent work through Phase 10 automatically.
5. Require the agent to run every command in `acceptance.md`.
6. Require a fresh `docs/phases/phase_10_email/agent_report.md`.
7. Send ChatGPT:
   - `agent_report.md`
   - `git status --short`
   - `git diff --stat`
   - relevant changed files or a review zip
   - complete acceptance output

## Expected app

Use the existing `apps.notifications` app if it already exists. Do not create `apps.email`.

The roadmap and service contracts use the notifications app for EmailPreference, EmailBatch, EmailEvent, EmailUnsubscribeToken, EmailSenderService, EmailPreferenceService, and WeeklyDigestService.

## Local email rule

Use Django's local/console or locmem email backend for tests and local development.

Do not require real SMTP credentials.

Do not print, log, commit, or document real secrets.

## Acceptance standard

A clean full test suite alone is not enough.

The current phase app tests must be discovered and must run. `Found 0 test(s)` is failure.

Hidden 500 responses are failure.

Stale `agent_report.md` is failure.
