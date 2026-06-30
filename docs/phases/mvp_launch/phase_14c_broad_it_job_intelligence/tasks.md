# Tasks

## TTA-14C-001 — Preflight and current data audit

- Run checks.
- Capture current modified/untracked files.
- Inspect current job models and available fields.
- Inspect current job normalization, classification, relevance, and skill extraction services.
- Do not commit.

## TTA-14C-002 — Build real-style France Travail fixtures

Create fixtures from current observed payload patterns, without secrets:

1. software app C# / WinDev / .NET.
2. mobile automation Flutter / React / Node / TypeScript / REST APIs.
3. AS400 / IBM i / RPG / DB2.
4. Salesforce developer.
5. data analyst/data engineer with SQL/BI/reporting.
6. webmaster / ecommerce / Prestashop / PHP / MySQL.
7. DevOps / Docker / Kubernetes / Linux / Bash.
8. cybersecurity.
9. QA / test automation.
10. photography seller / sales non-IT negative case.
11. commercial/business development negative case.
12. generic web developer with no extracted skills unavailable/low-confidence case.
13. IT apprenticeship/alternance front-end or support IT positive case.
14. non-technical customer support/helpdesk negative case.
15. non-technical project/product/business-analysis negative case.

Fixtures should live under a suitable tests fixture path inside `apps/jobs/tests/fixtures/` or equivalent.

## TTA-14C-003 — Broad IT family classification service

Add or improve a service such as:

```text
apps/jobs/services/it_classification.py
```

It should return a typed result:

```python
@dataclass(frozen=True)
class JobITClassificationResult:
    family: str
    is_it: bool
    confidence: str  # high | medium | low | excluded
    reasons: list[str]
    negative_reasons: list[str]
```

Use title, description, ROME fields, competences, formations, secteur.

## TTA-14C-004 — Improve skill extraction from descriptions

Improve `JobSkillExtractionService` so it extracts skills from:

- `competences[]` labels.
- description paragraphs.
- explicit sections: `Stack technique`, `Compétences techniques`, `Environnement technique`, `Votre boîte à outils`, `Profil recherché`, `Missions`.

Rules:

- `exigence=E` can become required if the skill is technical and specific.
- `exigence=S` becomes optional unless description section says required/indispensable/maîtrise.
- Description phrases like “Maîtrise de Flutter” or “Compétences techniques indispensables” should mark skills required.
- Generic FT labels are generic signals, not canonical stack skills.

## TTA-14C-005 — Expand canonical skill aliases

Add missing aliases for observed tech, if not already present:

```text
C#, .NET, .NET Core, ASP.NET, WinDev, IBM i, AS400, RPG, CL, DB2, Salesforce, Apex, Flutter, TypeScript, REST API, GraphQL, SharePoint, OVHcloud, n8n, Make, Sage X3, PeopleSoft, PeopleCode, SQR, PL/SQL, Crystal Reports, MyReport, Prestashop, Laravel, Symfony, Vue.js, Nuxt.js, Quarkus, Hibernate, Maven, Kubernetes, RabbitMQ, SignalR, SQL Server, PostgreSQL, MySQL, MariaDB, Cypress, Selenium, Playwright, Power BI, Tableau.
```

Do not create duplicates. Prefer aliases mapped to existing canonical skills where appropriate.

## TTA-14C-006 — Skill signal quality and mapping

Define job skill signal states:

```text
unknown
strong
partial
generic_only
missing
excluded_non_it
```

`unknown` is allowed only as a default/pre-computation value. User-facing and recommendation logic must map it before display.

Use the exact mapping table in `confidence_mapping.md` to convert classification confidence + skill signal quality into match confidence.

## TTA-14C-007 — Reprocess existing local jobs

Add or use an existing management command to re-run normalization/skill extraction/classification for local jobs only.

No public request should call France Travail live.

## TTA-14C-008 — Update match/recommendation UX labels and exact confidence behavior

Match detail must show:

- job family.
- skill signal quality.
- extracted required skills.
- detected optional/generic skills.
- confidence label.

Do not show normal score bars for unavailable matches.

Use exact behavior from `confidence_mapping.md`:

- Data Scientist with detected optional stack and no required stack => `low_confidence`, show detected skills and “compétences obligatoires non précisées”.
- Web Developer with no extracted skills and generic text => `unavailable`, hide normal score.
- Photography/commercial/sales jobs => `unavailable`, excluded from recommendations.
- Real stack with required skills => `reliable`.

## TTA-14C-009 — Tests

Add unit/integration tests for:

- each fixture classification.
- extraction of stack from description.
- negative non-IT cases.
- generic competence labels not becoming misleading stack skills.
- recommendations include broad IT families.
- non-IT excluded.
- low-confidence correctly labelled.

## TTA-14C-010 — Final report

Write:

```text
docs/phases/phase_14c_broad_it_job_intelligence/agent_report.md
```

Include changed files, tests, proof commands, and remaining risks.
