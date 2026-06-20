# Phase 15A Codex Verification Report

## Verdict

REPAIRED_PASS

Codex verified Gemini's Phase 15A implementation, found in-scope acceptance issues, repaired them, and reran the required checks successfully.

## Files Changed

- `apps/jobs/services/skill_materialization.py`
- `apps/jobs/services/skill_extraction.py`
- `apps/jobs/services/ingestion.py`
- `apps/jobs/management/commands/sync_france_travail_jobs.py`
- `apps/jobs/management/commands/materialize_job_skills.py`
- `apps/jobs/tests/test_skill_materialization.py`
- `apps/llm/services/job_enrichment.py`
- `apps/llm/tests/test_14d_enrichment.py`
- `apps/matching/services/scoring.py`
- `docs/phases/phase_15a_job_skill_materialization_pipeline_hardening/codex_report.md`

No migrations were created.

## Repairs Applied

- Added support for LLM skill candidates represented as plain strings, not only dictionaries.
- Added safe confidence parsing/clamping for skill candidates.
- Changed empty skill materialization from permanent `pending` to `not_enough_text`.
- Preserved an existing non-empty `skill_signal_quality` when empty materialization has no better evidence, preventing ingestion enrichment qualification regressions.
- Fixed the backfill command so `not_enough_text` jobs are counted as `No skill candidates`, not `Failed`.
- Removed raw `JobEnrichment.validated_output_json` scoring from `MatchScoringService`; matching now uses canonical `job.job_skills` as the skill source.
- Updated enrichment/matching tests to prove materialized enriched skills are used and unmaterialized enrichment JSON is ignored.

## Architecture Verdict

PASS

- Materialization logic lives in `apps/jobs/services/skill_materialization.py`.
- `JobSkillExtractionService` delegates canonical row creation to the materialization service.
- Celery tasks still call services only.
- Models do not call providers.
- Views/templates do not call OpenRouter or France Travail provider logic.
- No forbidden stack was introduced.
- No migrations or broad unrelated UI/deployment/auth/CV changes were introduced.

## Materialization Verdict

PASS

Verified behavior:

- Uses `transaction.atomic`.
- Creates canonical `NormalizedJobSkill` rows.
- Uses existing `SkillNormalizerService` / `SkillAlias`.
- Creates/updates `UnmatchedSkillCandidate` through the normalizer.
- Preserves `SkillSource.ADMIN` rows.
- Avoids duplicate canonical rows on repeated command runs.
- Required beats optional.
- Supports provider/rule skills, LLM dict skills, and LLM plain string skills.
- Sets source to `rule` or `llm` according to materialization source.
- Updates `required_skills_json` / `optional_skills_json` with canonical names.
- Updates `skill_extraction_status` to `success`, `not_enough_text`, or `failed`.
- Recomputes skill signal quality where there is materialized skill evidence.

Remaining caveat: for rule extraction, the wrapper still returns the legacy `SkillExtractionResult`, so command-created counts are only exact when the command calls the materializer directly. The rows are still materialized correctly and idempotently.

## LLM Wiring Verdict

PASS

- Successful enrichment calls `JobSkillMaterializationService.materialize_for_job(..., source="llm")`.
- Materialization errors are caught after provider success and do not trigger another provider call.
- Materialization failure marks only `job.skill_extraction_status=failed`.
- Tests mock OpenRouter; no real OpenRouter call is required.
- Matching no longer scores directly from raw LLM JSON.

## Ingestion Path Verdict

PASS

- `JobNormalizationService.normalize_record_by_id()` still calls extraction.
- `JobIngestionService._process_job()` calls extraction/materialization after normalization.
- `sync_france_travail_jobs --normalize` calls extraction/materialization after normalization.
- Scheduled ingestion uses `JobIngestionService`, so it receives the same materialization behavior.

## Backfill Verdict

PASS

Command:

```bash
python manage.py materialize_job_skills --active-only --limit 200
```

Verified options include `--active-only`, `--status`, `--limit`, `--dry-run`, `--enriched-only`, `--pending-only`, `--force`, and `--source`.

Dry run:

```text
Found 20 jobs matching criteria.
DRY RUN: Exiting without materialization.
```

Bounded real run before counter repair:

```text
Found 20 jobs matching criteria.
Finished processing 20 jobs.
Success: 19
Failed: 1
Skills created (if tracked): 93
Unmatched candidates (if tracked): 108
```

The apparent failure was a `not_enough_text` job, not an actual failed job. The command was repaired and rechecked:

```text
Found 1 jobs matching criteria.
Finished processing 1 jobs.
Success: 1
No skill candidates: 0
Failed: 0
Skills created (if tracked): 0
Unmatched candidates (if tracked): 15
```

The command is bounded, idempotent, and does not call providers.

## DB Smoke

Before bounded backfill:

```text
TOTAL_JOBS 1126
ACTIVE_JOBS 178
ACTIVE_WITH_SKILLS 2
ACTIVE_PENDING 176
NJS_ROWS 62
ACTIVE_ENRICHED_SUCCESS_NO_SKILLS 154
STATUS {'skill_extraction_status': 'pending', 'c': 1107}
STATUS {'skill_extraction_status': 'success', 'c': 19}
```

After bounded backfill:

```text
TOTAL_JOBS 1126
ACTIVE_JOBS 178
ACTIVE_WITH_SKILLS 16
ACTIVE_PENDING 156
NJS_ROWS 164
ACTIVE_ENRICHED_SUCCESS_NO_SKILLS 143
STATUS {'skill_extraction_status': 'not_enough_text', 'c': 1}
STATUS {'skill_extraction_status': 'pending', 'c': 1087}
STATUS {'skill_extraction_status': 'success', 'c': 38}
```

Improvement:

- Active jobs with canonical skills: `2 -> 16`
- Active pending jobs: `176 -> 156`
- NormalizedJobSkill rows: `62 -> 164`
- Active enriched-success jobs without skills: `154 -> 143`

## Checks Run

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

Final results:

- Django check: PASS, no issues.
- Makemigrations dry-run: PASS, no changes detected.
- Full tests: PASS, `469 tests`.
- CSS build: PASS. Warning only: `caniuse-lite is outdated`.
- Collectstatic dry-run: PASS, `2 static files copied`, `134 unmodified`.
- `git diff --check`: PASS.
- `git diff --cached --check || true`: PASS.

## Safety Greps

Ran the required greps for CV file URL/raw text/raw LLM fields, integer URL patterns, OpenRouter/provider usage in views/templates/admin, France Travail provider usage in views/templates, and obvious secrets in diff.

Findings:

- Raw field grep returned expected model, admin, service, migration, and test references.
- No template exposure of raw CV/LLM/provider fields was found.
- No `<int:` URL patterns found in `apps`, `templates`, or `config`.
- No OpenRouter calls found in views/templates/admin.
- No France Travail calls found in views/templates.
- Secret scan result: `OK: no obvious secrets in diff`.

## Remaining Risks / Manual Steps

- A large number of active jobs remain pending because only bounded backfill runs were executed during verification. Continue with a larger controlled backfill, for example `--active-only --limit 200`, after review.
- Some enriched-success jobs still lack canonical skills; many likely contain unknown skill labels requiring taxonomy/alias expansion or unmatched candidate review.
- `npm run css:build` reports an outdated Browserslist database warning; this is not Phase 15A blocking.

## Commit Recommendation

Recommended to review and commit on `dev` after Baha reviews this report. Do not commit directly from this verification step.
