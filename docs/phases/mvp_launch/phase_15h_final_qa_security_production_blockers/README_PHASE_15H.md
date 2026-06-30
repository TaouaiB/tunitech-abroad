# Phase 15H — Final QA, Security, and Production Settings Blocker Fixes

## Purpose

Phase 15H fixes the remaining blockers found during manual browser QA and pre-deployment security/production checks.

This phase is not deployment. It is the final blocker-fix phase before we can start a real deployment checklist.

## Current blockers

Manual QA blockers:

- Saved jobs page displays internal/debug classification text such as `Classified as non-IT or explicitly excluded`.
- Public jobs `Plus pertinentes` / relevance sort is not trustworthy.
- Operations dashboard metrics are confusing or inconsistent.

Security / production blockers:

- `requirements/base.txt` must keep `python-dotenv==1.2.2` because `1.0.1` was vulnerable.
- Production static files must remain consistent with Whitenoise setup and `collectstatic --settings=config.settings.production` must pass.
- Bandit reports production-code issues:
  - silent `except Exception: pass`
  - MD5 usage in LLM services
  - `urllib.request.urlopen` in OpenRouter client
  - FranceTravailClient empty-string secret default style
  - local settings `0.0.0.0` false positive needs either justification or `# nosec`.

## Non-negotiable architecture rules

- Views stay thin.
- Business logic belongs in services or presentation helpers.
- Templates must not expose internal machine/debug reasons.
- No OpenRouter calls from views/templates/models/admin display.
- No France Travail live API calls from public job search.
- Public URLs use UUID `public_id`, never internal integer IDs.
- CV files remain private.
- Do not introduce React, Next.js, Angular, FastAPI, MongoDB, SQLAlchemy, or SPA architecture.

## Definition of done

- User-facing pages never display internal classification strings.
- Saved jobs handles unavailable/excluded/non-public jobs safely.
- `Plus pertinentes` sort works and has tests.
- Operations dashboard metrics are accurate and clearly labelled.
- `pip-audit` passes.
- `bandit` has no unresolved high/medium production findings.
- Production `collectstatic` passes.
- Full Django tests pass.
- Manual browser checks pass for saved jobs, jobs sort, and operations dashboard.
