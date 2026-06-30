# Phase 16D — Skill Taxonomy and Alias Accuracy — tasks.md

## Goal

Make canonical skill handling reliable and ML-ready without building ML now.

## Required phase-specific policy

Read:

```text
canonical_skill_seed_table_v1.md
skill_alias_policy.md
```

Do not let Gemini invent taxonomy content from scratch. Use the seed artifact as the baseline and extend only when the existing repo already has richer skill data.

## In-scope apps/areas

```text
skills
profiles
matching
admin skill review
management commands
```

## Tickets

### TTA-16D-001 — ProfileSkill canonical FK audit/backfill

Priority: P0  
Type: model/migration/service/test

Acceptance:

```text
ProfileSkill has canonical skill FK according to v1 schema, or migration adds/backfills it safely.
Existing profile skill text/json is mapped through SkillAlias where possible.
Unmatched profile skills become UnmatchedSkillCandidate or review items; they are not silently dropped.
Backfill is idempotent.
Matching can read canonical skill_id.
```

### TTA-16D-002 — Canonical alias expansion

Priority: P0  
Type: seed/service/test

Acceptance:

```text
Seed/alias data includes the baseline from canonical_skill_seed_table_v1.md.
.NET, dotnet, .NET Core, ASP.NET Core, C#, C sharp, Node.js, node js, Postgres/PostgreSQL, ReactJS/React are covered.
Aliases normalize accents/case/punctuation/spacing.
Seed is idempotent.
No duplicate normalized_alias conflict unless intentionally resolved.
```

### TTA-16D-003 — audit_skill_aliases command

Priority: P0  
Type: command/service/test

Add:

```bash
python manage.py audit_skill_aliases --settings=config.settings.local
```

Acceptance:

```text
Reports duplicate normalized aliases.
Reports ambiguous aliases.
Reports aliases with missing/deactivated skill.
Reports frequent unmatched candidates from CV/job/quick_match/manual sources.
Uses shared diagnostics dict contract.
```

### TTA-16D-004 — Unmatched skill admin review hardening

Priority: P0  
Type: admin/service/test

Acceptance:

```text
Admin can map candidate to existing Skill.
Admin can ignore candidate.
Mapping can create SkillAlias if safe.
reviewed_by and reviewed_at set.
Only staff/superuser access.
No auto-create of canonical Skill from unknown text without owner/admin action.
```

### TTA-16D-005 — Matching by skill_id

Priority: P0  
Type: matching/service/test

Acceptance:

```text
Profile/job skill comparison uses skill_id, not raw strings.
Existing string snapshots may remain for display/debug only.
Tests prove .NET aliases normalize before matching.
No related-skill partial scoring yet unless explicitly already present and tested.
```

## Out of scope

```text
No job required/optional classifier rewrite.
No related-skill scoring beyond exact canonical ID matching.
No ML/DL.
No UI redesign.
```
