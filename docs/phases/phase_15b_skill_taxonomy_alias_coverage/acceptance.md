# Phase 15B Acceptance Criteria

## Accepted only if

- Reviewed aliases are permanently encoded in `apps/skills/services/seed.py`.
- Seed is idempotent.
- No all-unmatched auto-import exists.
- No duplicate canonical skills are introduced.
- Alias conflicts are handled safely.
- High-value aliases normalize correctly.
- Representative materialization creates `NormalizedJobSkill` from aliases.
- Full tests pass.
- No migrations are created unless justified.
- No provider/LLM calls are added.
- No UI/matching formula changes are made.

## Data health target

On the current local dataset after seed + rematerialization:
- active jobs with `job_skills` >= 90%
- latest 50 empty cards <= 10
- failed materialization = 0
- active strong empty <= 2 or explained

## Required checks

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test --settings=config.settings.local --parallel 1
npm run css:build
python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
git diff --check
git diff --cached --check || true
```

## Required safety

- No secrets in diff.
- No raw CV/LLM/provider exposure in templates.
- No public int URL patterns.
- No OpenRouter/France Travail calls from views/templates.
