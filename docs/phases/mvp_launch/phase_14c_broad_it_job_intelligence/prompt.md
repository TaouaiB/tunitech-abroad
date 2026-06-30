# Agent Prompt — Phase 14C Broad IT Job Intelligence and Skill Extraction Quality

Read first:

```text
docs/phases/phase_14c_broad_it_job_intelligence/README.md
docs/phases/phase_14c_broad_it_job_intelligence/scope.md
docs/phases/phase_14c_broad_it_job_intelligence/boundaries.md
docs/phases/phase_14c_broad_it_job_intelligence/observed_issues.md
docs/phases/phase_14c_broad_it_job_intelligence/taxonomy_strategy.md
docs/phases/phase_14c_broad_it_job_intelligence/confidence_mapping.md
docs/phases/phase_14c_broad_it_job_intelligence/tasks.md
docs/phases/phase_14c_broad_it_job_intelligence/acceptance.md
docs/phases/phase_14c_broad_it_job_intelligence/test_plan.md
docs/phases/phase_14c_broad_it_job_intelligence/regression_security_checks.md
```

## Mission

Fix job intelligence quality so TuniTech Abroad supports broad IT roles, not only developer roles.

The platform must correctly classify and extract skills for:

- software/web/mobile developer jobs
- data / AI / BI jobs
- DevOps / cloud / SRE jobs
- cybersecurity jobs
- QA/testing jobs
- systems/network/infrastructure jobs
- database/DBA jobs
- ERP/CRM/Salesforce/Sage/PeopleSoft jobs
- IT support/helpdesk jobs
- IT project/product/business analyst roles as one combined IT/SI/product-analysis family
- IT apprenticeships/stages/PFE

It must exclude or clearly mark non-IT jobs such as photography seller, commercial/business development, insurance sales, and generic sales jobs.

## Hard rules

- Do not commit.
- Do not deploy.
- Do not add React/Vite/SPA or any forbidden stack.
- Do not change public URL strategy.
- Do not call France Travail live from public search/match pages.
- Do not call OpenRouter/LLM from views.
- Do not use LLM to decide the final fit score.
- Do not hide weak data behind fake high scores.
- Do not hardcode current DB IDs.
- Do not delete `manage.py`.

## Required implementation approach

1. Inspect current job model fields before changing schema.
2. If existing fields can store classification, use them.
3. If not, add only narrow migration fields for classification/quality metadata.
4. Implement classification in services, not views.
5. Improve skill extraction through services, not templates.
6. Add tests using fixture payloads modeled on observed France Travail samples.
7. Re-run local normalization/skill extraction for existing jobs through a management command or service call.

## Required behavior

### Data Scientist with optional/detected skills

If a Data Scientist job has Python, Machine Learning, Pandas as optional/detected skills but no required skills:

- Do not say no technical skills exist.
- Show detected skills.
- Mark required skills as “non précisées”.
- Match confidence must be `low_confidence`, not unavailable and not reliable, unless explicit required technical skills are found.

### Web Developer with no skills and weak description

If title says Web Developer but no technical skills are extracted and description is generic:

- Mark `unavailable`.
- Hide normal score bars.
- Explain that the job lacks enough technical signal for a reliable match.

### Photography seller

If title/ROME/description indicates sales/photography/non-IT:

- Mark non_it / unavailable.
- Exclude from recommendations.
- Show human French label if match page is manually opened.

### Real broad IT jobs

If the description contains real stack, extract it even when France Travail `competences[]` are generic.

Examples:

- Flutter, React.js, Node.js, TypeScript, REST APIs.
- RPG, CL, DB2, IBM i, AS400.
- Salesforce, CRM.
- SQL, Crystal Reports, MyReport.
- Prestashop, PHP, MySQL.
- Docker, Kubernetes, Linux, Bash.
- Java, Spring, Hibernate, Angular.
- C#, .NET, ASP.NET, SQL Server.

## Required mapping rule

Implement `confidence_mapping.md` exactly. Do not invent your own mapping between classification confidence, skill signal quality, and match confidence.

## Required commands

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test apps.jobs apps.skills apps.matching apps.recommendations --settings=config.settings.local
python manage.py test --settings=config.settings.local
```

If a migration is added, run:

```bash
python manage.py migrate --settings=config.settings.local
```

## Required proof shell command

Create a proof command or include equivalent output in the report showing for at least these jobs/fixtures:

```text
Data Scientist Junior
Web Developer no skills
Photography seller
Salesforce developer
Mobile automation Flutter/React/Node/TypeScript
AS400/RPG/DB2
DevOps Docker/Kubernetes/Linux
QA/test automation
Cybersecurity
ERP/Sage/PeopleSoft
IT apprenticeship/alternance
Technical IT support
Non-technical support negative case
Non-technical project/business-analysis negative case
```

For each, print:

```text
title
family
is_it
classification confidence
required skills
optional/detected skills
skill signal quality
recommendation eligibility
match confidence
```

## Final report

Write:

```text
docs/phases/phase_14c_broad_it_job_intelligence/agent_report.md
```

Final verdict must be:

```text
BLOCKED_HUMAN_VISUAL_SIGNOFF
```

unless checks fail, then:

```text
FAIL
```
