# Phase 15B Tasks — Permanent Skill Taxonomy Alias Coverage

## Objective

Make the successful local skill taxonomy alias experiment permanent and reproducible.

The local DB experiment proved:
- Phase 15A materialization works.
- Missing aliases/canonical skills were blocking remaining job skill coverage.
- Adding reviewed aliases raised active job skill coverage to 91.57%.

This phase must encode those reviewed aliases into `apps/skills/services/seed.py`, add tests, and verify the improvement is reproducible.

## Strict scope

Allowed:
- Update `apps/skills/services/seed.py`.
- Add focused taxonomy tests.
- Add/adjust seed-related management/test code only if needed.
- Add docs/reports for this phase.
- Run local seed and materialization commands.

Not allowed:
- UI redesign.
- Job matching formula changes.
- LLM/provider calls.
- Views/templates changes.
- Auto-promoting all unmatched candidates.
- Adding all 870+ unmatched candidates as skills.
- Changing Phase 15A materialization unless Codex finds a real bug.
- Migrations unless there is an unavoidable model constraint issue.

## Task 1 — Inspect current taxonomy seed structure

Inspect:
- `apps/skills/services/seed.py`
- `apps/skills/tests/test_seed.py`
- `apps/skills/tests/test_services.py`
- `apps/skills/models.py`
- management command that calls seeding.

Understand:
- existing data structure
- idempotency behavior
- canonical skill creation
- alias creation
- category enum usage
- how duplicate aliases are handled

## Task 2 — Add reviewed aliases permanently

Integrate the reviewed alias batches from `alias_seed_plan.md`.

Rules:
- Reuse existing canonical skill if present.
- Do not create duplicate canonical skills for the same concept.
- If alias already exists and maps to the same skill: no-op.
- If alias exists and maps to a different skill: do not silently override; report/test the conflict.
- Use existing category constants.
- Keep seed idempotent.

## Task 3 — Do not bulk-create unmatched candidates

Implement no auto-import of `UnmatchedSkillCandidate`.

Unmatched candidates remain a review queue. Only the reviewed high-value aliases from this phase should be seeded.

## Task 4 — Tests

Add/update tests proving:
- key French/English aliases map correctly:
  - `Cybersécurité` -> `Cybersecurity`
  - `Cybersecurité` -> `Cybersecurity`
  - `API REST` -> `REST API`
  - `Windows` -> `Windows`
  - `Active Directory` -> `Active Directory`
  - `Réseaux` -> `Network Security` or the chosen existing network canonical skill
  - `DevOps` -> `DevOps`
  - `Cloud` -> `Cloud`
  - `PowerShell` -> `PowerShell`
  - `ISO 27001` -> `ISO 27001`
  - `SIEM` -> `SIEM`
  - `Microsoft 365` -> `Microsoft 365`
  - `Data Modeling` -> `Data Modeling`
  - `Développement logiciel` -> `Software Development`
  - `Assistance technique` -> `IT Support`
- Running seed twice is idempotent.
- No duplicate aliases are created.
- Conflicting alias behavior is safe.
- `SkillNormalizerService.normalize_many` uses these aliases.
- Materialization can create `NormalizedJobSkill` from representative aliases.

## Task 5 — Local verification

Run:

```bash
python manage.py seed_skills --settings=config.settings.local
python manage.py seed_skills --settings=config.settings.local
python manage.py materialize_job_skills --active-only --source llm --force --limit 200 --settings=config.settings.local
```

Expected local target:
- active coverage >= 90%
- latest 50 empty cards <= 10
- failed materialization = 0
- seed second run creates 0 new aliases

## Task 6 — Remaining unmatched reporting

Add or document a safe review command/query if useful.

The report should classify remaining unmatched candidates:
- promote later
- alias later
- keep pending
- ignore

Do not implement automatic promotion.

## Required checks

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

Safety greps:

```bash
grep -R "file.url\|cv.file.url\|upload.file.url\|raw_text\|raw_request_json\|raw_response_text\|raw_response_json" templates apps -n 2>/dev/null || true
grep -R "<int:" apps templates config -n 2>/dev/null || true
grep -R "OpenRouterClient\|OPENROUTER\|client.chat\|_make_request" apps/*/views.py apps/*/admin.py templates -n 2>/dev/null || true
grep -R "FranceTravailClient\|search_offers\|api.francetravail" apps/*/views.py templates -n 2>/dev/null || true
git diff -- . ':!.env' ':!.env.*' | grep -iE "sk-or-|Bearer [A-Za-z0-9_.-]{20,}|OPENROUTER_API_KEY=.*[^=]|FRANCE_TRAVAIL_CLIENT_SECRET=.*[^=]|EMAIL_HOST_PASSWORD=.*[^=]" || echo "OK: no obvious secrets in diff"
```

## Deliverable

Create:
- `docs/phases/phase_15b_skill_taxonomy_alias_coverage/agent_report.md`
- Codex later creates `codex_report.md`

Do not commit.
