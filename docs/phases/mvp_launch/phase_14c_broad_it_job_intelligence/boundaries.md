# Boundaries

## Architecture rules

- Views stay thin.
- Business logic goes in services.
- Celery tasks call services only.
- Models store data and expose simple display helpers only.
- No external API calls from public job search or match pages.
- No OpenRouter/LLM calls from views.
- Public job pages use UUID `public_id`, never internal integer IDs.

## Source rules

Normal user search and match pages must read from local PostgreSQL only.

France Travail live API calls are allowed only in ingestion/revalidation services or management commands, not in public request flow.

## Mandatory confidence mapping

All code and tests must follow:

```text
docs/phases/phase_14c_broad_it_job_intelligence/confidence_mapping.md
```

The mapping between classification confidence, skill signal quality, and match confidence is not optional.

## Matching rules

- Do not show a normal fit score if job technical data is unavailable.
- Do not treat missing required skills as “candidate has all required skills.”
- Do not give perfect language/experience/location scores when job data is unknown.
- Non-IT jobs must be excluded from recommendations.
- Low-confidence IT jobs may be shown only with explicit low-confidence labeling.

## Job classification rules

The platform is IT-focused, not developer-only.

Valid IT jobs include more than developers:

- Data Scientist, Data Analyst, BI Analyst, Data Engineer.
- DevOps, Cloud Engineer, SRE, Infrastructure Engineer.
- Cybersecurity Analyst/Engineer.
- QA Tester, Test Automation Engineer.
- System/Network Administrator.
- DBA / Database Engineer.
- ERP/CRM/Salesforce/Sage/PeopleSoft technical consultant/developer.
- IT Support / Helpdesk when technical.
- IT project/product/business analyst when clearly in tech/product/information systems context.

But these are not IT matches unless there is explicit IT signal:

- commercial / sales development
- photography “développeur-vendeur”
- business development
- insurance sales
- generic “développement commercial”
- non-technical training/sales/admin jobs

## PASS blockers

This phase fails if:

- The photography seller job is recommended as a developer/IT match.
- A job with no technical signal shows a normal score page.
- Data Scientist / DevOps / Cloud / QA / Cyber / ERP / IT support / IT project-product-analysis / IT apprenticeship jobs are rejected just because they are not developer roles.
- Description skills like Flutter, React.js, Node.js, TypeScript, REST APIs, SQL, Java, Spring, C#, .NET, Laravel, PHP, Vue.js, Docker, Kubernetes, PostgreSQL are not extracted when present in raw descriptions.
- Generic France Travail skills like “Application web” become misleading required stack skills.
- Raw risk flags leak to the user.
- Tests pass only by hardcoding specific current job IDs.
- `it_support` jobs without technical context are accepted as IT.
- project/product/business-analysis jobs without SI/software/product-system context are accepted as IT.
- `it_training_apprenticeship` exists as a family but has no fixture/test coverage.
