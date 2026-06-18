# Phase 14J Gemini / Antigravity Prompt

Read `AGENTS.md` first.

Then read every file in:

```text
docs/phases/phase_14j_admin_operations_analytics/
```

Implement **Phase 14J — Admin Operations and Analytics only**.

## Mission

Make Django Admin and lightweight admin operations useful enough to operate TuniTech Abroad safely after deployment.

You must inspect existing admin registrations, services, tasks, models, URLs, and tests before changing code.

## Required deliverables

Create or update:

```text
docs/admin/admin_operations_14j.md
docs/admin/admin_analytics_14j.md
```

Implement narrowly scoped improvements for:

- admin list displays
- search fields
- filters
- readonly fields
- sensitive field exclusion
- safe admin actions that delegate to services/tasks
- optional lightweight admin-only operations metrics page/service if appropriate
- tests for admin access, metrics, sensitive-field protection, and action delegation

## Hard boundaries

Do not deploy.
Do not commit.
Do not start Phase 14K or Phase 14L.
Do not redesign candidate-facing UI.
Do not add product features.
Do not add React, Next.js, Vue, Angular, Vite, FastAPI, MongoDB, SQLAlchemy, or SPA architecture.
Do not expose CV files, raw CV text, raw unsubscribe tokens, LLM payloads, secrets, API keys, or OAuth tokens.
Do not call OpenRouter from views/admin actions.
Do not call France Travail from public search or admin actions directly. Existing ingestion services/tasks may be referenced.
Admin actions must call services or enqueue existing tasks, not duplicate business logic.

## Required checks

Run:

```bash
source .venv/bin/activate

python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test --settings=config.settings.local --parallel 1
git diff --check
```

If admin templates/static changed, run:

```bash
npm run css:build
python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
```

Run security greps from `regression_security_checks.md`.

## Reporting

Final report must include:

- changed files
- admin coverage improved
- admin actions added/changed
- metrics added
- sensitive fields checked
- tests added/changed
- full command outputs
- risks and manual checks needed
- final verdict

Allowed final verdict before Baha manual admin browser signoff:

```text
FINAL_VERDICT: FAIL
```

or

```text
FINAL_VERDICT: BLOCKED_HUMAN_ADMIN_SIGNOFF
```

Never write PASS before Baha completes manual Django Admin signoff.
