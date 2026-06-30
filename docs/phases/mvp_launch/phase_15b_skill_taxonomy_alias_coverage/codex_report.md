# Phase 15B Codex Verification Report

## Verdict

REPAIRED_PASS

## Summary

Phase 15B is in scope and passes verification after one local data repair: historical `ruby on rails` and `ror` aliases in the local database were explicitly remapped from `Ruby` to the more precise `Ruby on Rails` canonical skill.

The permanent code change already prevents this conflict on fresh databases by keeping `Ruby on Rails` / `RoR` aliases off the `Ruby` canonical seed entry. No UI, matching formula, OpenRouter, France Travail, migrations, or forbidden stack changes were made.

## Files reviewed

- `apps/skills/services/seed.py`
- `apps/skills/tests/test_seed.py`
- `apps/skills/tests/test_services.py`
- `apps/skills/services/normalizer.py`
- `apps/jobs/tests/test_skill_materialization.py`
- `docs/phases/phase_15b_skill_taxonomy_alias_coverage/agent_report.md`
- `docs/phases/phase_15b_skill_taxonomy_alias_coverage/alias_seed_plan.md`
- `docs/phases/phase_15b_skill_taxonomy_alias_coverage/tasks.md`
- `docs/phases/phase_15b_skill_taxonomy_alias_coverage/unmatched_skill_policy.md`

## Repairs applied

Local database repair only:

```text
repair_reason=historical Ruby/RoR aliases should map to Ruby on Rails canonical
before [('ror', 'Ruby'), ('ruby on rails', 'Ruby')]
updated 2
after [('ror', 'Ruby on Rails'), ('ruby on rails', 'Ruby on Rails')]
```

No code repairs were required during this verification pass beyond the Phase 15B code already present in the worktree.

## Taxonomy quality verdict

- No duplicate canonical skills in the local database.
- No duplicate normalized aliases in the local database.
- Ruby/RoR local conflict is repaired.
- Phase 15B aliases are reviewed, bounded, and tied to explicit canonical targets.
- No bulk import of `UnmatchedSkillCandidate` exists.
- Conflict behavior is safe: existing conflicting aliases are reported and not silently remapped by seed.
- No alias spam pattern was added; the seed uses the reviewed `alias_seed_plan.md` batches rather than all unmatched candidates.

DB verification:

```text
duplicate_canonicals []
duplicate_aliases []
ruby_aliases [('ruby', 'Ruby'), ('ror', 'Ruby on Rails'), ('ruby on rails', 'Ruby on Rails')]
```

## Seed idempotency verdict

PASS

After local Ruby/RoR repair:

```text
Starting skill taxonomy seed...
Successfully seeded taxonomy. Skills created: 0, Aliases created: 0.
Starting skill taxonomy seed...
Successfully seeded taxonomy. Skills created: 0, Aliases created: 0.
```

## Normalizer/materialization verdict

PASS

Tests verify:

- high-value aliases such as `Cybersécurité`, `API REST`, `Windows`, `Active Directory`, `Réseaux`, `Cloud`, `PowerShell`, `ISO 27001`, `SIEM`, `Microsoft 365`, `Data Modeling`, `Développement logiciel`, and `Assistance technique`
- `SkillNormalizerService.normalize_many()` resolves representative Phase 15B aliases
- `JobSkillMaterializationService` creates `NormalizedJobSkill` rows from representative Phase 15B aliases
- conflict behavior reports the conflict and preserves the existing mapping

Materialization verification:

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

## DB health verification

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

Acceptance targets:

- Active coverage >= 90%: PASS, 91.57%.
- Latest 50 empty cards <= 10: PASS, 9.
- Failed materialization = 0: PASS.

## Tests/checks

```text
python manage.py check --settings=config.settings.local
System check identified no issues (0 silenced).
```

```text
python manage.py makemigrations --check --dry-run --settings=config.settings.local
No changes detected
```

```text
python manage.py test --settings=config.settings.local --parallel 1
Ran 474 tests in 142.766s

OK
```

```text
npm run css:build
Done in 1610ms.
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

The safety grep for file URLs / raw text / raw LLM payload fields returned existing model, service, admin, and test references only. No new unsafe template exposure was introduced by Phase 15B.

The `<int:`, OpenRouter-in-views/admin/templates, and France Travail-in-views/templates greps returned no Phase 15B scope findings.

Secret scan:

```text
OK: no obvious secrets in diff
```

## Remaining risks

- The local database was repaired, but other environments that previously seeded the old Ruby/RoR mapping may need the same explicit data correction. Fresh databases seeded from the current code will map `RoR` and `Ruby on Rails` to `Ruby on Rails`.
- The remaining 15 active jobs without materialized skills should stay acceptable unless product requirements change. The phase target is 90%+ coverage, not 100%.
- Remaining unmatched candidates should continue through manual review only: promote, alias, keep pending, or ignore according to `unmatched_skill_policy.md`.

## Commit recommendation

Do not commit from this verification step automatically. After review, commit the Phase 15B implementation and reports with:

```text
Complete Phase 15B skill taxonomy alias coverage
```
