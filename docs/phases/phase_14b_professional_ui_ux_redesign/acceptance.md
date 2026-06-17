# Phase 14B Acceptance Gates

Phase 14B is accepted only when all gates pass.

## Gate A — Automated checks

Required:

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py migrate --settings=config.settings.local
python manage.py seed_demo_data --settings=config.settings.local
python manage.py test --settings=config.settings.local
```

Must pass. No `Found 0 test(s)` fake success.

## Gate B — Visual/page coverage

The agent must browser-test homepage, jobs page, job detail, quick match, auth pages, dashboard, profile, CV, recommendations, matches, match detail if data exists, saved jobs, email preferences, account/delete, privacy/terms, and 404/500.

## Gate C — Design quality

Main pages must not look like default Django, raw admin, placeholder prototype, unstyled forms, or inconsistent card chaos.

Must have consistent design system, modern layout, readable typography, clear CTAs, mobile layout, and French-first copy.

## Gate D — Product correctness

Must preserve local PostgreSQL job search, UUID public URLs, private CV files, deterministic score authority, quick match as anonymous and LLM-free, stored/read recommendations, functional auth pages, and safe account/delete flows.

## Gate E — Security/privacy

Must not expose `.env`, secrets, OAuth credentials, API keys, tokens, CV private file URL, raw CV text, debug stack traces under DEBUG=False, URLconf dump under DEBUG=False.

## Gate F — Forbidden stack

Reject if React, Next.js, Vue, Angular, SPA architecture, Bootstrap, Material UI, or external heavy JS framework is added.

## Gate G — Report

Agent must fill `agent_report.md` with pages tested, files changed, commands run, test results, browser observations, mobile observations, remaining visual weaknesses, security checks, and no forbidden stack confirmation.
