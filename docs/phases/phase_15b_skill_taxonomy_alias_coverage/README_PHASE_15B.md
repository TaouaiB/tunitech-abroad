# Phase 15B — Permanent Skill Taxonomy Alias Coverage

This phase makes the local taxonomy success permanent.

Phase 15A fixed the materialization pipeline. Local experiments proved the remaining gap was not materialization, but missing `Skill` / `SkillAlias` coverage.

Verified local result before alias work:
- Active jobs with job_skills: 135 / 178
- Coverage: 75.84%
- Empty latest 50 cards: 29

Verified local result after two alias batches:
- Active jobs with job_skills: 163 / 178
- Coverage: 91.57%
- Empty latest 50 cards: 9
- Failed materialization: 0

Important: the alias batches were inserted through Django shell into the local DB only. They are not reproducible after a fresh deployment until they are encoded in `apps/skills/services/seed.py` and covered by tests.

Primary goal:
- Permanently seed high-value skill aliases and safe canonical skills.
- Keep taxonomy quality controlled.
- Do not convert every unmatched candidate into a skill.
