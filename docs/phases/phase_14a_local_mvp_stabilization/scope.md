# Scope

## Objective

Stabilize the MVP so the local backend and template layer satisfy the product flow:

```text
Tunisian IT profile
→ France IT jobs/internships
→ CV/profile parsing
→ deterministic matching
→ missing skill detection
→ stored recommendations
→ controlled LLM support
```

## Included work

The agent may repair and enhance existing implementation in these areas only:

1. CV upload/parsing/profile prefill.
2. Deterministic CV field extraction quality.
3. Optional OpenRouter structured CV extraction service path.
4. Profile completeness recalculation.
5. Recommendation generation/query/stale behavior.
6. Quick match HTMX/server behavior and template state reset.
7. Safe production 404/500 templates and URL handling.
8. Real-data ingestion service/management command for France Travail, limited to scheduled/manual ingestion only.
9. Test coverage for routes, services, tasks, templates, and management commands.
10. Minimal template polish needed to expose states clearly.

## Excluded work

Do not implement:

- New SPA frontend.
- React, Next.js, Angular, Vue, Svelte.
- FastAPI, Flask, MongoDB, SQLAlchemy.
- Employer dashboard, recruiter dashboard, training center dashboard.
- Payments/subscriptions.
- Auto-apply.
- Chatbot.
- LinkedIn import or LinkedIn login.
- Legal/visa advice.
- AI-only scoring.
- Bulk LLM ranking of jobs.
- Browser automation.
- Deployment changes unless needed only for safe local settings/templates.

## Why this scope exists

The MVP is job intelligence, not job listing volume. The core must prove that a Tunisian IT profile can upload a CV, get useful extracted profile data, compare against France jobs, see missing skills, and receive stored recommendations.
