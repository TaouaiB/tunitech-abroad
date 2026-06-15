<!-- Converted to Markdown for repository/agent context. The original generated PDF/DOCX remains the formatted source-of-truth document. -->


**TuniTech Abroad**

Business Requirements Document (BRD)

Version: v1 \| Status: Review Draft \| Date: 12 June 2026

# 1. Executive Summary

TuniTech Abroad is a France-first job intelligence platform for Tunisian
IT candidates, students, bootcamp graduates, and internship seekers. The
product aggregates France IT jobs, helps users upload and complete their
CV/profile, recommends realistic jobs or internships, detects missing
skills, and provides practical CV/job-fit guidance before applying.

The product is not a generic job board. Its core value is candidate
intelligence: helping Tunisian IT profiles understand which France
opportunities are realistic, why they match, what is missing, and what
to improve.

# 2. Product Identity

| **Product name**             | TuniTech Abroad                |
|------------------------------|--------------------------------|
| **Document**                 | Business Requirements Document |
| **Version**                  | v1                             |
| **Status**                   | Review Draft                   |
| **Candidate market**         | Tunisia                        |
| **First destination market** | France                         |
| **Domain**                   | IT jobs and internships        |
| **Primary UI language**      | French                         |

# 3. Business Problem

Tunisian IT candidates who target France or other francophone markets
face a fragmented and inefficient job search process.

- France IT jobs and internships are scattered across multiple
  platforms.

- Candidates apply randomly without knowing if their CV actually fits
  the job.

- Candidates do not know which technical skills are missing.

- Students and junior candidates struggle to identify realistic
  internships, PFE opportunities, and first jobs.

- Mid-level candidates may have relevant experience but weak CV
  positioning.

- Generic job boards list jobs but do not explain fit, missing skills,
  or readiness.

- Generic CV checkers analyze CVs without connecting them to real France
  IT job demand.

The market gap is job intelligence, not job listing volume.

# 4. Product Vision

Build the reference platform for Tunisian IT profiles targeting
francophone international opportunities, starting with France and later
expanding to Belgium, Luxembourg, Canada, and Switzerland.

The MVP focuses on France only to keep data sourcing, matching logic,
and product scope controllable.

# 5. Core Positioning

Positioning statement: TuniTech Abroad helps Tunisian IT profiles
understand which France IT jobs or internships they can realistically
target, what they are missing, and how to improve their CV/profile
before applying.

Short positioning: France IT job intelligence for Tunisian tech
profiles.

# 6. Target Users

| **User group**        | **Description**                                                                                          | **Primary needs**                                                                |
|-----------------------|----------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------|
| Junior IT candidate   | 0-2 years experience; may target first job, junior role, summer internship, standard internship, or PFE. | Realistic recommendations, missing skills, CV guidance, junior-friendly filters. |
| Final-year IT student | Preparing for PFE, summer internship, France internship, or first job after graduation.                  | Market visibility, skill roadmap, project/CV positioning, internship filtering.  |
| Bootcamp graduate     | Candidate entering the IT market through bootcamp training.                                              | Skill gap roadmap, realistic expectations, project-based CV guidance.            |
| Mid-level developer   | 2-5 years experience targeting France IT jobs.                                                           | Better targeting, CV alignment, role/stack positioning, advanced gap detection.  |

# 7. Secondary Users and Future Business Opportunities

- Training centers, bootcamps, and universities: future dashboard for
  student employability, readiness scores, cohort skill gaps, and
  placement analytics.

- Recruiters and recruitment agencies: future access to pre-analyzed
  candidate profiles and job-fit signals.

These are not MVP user groups for product functionality. They are later
monetization directions.

# 8. Value Proposition

| **Audience**                | **Value delivered**                                                                                            |
|-----------------------------|----------------------------------------------------------------------------------------------------------------|
| Candidates                  | Know which jobs match, why they match, which skills are missing, and what to improve.                          |
| Students/internship seekers | See realistic internship/PFE/first-job options and understand the roadmap from current profile to target jobs. |
| Bootcamp graduates          | Understand skill gaps and improve employability using real France IT job demand.                               |
| Mid-level developers        | Prioritize stronger applications and improve CV positioning for France recruiters.                             |
| Future training centers     | Measure student readiness and align training with real demand.                                                 |

