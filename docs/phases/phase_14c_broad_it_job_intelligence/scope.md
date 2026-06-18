# Scope

## In scope

1. Audit existing job normalization and skill extraction services.
2. Add or improve broad IT job family classification.
3. Improve rule-based job skill extraction from France Travail payloads.
4. Use both structured France Travail fields and description text:
   - `intitule`
   - `description`
   - `romeCode`
   - `romeLibelle`
   - `appellationlibelle`
   - `competences[]`
   - `formations[]`
   - `secteurActiviteLibelle`
   - `experienceLibelle`
   - `experienceExige`
   - `langues[]`
   - `natureContrat`
   - `alternance`
   - `typeContratLibelle`
5. Add support for broad IT families:
   - software development
   - web/mobile development
   - data / AI / BI
   - DevOps / cloud / SRE
   - cybersecurity
   - QA / testing
   - systems / network / infrastructure
   - database / DBA
   - ERP / CRM / Salesforce / Sage / PeopleSoft
   - IT support / helpdesk / technical support
   - IT project/product/business analysis as one combined family
   - technical training / IT apprenticeship / internship / PFE
   - low-confidence IT
   - non-IT / excluded
6. Improve canonical skill aliases for skills seen in current France Travail samples.
7. Add data quality/confidence labels for job skill extraction.
8. Reprocess existing local jobs using local DB only.
9. Update match/recommendation behavior so weak/non-IT jobs are not confusing.
10. Add tests using real-style France Travail payload fixtures from current Postman samples.

## Out of scope

- No deployment.
- No commit by the agent.
- No React, Next.js, Angular, Vue, SPA, FastAPI, MongoDB, SQLAlchemy, Bootstrap, Material UI.
- No live France Travail call during user job search.
- No LLM-only classification or scoring.
- No broad UI redesign.
- No recruiter/employer features.
- No LinkedIn-style profile experience/education sections. That is a later phase.
- No Belgium/Luxembourg/Canada expansion.
- No auto-apply.

## Migration rule

Prefer using existing fields if available. If `NormalizedJob` already has a suitable metadata/classification JSON field, use it.

If not, a narrow migration is allowed only for a clearly named field such as:

```python
classification_json = models.JSONField(default=dict, blank=True)
skill_signal_quality = models.CharField(max_length=32, default="unknown")  # unknown is a pre-computation state; display logic must map it before user-facing pages
```

Do not add large new tables unless strictly required.


## Required cross-concept mapping

Implementation must follow the table in:

```text
docs/phases/phase_14c_broad_it_job_intelligence/confidence_mapping.md
```

This explicitly maps classification confidence + skill signal quality to match confidence. Do not let each service invent its own rules.
