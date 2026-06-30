You are Gemini acting as the implementation agent for TuniTech Abroad.

Current phase: Phase 15A — Job Skill Materialization Pipeline Hardening.

Read and follow `docs/phases/phase_15a_job_skill_materialization_pipeline_hardening/tasks.md` and `acceptance.md` exactly.

Mission: fix the backend/data pipeline defect where successful `JobEnrichment.validated_output_json` and/or `NormalizedJob.required_skills_json` / `optional_skills_json` do not reliably produce canonical `NormalizedJobSkill` rows.

Do not redesign UI. Do not deploy. Do not commit. Do not reset the current branch. Do not change the final scoring formula. Do not call external providers from tests.

Hard architecture rules:
- Django + Django ORM only.
- Views stay thin.
- Business logic goes in services.
- Celery tasks call services only.
- Models store data and do not call external APIs.
- LLM can extract/suggest, but cannot decide final fit score.
- Public URLs use UUID `public_id`.
- User public job search reads local PostgreSQL only.
- No React, Next.js, Vue, Angular, FastAPI, MongoDB app DB, SQLAlchemy, SPA architecture.
- Do not expose secrets, raw CV text, raw provider payloads, or raw LLM response text in templates.

Implementation focus:
1. Create/refactor canonical materialization service, suggested path `apps/jobs/services/skill_materialization.py`.
2. Make `JobSkillExtractionService.extract_for_job(job)` use the canonical service.
3. Wire successful LLM enrichment to materialization in `apps/llm/services/job_enrichment.py`.
4. Fix normalization/ingestion paths so `sync_france_travail_jobs --normalize` and scheduled ingestion do not bypass extraction/materialization.
5. Add bounded idempotent backfill command, suggested `materialize_job_skills`.
6. Add service, LLM integration, ingestion path, command, and matching safety tests.

Allowed files:
- `apps/jobs/services/skill_materialization.py`
- `apps/jobs/services/skill_extraction.py`
- `apps/jobs/services/normalization.py`
- `apps/jobs/services/ingestion.py`
- `apps/jobs/tasks.py` only if needed
- `apps/llm/services/job_enrichment.py`
- `apps/llm/tasks.py` only if needed
- `apps/jobs/management/commands/materialize_job_skills.py`
- `apps/jobs/management/commands/sync_france_travail_jobs.py`
- tests under `apps/jobs/tests`, `apps/llm/tests`, `apps/recommendations/tests`, `apps/matching/tests`
- `docs/phases/phase_15a_job_skill_materialization_pipeline_hardening/agent_report.md`

Avoid templates/UI/OAuth/CV profile/deployment/model migrations unless absolutely justified.

Required checks:
```bash
source .venv/bin/activate
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test --settings=config.settings.local --parallel 1
npm run css:build
python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
git diff --check
git diff --cached --check || true
```

Required safety greps:
```bash
grep -R "file.url\|cv.file.url\|upload.file.url\|raw_text\|raw_request_json\|raw_response_text\|raw_response_json" templates apps -n 2>/dev/null || true
grep -R "<int:" apps templates config -n 2>/dev/null || true
git diff -- . ':!.env' ':!.env.*' | grep -iE "sk-or-|Bearer [A-Za-z0-9_.-]{20,}|OPENROUTER_API_KEY=.*[^=]|FRANCE_TRAVAIL_CLIENT_SECRET=.*[^=]|EMAIL_HOST_PASSWORD=.*[^=]" || echo "OK: no obvious secrets in diff"
```

Post-fix local verification:
Run the new backfill command in dry-run first, then limited real run. Report active job skill coverage before and after.

Create `agent_report.md` using the provided template. Do not commit.
