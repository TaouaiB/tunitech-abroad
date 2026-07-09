Read AGENTS.md first.

You are the strict verification/fix agent after Gemini implemented Phase 7.

Review Phase 7 only. Fix only defects inside Phase 7 scope. Do not start Phase 8.

Read:
- docs/phases/phase_07_matching_quick_match/tasks.md
- docs/phases/phase_07_matching_quick_match/prompt.md
- docs/phases/phase_07_matching_quick_match/acceptance.md
- docs/phases/phase_07_matching_quick_match/agent_report.md

Hard boundary:
Do not create recommendations, saved jobs, recommendation ranking/storage, OpenRouter/LLM calls, match explanation endpoint, email digest, unsubscribe, privacy/account deletion, or deployment work.
Do not commit, merge, or push.

Verification checklist:

1. Check git status and diff scope.
2. Confirm changed files are limited to Phase 7 scope.
3. Confirm views are thin and call services/forms.
4. Confirm MatchScoringService is deterministic and pure.
5. Confirm final fit score uses the required formula and clamps 0..100.
6. Confirm required skills affect technical score more than optional skills.
7. Confirm missing required skills create risk flags.
8. Confirm French level missing creates risk flag where relevant.
9. Confirm profile signals do not reduce score.
10. Confirm MatchResult stores profile/job snapshots.
11. Confirm snapshots contain no raw CV text, CV file path, or CV file URL.
12. Confirm MatchResult detail is owner-protected.
13. Confirm no route uses internal integer id for match/job detail or match creation.
14. Confirm job detail match actions use job.public_id only.
15. Confirm QuickMatchSession stores hashed session/IP only, never raw values.
16. Confirm quick match does not require login.
17. Confirm quick match expires after 24 hours.
18. Confirm quick match rate limit works and is tested.
19. Confirm no OpenRouter import or LLM call exists.
20. Confirm no France Travail live API call occurs.
21. Confirm no recommendations/saved jobs code exists.
22. Confirm no Phase 8 files/features exist.
23. Confirm no wrong file named task.md, no __pycache__, no pyc, no sqlite DB, no celerybeat files.
24. Confirm no red Pyright/Antigravity diagnostics remain.

Run:

source .venv/bin/activate
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py migrate --settings=config.settings.local
python manage.py seed_skills --settings=config.settings.local
python manage.py seed_job_sources --settings=config.settings.local
python manage.py ingest_job_fixtures apps/jobs/fixtures/france_travail_sample_jobs.json --settings=config.settings.local
python manage.py test apps.matching --settings=config.settings.local
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

Fix only real Phase 7 defects.
Do not hide failures by deleting meaningful tests.
If an older phase boundary test incorrectly rejects legal Phase 7 matching routes/app, update only that obsolete assertion.

Update docs/phases/phase_07_matching_quick_match/agent_report.md honestly with:
- defects found
- fixes made
- exact test results
- git status
- diff stat
- confirmation no Phase 8 work
- confirmation no red diagnostics remain

Do not package.
Do not commit.
