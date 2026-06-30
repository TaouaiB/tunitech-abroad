# Codex Verification Prompt — Phase 14C

You are verifying Phase 14C only.

Read:

```text
docs/phases/phase_14c_broad_it_job_intelligence/acceptance.md
docs/phases/phase_14c_broad_it_job_intelligence/confidence_mapping.md
docs/phases/phase_14c_broad_it_job_intelligence/regression_security_checks.md
docs/phases/phase_14c_broad_it_job_intelligence/agent_report.md
```

Verify:

1. Broad IT classification exists and is service-layer based.
2. Job skill extraction reads description and structured France Travail fields.
3. Generic FT skills are not treated as misleading stack requirements.
4. Data Scientist, DevOps, Cloud, QA, Cyber, ERP/CRM, support, and project/product IT cases are supported.
5. Non-IT/commercial/photography cases are excluded or unavailable.
6. Match/recommendation UX does not show normal score for unavailable data.
7. No raw internal flags leak in templates.
8. No live France Travail API from public search/match/recommendation/dashboard pages.
9. No LLM calls from views/templates.
10. Tests and greps pass.
11. The exact confidence mapping table is implemented and tested.
12. `it_project_product_analysis` is used as one combined family; no ambiguous split between project/product and business analysis.
13. IT apprenticeship positive case and non-technical support/project negative cases are tested.

Run:

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test apps.jobs apps.skills apps.matching apps.recommendations --settings=config.settings.local
python manage.py test --settings=config.settings.local
```

Final verdict must be one of:

```text
FAIL
BLOCKED_HUMAN_VISUAL_SIGNOFF
```

Never write PASS unless Baha has explicitly completed manual Chrome signoff.
