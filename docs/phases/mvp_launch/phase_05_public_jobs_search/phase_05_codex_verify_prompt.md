Read AGENTS.md first.

You are the strict verification/fix agent after Gemini implemented Phase 5.

Review Phase 5 only. Fix only defects inside Phase 5 scope. Do not start Phase 6.

Read:
- docs/phases/phase_05_public_jobs_search/tasks.md
- docs/phases/phase_05_public_jobs_search/prompt.md
- docs/phases/phase_05_public_jobs_search/acceptance.md
- docs/phases/phase_05_public_jobs_search/agent_report.md

Hard boundary:
Do not create CV upload/parsing, CV models, matching, quick match, recommendations, saved jobs, OpenRouter/LLM calls, email digest, unsubscribe, privacy deletion, or deployment work.
Do not commit, merge, or push.

Phase 5 allowed scope:
- public job list/search page
- public job detail page
- JobSearchService
- JobQueryService
- JobRevalidationService safe shell
- Django forms/views/URLs/templates for jobs
- pagination, filters, local PostgreSQL search
- tests proving public_id routing and no external API during search/detail

Verification checklist:

1. Check git status and diff scope.
2. Confirm changed files are limited to Phase 5 scope: apps/jobs services/views/forms/urls/templates/tests, root URL include, phase docs, and justified phase-boundary tests only.
3. Confirm no Phase 6+ files or features exist.
4. Confirm views are thin and call services/forms.
5. Confirm JobSearchService uses local PostgreSQL only.
6. Confirm no France Travail live API call occurs during normal /jobs/ or detail page access.
7. Confirm no OpenRouter/LLM calls.
8. Confirm public job detail uses UUID public_id only.
9. Confirm no route exists for /jobs/<int:id>/ or other internal-id detail.
10. Confirm job cards and detail links use public_id, never internal id.
11. Confirm inactive/expired/removed jobs are hidden by default from search.
12. Confirm filters and pagination are tested.
13. Confirm detail 404 handling is tested.
14. Confirm JobRevalidationService is safe no-op/default and cannot break detail page.
15. Confirm optional CTAs do not implement matching/saving behavior.
16. Confirm no React/Next/FastAPI/SQLAlchemy/MongoDB/SPA code.
17. Confirm no red Pyright diagnostics remain in changed Python files.
18. Confirm no wrong file named task.md, no __pycache__, no pyc, no celerybeat files.

Run:

source .venv/bin/activate
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py migrate --settings=config.settings.local
python manage.py seed_skills --settings=config.settings.local
python manage.py seed_job_sources --settings=config.settings.local
python manage.py ingest_job_fixtures apps/jobs/fixtures/france_travail_sample_jobs.json --settings=config.settings.local
python manage.py test apps.jobs --settings=config.settings.local
python manage.py test --settings=config.settings.local

Then run:

find . -type d -name "__pycache__" -print
find . -name "*.pyc" -print
find . -maxdepth 4 -name "task.md" -print
find . -maxdepth 3 -name "*.sqlite3" -print
find . -maxdepth 3 -name "celerybeat-schedule*" -print
git status --short
git diff --stat

Fix only real Phase 5 defects.
Do not hide failures by deleting meaningful tests.
Do not edit unrelated apps unless an older phase boundary test incorrectly rejects the legal Phase 5 public jobs routes/views.

Final report:
- defects found
- fixes made
- test results
- git status
- diff stat
- confirmation no Phase 6 work
- confirmation no red diagnostics remain
