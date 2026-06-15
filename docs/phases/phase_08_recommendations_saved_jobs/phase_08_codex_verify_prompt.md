Read AGENTS.md first.

You are the strict verification/fix agent after Gemini implemented Phase 8.

Review Phase 8 only. Fix only defects inside Phase 8 scope. Do not start Phase 9.

Read:

- docs/phases/phase_08_recommendations_saved_jobs/tasks.md
- docs/phases/phase_08_recommendations_saved_jobs/prompt.md
- docs/phases/phase_08_recommendations_saved_jobs/acceptance.md
- docs/phases/phase_08_recommendations_saved_jobs/agent_report.md

Hard boundary:

Do not create OpenRouter/LLM calls, LLM explanations, email digest, transactional emails, unsubscribe, privacy/account deletion, admin observability dashboards, deployment work, React/Next/Angular/FastAPI/SQLAlchemy/MongoDB/SPA.

Do not commit, merge, or push.

Verification checklist:

1. Check git status and diff scope.
2. Confirm changed files are limited to Phase 8 and necessary prior-phase hooks.
3. Confirm `apps.recommendations` exists and is registered.
4. Confirm `JobRecommendation`, `RecommendationRun`, and `SavedJob` exist with constraints/indexes.
5. Confirm no recommendation model stores raw CV text, CV file path, or CV URL.
6. Confirm `RecommendationService.refresh_for_user()` exists.
7. Confirm recommendation generation uses Phase 7 `MatchScoringService` and does not duplicate scoring logic.
8. Confirm recommendation generation reads local PostgreSQL only.
9. Confirm no live France Travail API call exists.
10. Confirm incomplete profile skips recommendations cleanly.
11. Confirm active CV access uses `CVUpload.objects`, not `CVUpload.all_objects`.
12. Confirm ranking formula is deterministic and documented.
13. Confirm refreshing twice does not duplicate recommendations.
14. Confirm old recommendations become stale/update safely inside a transaction.
15. Confirm expired jobs are excluded or marked `expired_job`.
16. Confirm `RecommendationQueryService` reads stored recommendations and does not compute heavy refresh synchronously in dashboard view.
17. Confirm missing/stale recommendations enqueue refresh safely without breaking the page.
18. Confirm `SavedJobService` is idempotent for save/remove.
19. Confirm save/unsave uses job UUID public_id only.
20. Confirm users cannot see/remove another user's saved jobs.
21. Confirm expired saved jobs remain visible with a status label.
22. Confirm Celery tasks call services only and contain no recommendation logic.
23. Confirm no email/digest/unsubscribe work exists.
24. Confirm no OpenRouter import/call exists.
25. Confirm no Phase 9+ files/features exist.
26. Confirm no wrong file named `task.md`, no `__pycache__`, no `.pyc`, no sqlite DB, no celerybeat files.
27. Confirm no red Pyright/Antigravity diagnostics remain. Prefer real typing fixes over `# type: ignore`.

Run:

```bash
source .venv/bin/activate
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py migrate --settings=config.settings.local
python manage.py seed_skills --settings=config.settings.local
python manage.py seed_job_sources --settings=config.settings.local
python manage.py ingest_job_fixtures apps/jobs/fixtures/france_travail_sample_jobs.json --settings=config.settings.local
python manage.py test apps.recommendations --settings=config.settings.local
python manage.py test apps.jobs --settings=config.settings.local
python manage.py test apps.matching --settings=config.settings.local
python manage.py test --settings=config.settings.local
```

Then run:

```bash
grep -R "openrouter\|OpenRouter" apps/recommendations apps/jobs apps/dashboard -n || echo "OK no OpenRouter"
grep -R "francetravel\|francetravail\|FranceTravail\|api.francetravail" apps/recommendations apps/jobs apps/dashboard -n || echo "OK no live France Travail"
grep -R "email_digest\|unsubscribe\|send_mail" apps/recommendations apps/jobs apps/dashboard -n || echo "OK no email phase work"
grep -R "CVUpload.all_objects" apps/recommendations -n || echo "OK no all_objects in recommendations"
find . -type d -name "__pycache__" -print
find . -name "*.pyc" -print
find . -maxdepth 4 -name "task.md" -print
find . -maxdepth 3 -name "*.sqlite3" -print
find . -maxdepth 3 -name "celerybeat-schedule*" -print
git status --short
git diff --stat
```

Fix only real Phase 8 defects.

Do not hide failures by deleting meaningful tests.

If an older phase boundary test incorrectly rejects legal Phase 8 recommendations/routes/models, update only that obsolete assertion.

Update docs/phases/phase_08_recommendations_saved_jobs/agent_report.md honestly with:

- defects found
- fixes made
- exact test results
- git status
- diff stat
- confirmation no Phase 9 work
- confirmation no red diagnostics remain

Do not package.
