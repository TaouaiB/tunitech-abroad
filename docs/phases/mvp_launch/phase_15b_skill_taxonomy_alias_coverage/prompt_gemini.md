You are Gemini acting as implementation agent for TuniTech Abroad.

Current phase: Phase 15B — Permanent Skill Taxonomy Alias Coverage.

Context:
Phase 15A fixed the job skill materialization pipeline. Local experiments proved the remaining gap is taxonomy/alias coverage. The local DB alias experiment raised active job skill coverage to 91.57% and reduced latest-50 empty cards to 9. But the aliases were inserted only through Django shell. They must be made permanent in `apps/skills/services/seed.py`.

Your mission:
- Make the reviewed alias batches permanent.
- Add tests.
- Verify `seed_skills` is idempotent.
- Verify materialization coverage remains >=90% locally after seeding and rematerialization.

Hard rules:
- Do not add all unmatched candidates as skills.
- Do not auto-promote `UnmatchedSkillCandidate`.
- Do not change matching formula.
- Do not change UI.
- Do not call OpenRouter or France Travail.
- Do not add React/Next/Vue/Angular/FastAPI/MongoDB/SQLAlchemy.
- Do not commit.
- Do not expose secrets or raw data.

Read first:
- `docs/phases/phase_15b_skill_taxonomy_alias_coverage/tasks.md`
- `docs/phases/phase_15b_skill_taxonomy_alias_coverage/alias_seed_plan.md`
- `docs/phases/phase_15b_skill_taxonomy_alias_coverage/unmatched_skill_policy.md`
- `apps/skills/services/seed.py`
- `apps/skills/tests/test_seed.py`
- `apps/skills/tests/test_services.py`
- `apps/skills/models.py`
- `apps/skills/services/normalizer.py`

Implementation requirements:
1. Integrate reviewed aliases into the existing seed architecture.
2. Prefer existing canonical skills when they exist.
3. Avoid duplicate canonical names and duplicate aliases.
4. If an alias conflict exists, handle it safely and report it; do not silently remap.
5. Keep seeding idempotent.
6. Add tests for high-value mappings listed in `tasks.md`.
7. Add a representative materialization test proving aliases create `NormalizedJobSkill`.

Do not implement a giant automatic unmatched importer.

After implementation, run:
```bash
source .venv/bin/activate
python manage.py seed_skills --settings=config.settings.local
python manage.py seed_skills --settings=config.settings.local
python manage.py materialize_job_skills --active-only --source llm --force --limit 200 --settings=config.settings.local
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test --settings=config.settings.local --parallel 1
npm run css:build
python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
git diff --check
git diff --cached --check || true
```

Run safety greps from `tasks.md`.

Create:
`docs/phases/phase_15b_skill_taxonomy_alias_coverage/agent_report.md`

Report:
- aliases/canonicals added
- conflicts found
- seed first/second run output
- before/after DB coverage
- empty latest 50 count
- tests and checks
- remaining unmatched candidate strategy
- commit recommendation

Do not commit.
