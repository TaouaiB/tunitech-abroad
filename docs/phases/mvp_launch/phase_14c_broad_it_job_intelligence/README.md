# Phase 14C — Broad IT Job Intelligence and Skill Extraction Quality

## Purpose

TuniTech Abroad must not behave like a narrow “developer-only” board. The product is for Tunisian IT candidates, students, bootcamp graduates, internship seekers, and junior/mid IT profiles targeting France.

This phase fixes the job data intelligence layer so the platform can correctly classify and match many IT job families, not only classic web/software developer roles.

## Core problem

Manual QA found that some jobs have weak or missing structured skills even when the raw France Travail description contains a real technical stack. The app can then show confusing match pages such as:

- “Aucune compétence technique obligatoire n'a été extraite” even when optional/detected skills exist.
- Normal score bars when job data is too weak.
- Non-IT jobs with “développeur” in the title appearing too close to IT jobs.
- Developer-centric language that does not fit data, DevOps, support, QA, ERP, cybersecurity, cloud, BI, systems, or project/product IT roles.

## Phase outcome

After this phase, every normalized job should have a defensible IT classification and skill-signal quality:

- IT family/classification.
- Required technical skills where reliable.
- Optional/detected technical skills where required is not explicit.
- Generic France Travail skills treated as generic signals, not canonical stack skills.
- Non-IT and commercial/photography/etc. jobs excluded from recommendations and shown honestly in match pages.
- Match UI explains data confidence clearly.

## Update notes

This package includes Claude review tightening:

- explicit confidence mapping table in `confidence_mapping.md`;
- one combined `it_project_product_analysis` family;
- IT apprenticeship fixture/test requirement;
- non-technical support and non-technical project/business-analysis negative fixtures;
- widened security checks for matching/recommendations/dashboard;
- `unknown` skill signal state clarified as pre-computation only.

## Agent entry point

Read and execute:

```text
docs/phases/phase_14c_broad_it_job_intelligence/prompt.md
```

## Final verdict rule

The agent must end with:

```text
BLOCKED_HUMAN_VISUAL_SIGNOFF
```

unless an automated check fails, in which case the verdict is:

```text
FAIL
```

Never claim PASS before Baha manually validates the affected job pages and match pages in Chrome.
