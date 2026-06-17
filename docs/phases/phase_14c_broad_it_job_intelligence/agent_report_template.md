# Phase 14C Agent Report — Broad IT Job Intelligence

## Verdict

Choose one:

```text
FAIL
BLOCKED_HUMAN_VISUAL_SIGNOFF
```

Never write PASS before Baha manual Chrome signoff.

## Summary

- What was changed:
- What was intentionally not changed:

## Files changed

List files created/modified.

## Confidence mapping proof

Confirm exact implementation of `confidence_mapping.md`:

- Mapping location in code:
- Tests covering each required example:
- Data Scientist optional-only =>
- Web Developer no skills =>
- Photography/commercial =>
- Real stack required =>
- Generic FT only =>

## Classification changes

- Service(s):
- Job families supported:
- Storage field used:
- Migration created: yes/no

## Skill extraction changes

- Services changed:
- Skill aliases added:
- Generic labels excluded from canonical stack:
- Unmatched skill handling:

## Fixture coverage

Must include IT apprenticeship, non-technical support negative case, and non-technical project/business-analysis negative case.

List fixture cases and expected result:

| Fixture | Family | Required skills | Optional/detected skills | Expected confidence |
| --- | --- | --- | --- | --- |

## Proof output

Paste proof output for:

- Data Scientist.
- Web Developer weak data.
- Photography seller.
- Salesforce.
- Mobile automation.
- AS400/RPG/DB2.
- DevOps.
- QA.
- Cybersecurity.
- ERP/Sage/PeopleSoft.

## Commands run

Paste commands and status:

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test apps.jobs apps.skills apps.matching apps.recommendations --settings=config.settings.local
python manage.py test --settings=config.settings.local
```

## Security checks

- Secrets check:
- Public live API check:
- LLM-in-view check:
- Raw private data check:
- Raw internal flag leak check:
- Root junk cleanup:

## Browser/manual status

- Chrome tested by agent/headless: yes/no
- Baha manual signoff: pending

## Remaining risks

List honestly.
