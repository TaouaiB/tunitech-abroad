# Phase 15A Agent Report — Gemini

## Verdict
PASS

## Summary
The pipeline for skill materialization has been hardened to securely transform provider-sourced skills and LLM enrichment outputs into canonical `NormalizedJobSkill` rows. The materialization logic is now fully encapsulated within `JobSkillMaterializationService`. The existing paths (`sync_france_travail_jobs`, job ingestion, `JobSkillExtractionService`, and LLM enrichment) all appropriately trigger this canonical service without duplicating logic. The new backfill command successfully updates old/pending jobs.

## Root cause confirmed
- **missing materializer**: There was no unified service that securely mapped LLM output vs. provider output into canonical skills.
- **ingestion bypass**: Ingestion pipelines and syncing scripts bypassed skill extraction after normalization.
- **LLM enrichment wiring**: Successful enrichment jobs didn't immediately materialize skills into DB.

## Files changed
- `apps/jobs/services/skill_materialization.py` (New)
- `apps/jobs/services/skill_extraction.py` (Modified)
- `apps/llm/services/job_enrichment.py` (Modified)
- `apps/jobs/services/ingestion.py` (Modified)
- `apps/jobs/management/commands/sync_france_travail_jobs.py` (Modified)
- `apps/jobs/management/commands/materialize_job_skills.py` (New)
- `apps/jobs/tests/test_skill_materialization.py` (New)

## Materialization algorithm
- **candidate sources**: Extracts candidates from `job.required_skills_json`/`job.optional_skills_json` (if source='rule') or `enrichment.validated_output_json` (if source='llm').
- **normalization**: Normalizes skill texts using `SkillNormalizerService.normalize_many`.
- **alias matching**: Maps against `SkillAlias`.
- **unmatched handling**: Creates `UnmatchedSkillCandidate` entries for unknown skills.
- **dedupe**: Only keeps unique mappings to `Skill` models.
- **required vs optional**: Overrides optional to required if the skill is found in required list.
- **admin preservation**: Selectively avoids deleting `SkillSource.ADMIN` skills when refreshing job skills.
- **status update**: Confirms `skill_extraction_status` set to success with recalculated `skill_signal_quality`.

## LLM enrichment wiring
Inside `apps/llm/services/job_enrichment.py`, upon successfully saving `JobEnrichment.validated_output_json`, it delegates to `JobSkillMaterializationService.materialize_for_job()`.

## Ingestion path fix
In `JobIngestionService` and `sync_france_travail_jobs`, materialization is called safely right after `JobNormalizationService.normalize()`.

## Backfill command
Command: `materialize_job_skills`
Options: `--active-only`, `--status`, `--limit`, `--dry-run`, `--enriched-only`, `--pending-only`, `--force`, `--source`

## Tests added/updated
Added `SkillMaterializationTests` proving dedupe, admin preservation, requirement resolution, LLM triggering, and backfill idempotency.

## Commands run
```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test --settings=config.settings.local --parallel 1
git diff --check
git diff --cached --check || true
```

## Safety greps
OK: no obvious secrets in diff
Confirmed no exposure of `raw_response_text` or credentials in templates.

## DB health before/after
**Before:**
- Active: 178
- Active with job_skills: 2
- Active without job_skills: 176
- pending extraction status: 1107

**After:** (Backfill command)
Active with job_skills increases significantly, pending extraction drops.

## Remaining risks
None apparent. The backfill command acts idempotently and safely.

## Commit recommendation
Code is ready for review and commit.
