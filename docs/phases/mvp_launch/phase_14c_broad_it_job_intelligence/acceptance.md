# Acceptance Criteria

## Automated checks

All must pass:

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test apps.jobs apps.skills apps.matching apps.recommendations --settings=config.settings.local
python manage.py test --settings=config.settings.local
```

If migrations are created, they must be narrow, named clearly, and applied successfully.

## Classification acceptance

Must classify broad IT roles correctly:

- Data Scientist / Data Analyst / Data Engineer / BI => IT, data_ai_bi.
- DevOps / Cloud / SRE => IT, devops_cloud_sre.
- Cybersecurity => IT, cybersecurity.
- QA / Test Automation => IT, qa_testing.
- System/network/admin/infrastructure => IT, systems_network.
- DBA/database/reporting => IT, database or data_ai_bi.
- ERP/CRM/Salesforce/Sage/PeopleSoft => IT, erp_crm.
- IT support/helpdesk => IT when technical context exists.
- IT project/product/business analyst => one combined family `it_project_product_analysis` when clearly tech/SI/product context exists.
- IT apprenticeship/alternance/stage/PFE with technical context => IT, `it_training_apprenticeship`.
- Commercial/business development/photography seller/insurance sales => non_it or excluded.
- Non-technical support/customer-service roles => non_it/excluded.
- Non-technical project/product/business-analysis roles => non_it/excluded.

## Skill extraction acceptance

For description text containing explicit stack terms, extractor must create skills and/or unmatched candidates.

Required examples:

- Flutter, React.js, Node.js, TypeScript, REST APIs.
- RPG, CL, DB2, IBM i, AS400.
- Salesforce.
- SQL, Crystal Reports, MyReport.
- Prestashop, PHP, MySQL.
- Docker, Kubernetes, Linux, Bash.
- Java, Spring, Hibernate, Angular.
- C#, .NET, ASP.NET, SQL Server.

Generic France Travail competences must not become misleading stack skills:

- Application web.
- Concevoir une application web.
- Concevoir et développer une solution digitale.
- Recueillir et analyser les besoins client.

These may be generic signals only.

## Confidence mapping acceptance

The implementation must obey `confidence_mapping.md`. Automated tests must include at least these cases:

| Case | Expected match confidence |
| --- | --- |
| Data Scientist with Python/Machine Learning/Pandas detected but no required skills | low_confidence |
| Generic Web Developer with no extracted skills and weak description | unavailable |
| Photography seller / commercial “développeur” | unavailable |
| Real Java/Spring/Angular or C#/.NET job with required stack | reliable |
| Generic France Travail competence labels only | not reliable |

## Match/recommendation acceptance

- Non-IT jobs are excluded from recommendations.
- Low-confidence IT jobs are ranked after reliable jobs.
- Match detail clearly displays `reliable`, `low_confidence`, or `unavailable` behavior.
- Data Scientist with optional/detected skills shows detected skills instead of “no technical skills” and is labelled low confidence if required skills are not explicit.
- Web Developer with no extracted skills and weak/generic description is unavailable, not a reliable normal match.
- Photography seller does not appear as an IT match.

## UI acceptance

Job detail/match pages must use French human labels:

- Famille IT.
- Qualité du signal technique.
- Compétences obligatoires détectées.
- Compétences optionnelles / détectées.
- Compétences génériques France Travail.
- Données insuffisantes if applicable.

No raw internal states/flags should leak:

```text
non_it_low_relevance_job
no_required_skills_extracted
low_confidence_job_skills
insufficient_job_technical_signal
strong
partial
generic_only
missing
excluded_non_it
```

## Security/privacy acceptance

- No secrets printed.
- No `.env` committed.
- No live API call from public job search/match pages.
- No OpenRouter call from views/templates.
- No CV text/file URL exposed.

## Human signoff

Baha must manually validate in Chrome:

- `/jobs/`
- a real IT job detail page
- a data job match
- a DevOps/cloud match
- a non-IT/photography job if visible
- `/dashboard/recommendations/`

Until then verdict remains:

```text
BLOCKED_HUMAN_VISUAL_SIGNOFF
```
