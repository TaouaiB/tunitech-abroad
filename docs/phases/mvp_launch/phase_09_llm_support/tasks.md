# Phase 09 — LLM Support — Tasks

## Phase goal

Add controlled LLM support through OpenRouter for assistive features only. LLM may extract, explain, and suggest, but must never decide final fit score.

## Hard boundaries

- Do not start Phase 10 email.
- Do not add email digest, unsubscribe, or notification sending.
- Do not add privacy deletion workflows.
- Do not add deployment work.
- Do not add admin observability dashboards.
- Do not change the deterministic Phase 7 scoring contract.
- Do not call OpenRouter from Django views.
- Do not call OpenRouter from models.
- Do not call OpenRouter during normal public job search.
- Do not call France Travail live APIs.
- Do not expose CV files, CV file paths, private URLs, or raw CV text publicly.

## Architecture rules

- Views stay thin.
- Business logic goes in services.
- Celery tasks call services only.
- Models store data only and do not call external APIs.
- User job search reads local PostgreSQL only.
- Public URLs use UUID `public_id`, never internal integer IDs.
- Secrets must stay in `.env`, never committed or logged.
- Only `.env.example` may be updated.

## Ticket 09.1 — Add LLM settings and provider shell

Create a controlled LLM integration layer, for example:

```text
apps/llm/
├── apps.py
├── __init__.py
├── services/
│   ├── __init__.py
│   ├── client.py
│   ├── prompts.py
│   ├── usage.py
│   └── safety.py
├── tasks.py
├── models.py
├── admin.py
└── tests/
```

Requirements:

- Register app in `config/settings/base.py`.
- Add safe defaults to settings.
- Add `.env.example` placeholders only.
- Do not put real API keys anywhere.
- Do not print or log API keys.
- OpenRouter calls must be isolated in a service client.
- The client must support disabled mode for local tests.
- Tests must not make real network calls.

## Ticket 09.2 — Add LLM request audit model

Add a model such as `LLMRequestLog` or equivalent.

It may store:

- user
- purpose
- provider
- model name
- status
- token estimate or usage if available
- latency if available
- created_at
- safe metadata

It must not store:

- raw CV text
- CV file path
- CV private URL
- real secrets
- full API key

## Ticket 09.3 — CV assistive extraction service

Add an optional service that can suggest structured fields from already-extracted CV text.

Rules:

- It can assist extraction.
- It cannot overwrite user profile blindly.
- It cannot decide final match score.
- It must be callable from Celery/service layer only, not views.
- It must be disabled by default unless settings allow it.
- Tests use mocks/fakes only.

## Ticket 09.4 — Match explanation service

Add an assistive explanation service for existing deterministic match results.

Rules:

- It can explain why the deterministic score is high/medium/low.
- It can explain missing skills.
- It cannot change or decide the final score.
- It must rely on already-computed `MatchResult`/recommendation data.
- It must not call LLM from views.

## Ticket 09.5 — Skill/course suggestion shell

Add a controlled suggestion service for missing skills.

Rules:

- Suggestions are advisory only.
- Do not implement full recommendation marketplace.
- Do not add email sending.
- Do not add paid course integrations.

## Ticket 09.6 — Tests and boundaries

Tests must cover:

- LLM disabled mode.
- No network calls in tests.
- OpenRouter client is not called from views.
- OpenRouter client is not called from models.
- Celery tasks call services only.
- LLM cannot change final fit score.
- Logs do not include raw CV text, file path, private URL, or secrets.
- Missing API key fails safely.
- `.env.example` has placeholders only.
