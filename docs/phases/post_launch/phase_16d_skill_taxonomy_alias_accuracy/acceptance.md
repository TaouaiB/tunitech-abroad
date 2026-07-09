# Phase 16D — Skill Taxonomy and Alias Accuracy — acceptance.md

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
Skill aliases normalize .NET, dotnet, .NET Core, Node.js, ReactJS, Postgres, C#, C++, CI/CD.
Matching compares skill IDs where in scope.
audit_skill_aliases exists or is documented if deferred.
Unknown skills go to review, not auto-created.
```
