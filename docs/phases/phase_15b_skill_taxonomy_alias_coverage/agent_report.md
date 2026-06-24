# Phase 15B Agent Report

## Verdict

PASS

## Summary

Phase 15B made the reviewed alias experiment permanent in the skill seed service, added regression coverage for alias lookup and job skill materialization, and verified local active job skill coverage remains above the 90% target after seeding and rematerialization.

No unmatched candidate auto-promotion was implemented. No matching formula, UI, LLM, or France Travail live search behavior was changed.

## Files changed

- `apps/skills/services/seed.py`
- `apps/skills/tests/test_seed.py`
- `apps/skills/tests/test_services.py`
- `apps/jobs/tests/test_skill_materialization.py`
- `docs/phases/phase_15b_skill_taxonomy_alias_coverage/agent_report.md`

## Alias strategy

Integrated the reviewed Phase 15B batches from `alias_seed_plan.md` into `SkillSeedService.seed_initial_taxonomy()`.

High-value canonical groups added or extended include:

- Security / cyber: `Cybersecurity`, `Network Security`, `Application Security`, `Database Security`, `Cloud Security`, `Vulnerability Management`, `Risk Analysis`, `GRC`, `ISO 27001`, `ISO 27005`, `NIS2`, `IAM`, `SIEM`, `Entra ID`, `Active Directory`
- Systems / support: `Windows`, `PowerShell`, `Microsoft 365`, `Office 365`, `Troubleshooting`, `GLPI`, `IT Support`, `IT Asset Management`, `Hardware Maintenance`, `Workstation Deployment`
- DevOps / cloud: `DevOps`, `Cloud`, `OpenShift`, `Azure DevOps`, `Infrastructure as Code`, `Argo CD`, `Helm`, `Dynatrace`, `VMware`, `Monitoring`, `Data Center Operations`
- API / software delivery: `REST API`, `API`, `Software Development`, `Software Analysis`, `Software Architecture`, `Software Testing`, `Software Deployment`, `Technical Documentation`, `Requirements Analysis`
- Data / AI / automation: `Data Modeling`, `Data Engineering`, `Data Warehouse`, `ETL`, `dbt`, `Azure Data Factory`, `PySpark`, `Prompt Engineering`, `RAG`, `Azure OpenAI`, `Copilot Studio`, `RPA`
- ERP / legacy / embedded: `ERP`, `ABAP`, `SAP ECC6`, `SAP S/4HANA`, `SAP Fiori`, `SAP UI5`, `COBOL`, `Mainframe`, `JCL`, `CICS`, `Embedded Systems`, `Embedded Linux`, `RTOS`, `Yocto Project`

The seed now:

- reuses existing canonical names through `get_or_create(canonical_name=...)`
- creates missing aliases only when `normalized_alias` is not already present
- reports alias conflicts in the returned result and console output
- leaves conflicting existing mappings unchanged instead of silently remapping
- sorts grouped Phase 15B aliases for deterministic seed behavior

I also removed internal fresh-seed duplicate alias definitions by keeping `Ruby on Rails` / `RoR` on the `Ruby on Rails` canonical skill instead of `Ruby`, and `ASP.NET Core` on `.NET Core` instead of `ASP.NET`.

## Conflicts found

Focused tests prove fresh seed idempotency has no internal conflicts.

Verification initially found historical local database aliases from an earlier seed run:

- `ruby on rails` mapped to `Ruby`, while the corrected seed wants `Ruby on Rails`
- `ror` mapped to `Ruby`, while the corrected seed wants `Ruby on Rails`

Codex repaired those local aliases explicitly during verification. They now map to `Ruby on Rails`, and `seed_skills` runs without Ruby/RoR conflict output.

The test suite also includes a deliberate conflict fixture for `Cybersécurité`; it verifies the seed reports the conflict and preserves the existing mapping.

## Unmatched candidate policy

No bulk importer was added. `UnmatchedSkillCandidate` remains a human review queue.

Recommended remaining strategy:

- Promote later: reusable IT skills or technologies that appear on both CVs and jobs.
- Alias later: translations, spelling variants, and clear synonyms for existing canonical skills.
- Keep pending: ambiguous acronyms, sector terms, and phrases needing human review.
- Ignore: responsibilities, vague process text, education requirements, and non-matching business-only terms.

## Tests added/updated

- `apps/skills/tests/test_seed.py`
  - key French/English aliases map to expected canonicals
  - seed can run twice without duplicate aliases
  - alias conflicts are reported and not remapped
- `apps/skills/tests/test_services.py`
  - `SkillNormalizerService.normalize_many()` resolves representative Phase 15B aliases
- `apps/jobs/tests/test_skill_materialization.py`
  - representative Phase 15B aliases create `NormalizedJobSkill` rows through `JobSkillMaterializationService`

Focused test run:

```text
Ran 22 tests in 18.987s

OK
```

Full test run:

```text
Ran 474 tests in 87.495s

OK
```

## Seed verification

First run:

```text
Starting skill taxonomy seed...
Successfully seeded taxonomy. Skills created: 0, Aliases created: 0.
```

Second run:

```text
Starting skill taxonomy seed...
Successfully seeded taxonomy. Skills created: 0, Aliases created: 0.
```

Second run created 0 skills and 0 aliases.

## Materialization verification

```text
Found 178 jobs matching criteria.
Finished processing 178 jobs.
Success: 166
No skill candidates: 12
Failed: 0
Skills created (if tracked): 1016
Unmatched candidates (if tracked): 620
```

Failed materialization count: 0.

## DB health

Before this run, the local database was already carrying the successful alias experiment state:

```text
active_total=178
active_with_skills=163
active_coverage_pct=91.57
latest_50_empty=9
```

After seeding and rematerialization:

```text
active_total=178
active_with_job_skills=163
active_without_job_skills=15
coverage_pct=91.57
active_strong_empty=0
active_enriched_success_empty=12
normalized_job_skill_rows=1197
latest_50_empty_cards=9
```

Coverage target met: 91.57% >= 90%.

Latest 50 empty cards target met: 9 <= 10.

## Checks

```text
python manage.py check --settings=config.settings.local
System check identified no issues (0 silenced).
```

```text
python manage.py makemigrations --check --dry-run --settings=config.settings.local
No changes detected
```

```text
npm run css:build
Done in 827ms.
```

Note: Tailwind emitted the existing Browserslist freshness warning.

```text
python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
2 static files copied to '/home/bahaedinetaouai/Projects/tunitech-abroad/staticfiles', 134 unmodified.
```

```text
git diff --check
```

Passed with no output.

```text
git diff --cached --check || true
```

Passed with no output.

## Safety greps

The safety grep for file URLs / raw text / raw LLM payload fields returned existing model, service, admin, and test references only. No new unsafe template exposure was added in this phase.

The `<int:`, OpenRouter-in-views/admin/templates, and France Travail-in-views/templates greps returned no findings.

Secret scan result:

```text
OK: no obvious secrets in diff
```

## Remaining risks

- Other environments that previously seeded the old Ruby/RoR mapping may need the same explicit data repair. Fresh databases seeded from the current code map `RoR` and `Ruby on Rails` to `Ruby on Rails`.
- Remaining unmatched candidates still need review over time. They should be promoted, aliased, kept pending, or ignored manually according to `unmatched_skill_policy.md`.
- The 12 active enriched-success empty jobs appear to have no usable skill candidates after materialization. This is acceptable because the target is 90%+ coverage, not 100%.

## Commit recommendation

Commit after review with a message such as:

```text
Complete Phase 15B skill taxonomy alias coverage
```
