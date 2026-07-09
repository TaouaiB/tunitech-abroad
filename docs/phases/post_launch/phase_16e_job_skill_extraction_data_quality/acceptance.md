# Phase 16E — Job Skill Extraction and Data Quality — acceptance.md

## General acceptance

```text
All tickets in tasks.md are complete or explicitly deferred with reason.
No next-phase work was implemented.
No stack changes.
Service-layer boundary preserved.
Tests pass or failures are documented and clearly unrelated.
No secrets, raw CV text, OAuth tokens, API keys, or private file paths are logged.
```

## Required checks

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test --settings=config.settings.local
```

## Phase-specific acceptance

```text
Job skill extraction separates required/optional/detected where possible.
Zero-skill and weak-skill jobs are detectable.
Search vectors can be rebuilt.
Public eligibility can be inspected.
No user search calls external API.
```

## Contract with Phase 16F

```text
Each NormalizedJobSkill row must expose a confidence value or documented equivalent that Phase 16F can consume.
The confidence value must distinguish strong extracted skills from weak/ambiguous detected skills.
If the existing schema already has confidence, use it; do not create duplicate fields.
If confidence cannot be implemented in this phase, Codex must mark this as an intent-changing/deferred item and stop for senior review.
```
