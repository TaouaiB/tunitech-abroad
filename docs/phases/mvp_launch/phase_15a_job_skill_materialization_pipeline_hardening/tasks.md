# Phase 15A Tasks — Job Skill Materialization Pipeline Hardening

## Objective

Make the job skills pipeline reliable before deployment.

Every active IT job should move from raw skill evidence to canonical job skill rows:

```text
NormalizedJob.required_skills_json / optional_skills_json
and/or
JobEnrichment.validated_output_json.required_skills / optional_skills
        ↓
Skill + SkillAlias normalization
        ↓
NormalizedJobSkill rows
        ↓
UnmatchedSkillCandidate rows for unknown skills
        ↓
skill_extraction_status updated
        ↓
matching/recommendations/cards can use canonical skills
```

## Strict scope

Allowed:
- Create/update services for skill materialization.
- Wire existing normalization/enrichment paths to the materialization service.
- Add a backfill management command.
- Add tests proving the pipeline works.
- Add minimal docs/report files.

Not allowed:
- UI redesign.
- New frontend dependencies.
- React/Next/Vue/Angular/FastAPI/MongoDB/SQLAlchemy.
- Model/migration changes unless absolutely unavoidable.
- Changing final matching score formula.
- Letting LLM decide the final fit score.
- Provider/live API calls in Django views.
- Reading raw LLM JSON directly in templates as the primary display source.
- Exposing raw request/response/CV text/secrets.
- Committing.

## Task 1 — Inspect existing service contracts and code paths

Inspect:
- `apps/jobs/services/skill_extraction.py`
- `apps/jobs/services/normalization.py`
- `apps/jobs/services/ingestion.py`
- `apps/llm/services/job_enrichment.py`
- `apps/skills/services/normalizer.py`
- `apps/jobs/tasks.py`
- `apps/llm/tasks.py`
- management commands for ingestion/enrichment.

Confirm:
- Which paths create/update `NormalizedJob`.
- Which paths call `JobSkillExtractionService.extract_for_job`.
- Which paths save `JobEnrichment.validated_output_json`.
- Whether any service already materializes enrichment into `NormalizedJobSkill`.

## Task 2 — Implement materialization service

Create a dedicated service, suggested path:

```text
apps/jobs/services/skill_materialization.py
```

Suggested public API:

```python
@dataclass(frozen=True)
class JobSkillMaterializationResult:
    job_id: int
    created_count: int
    updated_count: int
    matched_required_count: int
    matched_optional_count: int
    unmatched_count: int
    source: str
    status: str

class JobSkillMaterializationService:
    @classmethod
    def materialize_for_job(cls, job, *, source: str = "rule", enrichment=None) -> JobSkillMaterializationResult:
        ...
```

The service must:
- Use `transaction.atomic`.
- Accept candidates from `job.required_skills_json`, `job.optional_skills_json`, and enrichment `required_skills` / `optional_skills`.
- Support LLM skill dicts and plain strings.
- Normalize candidates via existing `SkillNormalizerService` / `SkillAlias`.
- Create/update `NormalizedJobSkill`.
- Create/update `UnmatchedSkillCandidate` for unknown skills.
- Preserve `SkillSource.ADMIN` rows if present.
- Avoid duplicate rows.
- Prefer required over optional if the same skill appears in both.
- Use `SkillSource.LLM` for enrichment-derived skills.
- Use `SkillSource.RULE` or `SOURCE_API` for provider/raw-derived skills.
- Set `requirement_type` correctly.
- Set confidence safely.
- Update `NormalizedJob.required_skills_json` / `optional_skills_json` with useful canonical display values where appropriate.
- Update `skill_extraction_status` to `success`, `not_enough_text`, or `failed`.
- Recompute/update `skill_signal_quality`.
- Rebuild or refresh `search_vector` if existing project code does this during skill extraction.

## Task 3 — Harden existing `JobSkillExtractionService`

`JobSkillExtractionService.extract_for_job(job)` should either delegate to the new materialization service or share the same canonical implementation path.

Avoid duplicate logic.

