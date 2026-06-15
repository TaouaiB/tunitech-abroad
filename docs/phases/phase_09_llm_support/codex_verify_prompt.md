# Phase 09 — Codex Verification Prompt

Read `AGENTS.md` first.

Review Phase 09 strictly.

Current phase:
Phase 09 — LLM Support.

Do not start Phase 10.
Do not commit.
Do not push.

## Review checklist

Check for:

- wrong stack usage
- OpenRouter calls from views
- OpenRouter calls from models
- LLM deciding final score
- network calls in tests
- real API keys/secrets
- raw CV text stored/logged unsafely
- CV file path/private URL exposure
- `CVUpload.all_objects` misuse
- email/unsubscribe work outside Phase 10
- live France Travail calls
- logic in views instead of services
- Celery tasks containing business logic
- missing tests
- `Found 0 test(s)`
- stale or dishonest `agent_report.md`
- junk files

## Commands

```bash
source .venv/bin/activate

python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py migrate --settings=config.settings.local
python manage.py test apps.llm --settings=config.settings.local
python manage.py test --settings=config.settings.local

grep -R "objects\.create_user" apps --exclude-dir="__pycache__" -n || echo "OK no objects.create_user"
grep -R "OpenRouter\|openrouter" apps --exclude-dir="tests" -n
grep -R "send_mail\|email_digest\|unsubscribe" apps/llm apps/cvs apps/jobs apps/matching apps/recommendations apps/dashboard --exclude-dir="tests" -n || echo "OK no email phase work"
grep -R "CVUpload.all_objects" apps/llm --exclude-dir="tests" -n || echo "OK no all_objects in LLM runtime"
find . -type d -name "__pycache__" -print
find . -name "*.pyc" -print
find . -maxdepth 4 -name "task.md" -print
```

If issues are found:

1. Fix only the issue.
2. Add regression tests.
3. Re-run Phase 09 tests.
4. Re-run full suite.
5. Repeat up to 5 loops.

Final output:

- approved/not approved
- blockers fixed
- blockers remaining
- test counts
- git status
- diff stat
