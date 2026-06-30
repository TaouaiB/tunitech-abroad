# Phase 14J Codex Verification Prompt

Start from Warp using `codex-tunitech`, not plain `codex`.

Read:

```text
AGENTS.md
docs/phases/phase_14j_admin_operations_analytics/*.md
```

Verify Gemini's Phase 14J implementation only.

## Verification scope

Confirm:

- `docs/admin/admin_operations_14j.md` exists and is specific
- `docs/admin/admin_analytics_14j.md` exists and is specific
- admin changes stay inside Phase 14J
- no candidate-facing redesign
- no deployment work
- no Phase 14K/14L work
- no forbidden stack
- normal user cannot access admin/admin operations page
- anonymous user cannot access admin/admin operations page
- staff/superuser can access admin operations page
- sensitive fields are not exposed in admin list displays
- CV raw text is not exposed
- CV direct file URL is not public
- raw unsubscribe token not listed
- LLM payloads/secrets not listed
- admin actions delegate to services/tasks, not duplicate business logic
- no OpenRouter/France Travail direct calls from views/admin actions
- metrics service/page does not expose secrets/raw personal data
- tests cover the above

## Required commands

Run exactly:

```bash
source .venv/bin/activate

python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test --settings=config.settings.local --parallel 1
git diff --check
```

If templates/static/admin page changed:

```bash
npm run css:build
python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
```

Run all greps in `regression_security_checks.md`.

## Fix policy

You may fix only Phase 14J defects.

Do not:

- commit
- deploy
- start Phase 14K
- redesign public UI
- add product features
- change stack

## Final verdict rule

If any check fails or coverage is missing:

```text
FINAL_VERDICT: FAIL
```

If all automated checks pass but Baha has not completed manual Django Admin signoff:

```text
FINAL_VERDICT: BLOCKED_HUMAN_ADMIN_SIGNOFF
```

Never write PASS before documented human admin signoff.
