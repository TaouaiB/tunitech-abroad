You are Codex acting as strict senior verifier and repair agent for TuniTech Abroad.

Current phase: Phase 15A — Job Skill Materialization Pipeline Hardening.

Read and enforce:
- `docs/phases/phase_15a_job_skill_materialization_pipeline_hardening/tasks.md`
- `acceptance.md`
- Gemini's `agent_report.md`

Your job: verify architecture, run checks, repair only in-scope defects, and write `codex_report.md`. Do not commit.

Hard rules:
- Views thin.
- Business logic in services.
- Celery tasks call services.
- Models do not call external APIs.
- No provider/LLM calls from views/templates.
- No final score decided by LLM.
- Matching must use canonical `NormalizedJobSkill`, not raw LLM JSON as primary source.
- No React/Next/Vue/Angular/FastAPI/MongoDB/SQLAlchemy.
- No secrets/raw CV/raw provider/raw LLM leaks.
- No migrations unless absolutely justified.

Expected implementation:
- Canonical service materializes skills from job JSON and LLM output.
- LLM enrichment success calls materialization.
- Normalization/ingestion paths do not leave jobs stuck pending when skills exist.
- Backfill command exists, is idempotent, bounded, and never calls providers.
- Tests cover service, LLM integration, ingestion path, command, and matching safety.

Verification checklist:
1. Inspect changed files and reject broad unrelated UI/deployment/OAuth/CV changes.
2. Inspect materialization service: transaction, dedupe, admin preservation, `NormalizedJobSkill`, `UnmatchedSkillCandidate`, required over optional, source/confidence, status update, no external calls.
3. Inspect LLM wiring: materialization after successful validation; provider success not converted into provider failure by materialization; no retry-provider loop.
4. Inspect ingestion path: `sync_france_travail_jobs --normalize` and scheduled ingestion do not bypass extraction/materialization.
5. Run all checks:
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
6. Run safety greps:
```bash
grep -R "file.url\|cv.file.url\|upload.file.url\|raw_text\|raw_request_json\|raw_response_text\|raw_response_json" templates apps -n 2>/dev/null || true
grep -R "<int:" apps templates config -n 2>/dev/null || true
grep -R "OpenRouterClient\|OPENROUTER\|client.chat\|_make_request" apps/*/views.py apps/*/admin.py templates -n 2>/dev/null || true
grep -R "FranceTravailClient\|search_offers\|api.francetravail" apps/*/views.py templates -n 2>/dev/null || true
git diff -- . ':!.env' ':!.env.*' | grep -iE "sk-or-|Bearer [A-Za-z0-9_.-]{20,}|OPENROUTER_API_KEY=.*[^=]|FRANCE_TRAVAIL_CLIENT_SECRET=.*[^=]|EMAIL_HOST_PASSWORD=.*[^=]" || echo "OK: no obvious secrets in diff"
```
7. DB smoke locally, no providers:
```bash
python manage.py shell --settings=config.settings.local <<'PY'
from django.db.models import Count
from apps.jobs.models import NormalizedJob, NormalizedJobSkill
print("TOTAL_JOBS", NormalizedJob.objects.count())
print("ACTIVE_JOBS", NormalizedJob.objects.filter(status="active").count())
print("ACTIVE_WITH_SKILLS", NormalizedJob.objects.filter(status="active", job_skills__isnull=False).distinct().count())
print("ACTIVE_PENDING", NormalizedJob.objects.filter(status="active", skill_extraction_status="pending").count())
print("NJS_ROWS", NormalizedJobSkill.objects.count())
print("ACTIVE_ENRICHED_SUCCESS_NO_SKILLS", NormalizedJob.objects.filter(status="active", enrichment__status="success", job_skills__isnull=True).distinct().count())
for row in NormalizedJob.objects.values("skill_extraction_status").annotate(c=Count("id")).order_by("skill_extraction_status"):
    print("STATUS", row)
PY
```
8. Run the new backfill command in dry-run then limited real run:
```bash
python manage.py materialize_job_skills --active-only --limit 20 --dry-run --settings=config.settings.local
python manage.py materialize_job_skills --active-only --limit 20 --settings=config.settings.local
```
Run DB smoke again. There should be clear improvement.

Repair in-scope issues directly. Block only for secret exposure, forbidden stack, unjustified migrations/model changes, scoring formula change, provider calls in tests/views/templates, broad unrelated rewrites, or tests still failing after repair.

Create:
`docs/phases/phase_15a_job_skill_materialization_pipeline_hardening/codex_report.md`

Report must include PASS/REPAIRED_PASS/FAIL, exact files changed, architecture verdict, materialization verdict, LLM wiring verdict, ingestion path verdict, backfill verdict, DB before/after numbers, checks, safety greps, remaining risks, and commit recommendation.
