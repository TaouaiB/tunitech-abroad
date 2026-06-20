# Phase 15D Tasks — Curated Taxonomy + Zero-Skill Job Recovery

## Task 0 — Read context

Read:
- this phase folder
- Phase 15A/15B/15C reports
- `apps/jobs/services/skill_extraction.py`
- `apps/jobs/services/skill_materialization.py`
- `apps/jobs/services/admin_operations.py`
- `apps/skills/services/seed.py`
- `apps/skills/services/normalizer.py`
- `apps/skills/models.py`
- `apps/jobs/models.py`

Also read the curated CSV decisions in this phase folder if present:
- `taxonomy_review_decisions_phase_15d_approved.csv`
- `taxonomy_review_decisions_all_780.csv`

## Task 1 — Curated taxonomy seed updates

Apply only approved rows from `taxonomy_review_decisions_phase_15d_approved.csv`.

Implement in `SkillSeedService.seed_initial_taxonomy()` or its existing seed structure.

Requirements:
- add approved aliases
- add approved new canonical skills
- no duplicate canonical skills
- no duplicate normalized aliases
- no silent alias remapping
- seed idempotent
- preserve existing conflict reporting

## Task 2 — Permanent ignore rules

Add a permanent ignore mechanism for obvious junk/unhelpful candidates.

Acceptable designs:
- `apps/skills/services/ignored.py`
- or a clean class inside `normalizer.py`

Rules:
- exact normalized terms preferred
- very limited phrase rules allowed
- no broad regex that hides real skills
- ignored terms should not appear as new pending candidates
- existing pending candidates that are now ignored should be reconcilable

Examples:
- pedagogy/education-only terms
- diploma names such as Bac Pro CIEL / Bac Pro MSPC
- sector-only labels such as secteur automobile / secteur industriel
- generic `informatique` if used alone and not useful as a skill
- broad `reporting` only if project decides it is not useful for matching

## Task 3 — Reconcile old pending unmatched candidates

Add a command such as:

```bash
python manage.py reconcile_unmatched_skill_candidates --dry-run --settings=config.settings.local
python manage.py reconcile_unmatched_skill_candidates --apply --settings=config.settings.local
```

It should:
- mark already-resolved candidates as resolved/mapped if model supports status
- mark ignored candidates as ignored if model supports status
- leave keep_pending untouched
- not delete rows
- output counts

If the current model does not support statuses needed, do not add a migration unless absolutely necessary. Prefer using existing statuses/fields.

## Task 4 — Deterministic zero-skill recovery service

Add a service, for example:

```python
apps/jobs/services/zero_skill_recovery.py
class ZeroSkillJobRecoveryService:
    recover_job(job) -> result
    recover_queryset(qs) -> result
```

Requirements:
- runs only on jobs with zero `NormalizedJobSkill`
- uses stored `NormalizedJob.description/title`
- detects explicit evidence phrases from `deterministic_recovery_rules.md`
- maps evidence to canonical `Skill` records through existing skills/aliases
- creates `NormalizedJobSkill` rows only for mapped canonical skills
- source is deterministic/rule source, not LLM/admin
- idempotent
- does not add fake skills to excluded_non_it/business/outreach jobs
- records/returns reason counts

## Task 5 — Zero-skill recovery command

Add command:

```bash
python manage.py recover_zero_skill_jobs --active-only --dry-run --limit 200 --settings=config.settings.local
python manage.py recover_zero_skill_jobs --active-only --apply --limit 200 --settings=config.settings.local
```

It should output:
- jobs inspected
- skipped excluded/non-IT
- recovered jobs
- skills created
- still zero-skill
- examples

It must not call OpenRouter or France Travail.

## Task 6 — Admin action integration

Add a safe admin action:
- `recover_zero_skill_jobs_action`

It must:
- call `ZeroSkillJobRecoveryService`
- be safe for small selections
- message counts to admin
- not call external providers

## Task 7 — Fix misleading `not_enough_text` behavior

If current code marks long descriptions as `not_enough_text` because no skills were found, improve wording/status handling if possible without migration.

Preferred:
- Only use `not_enough_text` when actual stored job text is too short.
- If text is long but no skills found, use existing status such as `success` with zero skills, or another existing status if available.
- Do not add migration unless already necessary.

## Task 8 — Tests

Required:
- seed idempotency after new aliases/skills
- ignore rules prevent new pending candidates
- reconcile command dry-run/apply behavior
- zero-skill recovery creates expected skills for:
  - Apprenti(e) Technicien Informatique
  - Apprenti infrastructure et sécurité informatique
  - ALTERNANT EN INFORMATIQUE
- zero-skill recovery does not add skills to:
  - SDR/BDR Business Developer Cybersécurité
  - Médiateur scientifique cybersécurité
  - Consultant transformation digitale excluded_non_it
- recovery command dry-run does not write
- recovery command apply writes
- admin action calls service only
- no duplicate `NormalizedJobSkill`

## Task 9 — Verification

Run:

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test --settings=config.settings.local --parallel 1
npm run css:build
python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
git diff --check
```

Run:

```bash
python manage.py seed_skills --settings=config.settings.local
python manage.py seed_skills --settings=config.settings.local
python manage.py reconcile_unmatched_skill_candidates --dry-run --settings=config.settings.local
python manage.py recover_zero_skill_jobs --active-only --dry-run --limit 200 --settings=config.settings.local
python manage.py recover_zero_skill_jobs --active-only --apply --limit 200 --settings=config.settings.local
```

Then report before/after:
- active zero-skill jobs
- strong zero-skill jobs
- excluded_non_it zero-skill jobs
- normalized job skill row count
- unmatched candidates by status

## Task 10 — Safety greps

Run:

```bash
grep -R "OpenRouterClient\|OPENROUTER\|client.chat\|_make_request" apps/*/views.py apps/*/admin.py templates -n 2>/dev/null || true
grep -R "FranceTravailClient\|search_offers\|api.francetravail" apps/*/views.py templates -n 2>/dev/null || true
grep -R "file.url\|cv.file.url\|upload.file.url\|raw_text\|raw_request_json\|raw_response_text\|raw_response_json" templates apps -n 2>/dev/null || true
grep -R "<int:" apps templates config -n 2>/dev/null || true
git diff -- . ':!.env' ':!.env.*' | grep -iE "sk-or-|Bearer [A-Za-z0-9_.-]{20,}|OPENROUTER_API_KEY=.*[^=]|FRANCE_TRAVAIL_CLIENT_SECRET=.*[^=]|EMAIL_HOST_PASSWORD=.*[^=]" || echo "OK: no obvious secrets in diff"
```

## Deliverables

Create:
- code/tests/commands
- `docs/phases/phase_15d_curated_taxonomy_and_zero_skill_recovery/agent_report.md`

Do not commit.