# 9. MVP Scope

## 9.1 Included

- Public landing page and public France IT job search.

- Job detail pages from local normalized database.

- France Travail API as primary job source.

- Raw job storage and normalized job storage.

- Job freshness tracking: active, stale, expired, removed, archived.

- Google login, GitHub login, and email/password signup.

- Email verification for email/password users.

- PDF CV upload and parsing.

- Manual profile completion after parsing.

- Anonymous quick-match teaser using manual skills.

- Rule-based match scoring.

- Job recommendations.

- Skill gap detection using canonical skill taxonomy and aliases.

- Controlled OpenRouter LLM usage for extraction help and explanations.

- Saved jobs, match history, email preferences, optional weekly digest.

- Django Admin-based admin dashboard.

- Basic privacy/GDPR features: Privacy Policy, Terms, CV consent, delete
  CV, delete account.

## 9.2 Excluded

- Employer dashboard, recruiter dashboard, training center dashboard.

- Payments and subscriptions.

- Belgium, Luxembourg, Canada, and Switzerland jobs.

- Welcome to the Jungle partnership/API integration, APEC scraping,
  Adzuna fallback.

- LinkedIn full profile import, LinkedIn login, Facebook login.

- Auto-apply, chatbot, mobile app, salary prediction, company reviews,
  messaging.

- Legal immigration advice or guaranteed employment/relocation claims.

- AI-only scoring or bulk LLM job ranking.

# 10. Job Source Strategy

MVP primary source: France Travail API Offres d emploi. The platform
should ingest jobs on a schedule, store raw source records, normalize
jobs locally, and serve search/recommendations from PostgreSQL rather
than calling the external API for each user search.

Future internship/alternance source: La Bonne Alternance API, especially
for apprenticeship/alternance opportunities. It is not required in the
first MVP build unless France Travail internship coverage is
insufficient.

- No scraping for MVP.

- No live external API call per user search.

- High-intent revalidation may refresh a specific job when a user opens
  or applies to an old job.

# 11. Skill Taxonomy Strategy

MVP uses a flat canonical skill taxonomy with aliases. This prevents
noisy matching between raw strings such as Python, Python 3, python
developer, and Python/Django.

| **Entity**            | **Purpose**                                                            |
|-----------------------|------------------------------------------------------------------------|
| Skill                 | Canonical normalized skill such as Python, Django, Docker, PostgreSQL. |
| SkillAlias            | Aliases that map raw extracted strings to a canonical skill.           |
| UnknownSkillCandidate | Unmatched extracted skill stored for admin review.                     |

- MVP target: 200-300 canonical IT skills.

- Aliases target: 500-1000 aliases.

- Initial categories: Programming Language, Frontend, Backend, Database,
  DevOps, Cloud, Testing, Data/AI, Mobile, Tools, Methodology, Soft
  Skill.

- LLM may suggest skills, but the system maps them to canonical taxonomy
  before scoring.

# 12. Matching and Recommendation Strategy

The product separates candidate-job fit from recommendation ranking.

| **Fit score component**        | **Weight** |
|--------------------------------|------------|
| Technical skills match         | 45%        |
| Experience level match         | 20%        |
| Role/title match               | 15%        |
| Language fit                   | 10%        |
| Location/remote/relocation fit | 10%        |

Recency affects recommendation ranking, not fit score. Recommendation
ranking combines fit score, freshness boost, target-type boost,
user-preference boost, and stale-job penalty.

# 13. Anonymous Quick-Match Teaser

To reduce funnel friction, anonymous users may test a limited match on a
job by entering 3-5 skills, experience level, and French level. The
teaser returns an estimated match, matched skills, likely missing
skills, and a prompt to create an account for full CV analysis.

The anonymous teaser does not use LLM, does not store a CV, does not
create recommendations, and does not save history.

# 14. Authentication and Profile Strategy

| **Method**              | **MVP decision**                                                                 |
|-------------------------|----------------------------------------------------------------------------------|
| Google login            | Included.                                                                        |
| GitHub login            | Included.                                                                        |
| Email/password          | Included with email verification.                                                |
| LinkedIn login          | Excluded from MVP.                                                               |
| Facebook login          | Excluded from MVP.                                                               |
| LinkedIn profile import | Excluded from MVP due to restricted API access. Manual LinkedIn URL is included. |