The old rule-based flow must still work:
- Raw provider skill JSON -> canonical skill rows.
- Unknown provider skills -> `UnmatchedSkillCandidate`.
- Empty/no useful skills -> no permanent pending state.

## Task 4 — Wire LLM enrichment success to materialization

In `apps/llm/services/job_enrichment.py`, after successful validation and save of `JobEnrichment.validated_output_json`, call the materialization service.

Required behavior:
- LLM provider success remains logged as success.
- Materialization failure must not trigger another provider call.
- On materialization exception, log safe error and mark `job.skill_extraction_status=failed`.
- Do not expose raw LLM response in templates or logs.
- Do not call OpenRouter from tests.

## Task 5 — Fix ingestion command/path inconsistency

Ensure every normalized job goes through skill extraction/materialization.

At minimum:
- `sync_france_travail_jobs --normalize` must not leave normalized jobs stuck pending when provider skill JSON exists.
- Scheduled ingestion path must also run extraction/materialization.
- `JobNormalizationService.normalize_record_by_id()` already calls extraction; preserve or improve that path.
- If code uses `JobNormalizationService.normalize(raw_record)` directly, call materialization after it or switch to `normalize_record_by_id()` where appropriate.

## Task 6 — Add backfill management command

Create a command, suggested name:

```bash
python manage.py materialize_job_skills --active-only --limit 200
```

Suggested options:
- `--active-only`
- `--status active|stale|removed` optional repeat/list
- `--limit`
- `--dry-run`
- `--enriched-only`
- `--pending-only`
- `--force`
- `--source rule|llm|both`

Command should:
- Process active jobs with `skill_extraction_status=pending`.
- Process active jobs with successful enrichment but no `job_skills`.
- Process jobs with raw `required_skills_json` / `optional_skills_json` but no `job_skills`.
- Be idempotent.
- Print counts: scanned, materialized, created skills, unmatched candidates, no skill candidates, failed.
- Never call external APIs or OpenRouter.

## Task 7 — Add tests

Add tests proving:
- Provider/raw skills create `NormalizedJobSkill`.
- LLM `required_skills` / `optional_skills` create `NormalizedJobSkill`.
- Known skills match `Skill.canonical_name`.
- Aliases match `SkillAlias.normalized_alias`.
- Unknown skills create/update `UnmatchedSkillCandidate`.
- Duplicate skill names do not create duplicate rows.
- Required wins over optional.
- Existing `SkillSource.ADMIN` rows are preserved.
- `skill_extraction_status` no longer remains pending after processing.
- Successful enrichment triggers materialization without OpenRouter calls in tests.
- Backfill command materializes active enriched jobs and is idempotent.
- Matching still reads `job.job_skills` and scoring formula is unchanged.

## Task 8 — Post-implementation local health command

After implementation, run a DB audit similar to:

```bash
python manage.py shell --settings=config.settings.local <<'PY'
from django.db.models import Count
from apps.jobs.models import NormalizedJob, NormalizedJobSkill

print("Total:", NormalizedJob.objects.count())
for row in NormalizedJob.objects.values("status").annotate(c=Count("id")).order_by("status"):
    print(row["status"], row["c"])
active = NormalizedJob.objects.filter(status="active").count()
active_with = NormalizedJob.objects.filter(status="active", job_skills__isnull=False).distinct().count()
print("Active:", active)
print("Active with job_skills:", active_with)
print("Active without job_skills:", active - active_with)
print("NormalizedJobSkill rows:", NormalizedJobSkill.objects.count())
for row in NormalizedJob.objects.values("skill_extraction_status").annotate(c=Count("id")).order_by("skill_extraction_status"):
    print(row["skill_extraction_status"], row["c"])
PY
```

Expected improvement:
- Active jobs with `job_skills` rises significantly.
- Active enriched-success jobs without `job_skills` drops close to zero for common matched skills.
- Pending active IT jobs no longer dominate.

## Deliverable

Create:
`docs/phases/phase_15a_job_skill_materialization_pipeline_hardening/agent_report.md`

Do not commit.
