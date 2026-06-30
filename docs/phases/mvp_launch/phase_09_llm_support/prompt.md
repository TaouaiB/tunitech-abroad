# Phase 09 — LLM Support — Gemini Implementation Prompt

Read `AGENTS.md` first.

You are implementing Phase 09 only.

## Current phase

Phase 09 — LLM Support.

## Hard boundaries

- Do not start Phase 10.
- Do not implement email digest.
- Do not implement unsubscribe.
- Do not implement privacy deletion.
- Do not implement admin observability.
- Do not implement deployment work.
- Do not change deterministic match scoring to be LLM-decided.
- Do not call OpenRouter from Django views.
- Do not call OpenRouter from models.
- Do not call OpenRouter during public job search.
- Do not call France Travail live APIs.
- Do not use React, Next.js, Angular, FastAPI, MongoDB, SQLAlchemy, or SPA architecture.
- Do not commit.
- Do not merge.
- Do not push.

## Required files to follow

- `docs/phases/phase_09_llm_support/tasks.md`
- `docs/phases/phase_09_llm_support/acceptance.md`
- `docs/phases/phase_09_llm_support/agent_report_template.md`

## Work mode

Implement all Phase 09 tickets automatically.

## Autonomous repair loop

After implementation, run the full acceptance commands from `acceptance.md`.

If any command fails:

1. Read the exact error.
2. Identify the real root cause.
3. Fix only the cause.
4. Add or update a regression test for that failure.
5. Re-run the failed command.
6. Re-run the full acceptance set.
7. Repeat until all acceptance commands pass.

Maximum repair loops: 8.

If still failing after 8 repair loops, stop and report:

- exact failing command
- traceback/error
- files changed
- what was attempted
- remaining blocker

Do not keep coding blindly.

## Test requirements

- `python manage.py test apps.llm --settings=config.settings.local` must run real tests.
- `Found 0 test(s)` is a failure.
- Full suite passing is not enough if Phase 09 app tests do not run.
- Tests must mock OpenRouter/network calls.
- No test may require real API keys.

## Static typing rules

- Do not use `User.objects.create_user` in tests.
- Use `UserModel.objects.create(...)` plus `set_password(...)`.
- Avoid `# type: ignore` unless unavoidable and explained.
- Avoid Django dynamic reverse access in tests when explicit ORM queries are clearer.

## Final cleanup

Before final report:

```bash
find . -type d -name "__pycache__" -prune -exec rm -rf {} +
find . -name "*.pyc" -delete
find . -maxdepth 4 -name "task.md" -delete
rm -f phase9_review_package.zip phase9_git_status.txt phase9_diff_stat.txt phase9_diff.patch
```

## Final report

Update:

```text
docs/phases/phase_09_llm_support/agent_report.md
```

Use `agent_report_template.md`.

Report must include exact test commands and counts.

## Final output

Show:

```bash
git status --short
git diff --stat
```

Then stop. Do not commit.