OAuth simplifies account creation but does not replace profile
completion. Users must still complete phone, location,
LinkedIn/GitHub/portfolio URLs, target role, target type, experience,
language levels, and preferences.

# 15. Privacy and Compliance Basics

The product processes CVs and recruitment-related personal data. MVP
must include concrete privacy features, not only internal security
notes.

- Privacy Policy page.

- Terms page.

- Explicit CV upload consent checkbox.

- Delete CV action.

- Delete account and associated data action.

- Email unsubscribe/preferences.

- No public CV exposure.

- Restricted admin access to user CV/profile data.

- No guaranteed employment, visa, or relocation claims.

# 16. Business Model

| **Phase**                       | **Monetization logic**                                                                                     |
|---------------------------------|------------------------------------------------------------------------------------------------------------|
| Phase 1: Free MVP               | Validate demand with free job search, limited CV matching, recommendations, and saved jobs.                |
| Phase 2: Candidate monetization | Paid detailed CV/job-fit report, CV rewrite for France market, personalized roadmap, premium explanations. |
| Phase 3: B2B monetization       | Training center dashboard, bootcamp/university employability analytics, recruiter/talent pool access.      |

# 17. Success Metrics

| **Category**        | **Metrics**                                                                                                                   |
|---------------------|-------------------------------------------------------------------------------------------------------------------------------|
| Product             | Registered users, uploaded CVs, completed profiles, job searches, job detail views, saved jobs, returning users.              |
| Matching            | Match analyses generated, recommendation click-through rate, saved jobs from recommendations, user feedback on match quality. |
| Data quality        | CV parsing success rate, job normalization success rate, skill extraction success rate, unknown skill rate.                   |
| Cost/control        | LLM calls per user, cache hit rate, LLM cost per active user.                                                                 |
| Business validation | Users requesting CV improvement, paid report interest clicks, digest opt-ins, organic traffic growth.                         |

# 18. Main Risks and Mitigations

| **Risk**               | **Mitigation**                                                                                                   |
|------------------------|------------------------------------------------------------------------------------------------------------------|
| Job source limitations | Start with France Travail API, store raw payloads, track source errors, add La Bonne Alternance later if needed. |
| Skill matching noise   | Use canonical skill taxonomy with aliases and admin review for unknown skills.                                   |
| CV parsing errors      | Show extracted profile to user and require manual confirmation/completion.                                       |
| LLM cost growth        | Rule-based scoring, caching, rate limits, LLM only for selected explanations/extraction support.                 |
| Funnel friction        | Anonymous quick-match teaser before signup.                                                                      |
| Privacy risk           | Consent, deletion, restricted CV access, clear policy pages.                                                     |
| Scope creep            | France-only MVP, no recruiter/employer/training-center side yet.                                                 |

# 19. Recommended Technology Direction

- Backend/product: Django.

- Frontend: Django templates + HTMX + Tailwind.

- Database: PostgreSQL.

- Background jobs: Redis + Celery or RQ.

- Auth: django-allauth for Google, GitHub, email/password.

- AI: OpenRouter, controlled and cached.

- Admin: Django Admin for MVP.

# 20. Final MVP Decision

Build a France-first job intelligence platform for Tunisian IT
candidates, students, bootcamp graduates, and internship seekers. The
core loop is: user finds France IT jobs or internships, uploads CV or
tests quick match, completes profile, receives recommendations, sees
match score, understands missing skills, saves or applies to
better-targeted opportunities.

This BRD is ready for review before moving to Technical Architecture v1
after PRD validation.

# 21. References Used for Planning

- France Travail API Offres d emploi:
  https://www.data.gouv.fr/dataservices/api-offres-demploi

- La Bonne Alternance developer/API space:
  https://labonnealternance.apprentissage.beta.gouv.fr/espace-developpeurs

- CNIL recruitment and GDPR guide:
  https://www.cnil.fr/fr/le-guide-du-recrutement

- LinkedIn Profile API restriction note:
  https://learn.microsoft.com/en-us/linkedin/shared/integrations/people/profile-api
