# Phase 16F — Matching and Recommendation Accuracy — acceptance.md

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
Fit score remains deterministic.
LLM cannot alter score.
Recommendation reasons are stored/built deterministically.
Missing skills and risks are understandable.
Tests cover exact/related/low-confidence skill behavior where implemented.
```

## Upstream dependency check

```text
Before changing scoring behavior, verify Phase 16D canonical ProfileSkill.skill_id exists and Phase 16E NormalizedJobSkill confidence exists or equivalent is documented.
Do not invent upstream data fields inside 16F without explicit senior approval.
```
