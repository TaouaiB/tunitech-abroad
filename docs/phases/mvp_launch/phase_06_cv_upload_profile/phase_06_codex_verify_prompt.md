# Phase 6 — Codex Verification/Fix Prompt

Read AGENTS.md first.

You are the strict verification/fix agent after Gemini implemented Phase 6.

Review Phase 6 only. Fix only defects inside Phase 6 scope. Do not start Phase 7.

Read:

- `docs/phases/phase_06_cv_upload_profile/tasks.md`
- `docs/phases/phase_06_cv_upload_profile/prompt.md`
- `docs/phases/phase_06_cv_upload_profile/acceptance.md`
- `docs/phases/phase_06_cv_upload_profile/agent_report.md`

## Hard boundary

Do not create or implement:

- matching
- quick match
- fit scoring
- recommendations
- saved jobs
- OpenRouter/LLM calls
- email digest
- unsubscribe
- privacy/account deletion beyond CV deletion
- OCR
- public CV downloads
- Phase 7+ features

Do not commit, merge, or push.

## Verification checklist

1. Check `git status --short` and diff scope.
2. Confirm changes are limited to Phase 6 scope.
3. Confirm `CVUpload.objects` excludes soft-deleted CVs.
4. Confirm `CVUpload.all_objects` is not used in normal user views.
5. Confirm one active CV per user is enforced at DB level.
6. Confirm CV files are private and not rendered with `file.url` in templates.
7. Confirm no public route serves CV files.
8. Confirm upload validation rejects non-PDF and oversized files.
9. Confirm consent is required before upload.
10. Confirm upload deactivates previous active CV.
11. Confirm upload enqueues parse task after transaction commit.
12. Confirm Celery task calls parsing service only.
13. Confirm parser aborts safely for deleted CVs.
14. Confirm text extraction handles too-little-text PDFs.
15. Confirm deterministic extraction does not invent complex experience/education.
16. Confirm extracted skills go through `SkillNormalizerService`.
17. Confirm `ProfileSkill` creation is idempotent.
18. Confirm CandidateProfile prefill does not overwrite user-entered non-empty fields.
19. Confirm profile completeness updates deterministically.
20. Confirm CV deletion soft-deletes row and removes physical file where possible.
21. Confirm users cannot view/delete another user's CV.
22. Confirm LLM service is disabled shell only and makes no network call.
23. Confirm no OpenRouter imports/calls.
24. Confirm no matching/recommendations/saved jobs code exists.
25. Confirm no wrong `task.md`, no `__pycache__`, no pyc, no sqlite DB, no celerybeat files.
26. Confirm no red Pyright/Antigravity diagnostics remain.

## Required commands

Run:

```bash
source .venv/bin/activate
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py migrate --settings=config.settings.local
python manage.py seed_skills --settings=config.settings.local
python manage.py seed_job_sources --settings=config.settings.local
python manage.py ingest_job_fixtures apps/jobs/fixtures/france_travail_sample_jobs.json --settings=config.settings.local
python manage.py test apps.cvs --settings=config.settings.local
python manage.py test apps.profiles --settings=config.settings.local
python manage.py test --settings=config.settings.local
```

Then run:

```bash
find . -type d -name "__pycache__" -print
find . -name "*.pyc" -print
find . -maxdepth 4 -name "task.md" -print
find . -maxdepth 3 -name "*.sqlite3" -print
find . -maxdepth 3 -name "celerybeat-schedule*" -print
git status --short
git diff --stat
```

Fix only real Phase 6 defects. Do not hide failures by deleting meaningful tests.

If an older phase boundary test incorrectly rejects legal Phase 6 `apps.cvs` or dashboard CV/profile pages, update only that obsolete assertion.

Update `docs/phases/phase_06_cv_upload_profile/agent_report.md` honestly with:

- defects found
- fixes made
- exact test results
- git status
- diff stat
- confirmation no Phase 7 work
- confirmation no red diagnostics remain
