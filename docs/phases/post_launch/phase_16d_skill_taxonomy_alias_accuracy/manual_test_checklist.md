# Manual Test Checklist — Phase 16D

Run after automated tests.

```bash
python manage.py audit_skill_aliases --settings=config.settings.local
```

Admin/manual checks:

```text
Open Skill admin and confirm canonical .NET, ASP.NET Core, C#, Node.js, PostgreSQL exist.
Search aliases: dotnet, .NET Core, csharp, node js, postgres, reactjs.
Confirm aliases map to expected canonical skills.
Create/test an UnmatchedSkillCandidate and map it to existing Skill.
Confirm mapping can create safe SkillAlias if implemented.
Confirm matching service uses skill_id, not raw text.
```
