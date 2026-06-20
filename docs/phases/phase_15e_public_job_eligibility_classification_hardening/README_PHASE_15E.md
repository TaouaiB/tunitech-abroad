# Phase 15E — Public Job Eligibility + Classification Hardening

## Purpose

Phase 15E fixes a product trust problem:

- Some non-IT/commercial/outreach jobs are visible to users.
- Some real IT jobs are incorrectly marked `excluded_non_it`.
- Public job pages show weak wording such as `Compétences en cours d'analyse` even when the job should be hidden or admin-review-only.
- Some public badges are duplicated, such as `Internship` appearing twice.

TuniTech Abroad is not a generic job board. Public users should mainly see France IT jobs/internships that are useful for Tunisian IT candidates.

## Current diagnostic

Current local diagnostic showed 10 active jobs with `skill_signal_quality=excluded_non_it`.

The list contains both:
- true non-IT/commercial jobs, for example wood/layout commercial business development;
- real IT jobs incorrectly excluded, for example Data Engineer GCP, Tech Lead / DevOps, Fullstack Java/Angular, .NET/C# Fullstack, Data Engineer / Expert Data Integration.

So we must not simply hide every `excluded_non_it` job before fixing classification.

## High-level goal

Add a central eligibility layer:

```text
job imported
→ classify/reclassify role
→ decide public visibility
→ decide matchability
→ decide admin-review-only/excluded reason
```

Public pages must use this central eligibility, not scattered ad-hoc filters.

## Strict non-goals

- Do not change matching score formula.
- Do not call France Travail live APIs from user search.
- Do not call OpenRouter from views/templates/admin.
- Do not redesign UI.
- Do not bulk-create skills.
- Do not delete jobs.
