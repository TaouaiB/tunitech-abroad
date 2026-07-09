# Manual Test Checklist — Phase 16E

Run commands:

```bash
python manage.py inspect_public_job_eligibility --settings=config.settings.local
python manage.py rematerialize_job_skills --dry-run --limit 20 --settings=config.settings.local
python manage.py rebuild_job_search_vectors --dry-run --limit 20 --settings=config.settings.local
```

Manual checks:

```text
Inspect a job with clear required skills; skills are required with high confidence.
Inspect a job with vague skills; skills are detected/low confidence, not fake required.
Inspect zero-skill jobs report.
Confirm NormalizedJobSkill confidence is present or equivalent documented.
Confirm search vector rebuild does not duplicate skills or call external API.
```
