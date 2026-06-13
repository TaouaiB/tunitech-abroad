<!-- Converted to Markdown for repository/agent context. The original generated PDF/DOCX remains the formatted source-of-truth document. -->


**TuniTech Abroad**

Product Requirements Document (PRD)

Version: v1 \| Status: Review Draft \| Date: 12 June 2026

# 1. Product Summary

TuniTech Abroad is a France-first job intelligence platform helping
Tunisian IT profiles find realistic France IT jobs or internships,
compare their CV/profile against job requirements, detect missing
skills, and receive practical guidance before applying.

The product is not a generic job board. It combines job aggregation,
CV/profile parsing, canonical skill matching, recommendations, and
controlled AI explanations.

# 2. MVP Goal

Validate whether Tunisian IT candidates, students, bootcamp graduates,
and internship seekers will use a platform that gives practical job-fit
intelligence for France opportunities.

1.  Find relevant France IT jobs and internships.

2.  Upload or complete a CV/profile.

3.  Receive ranked recommendations.

4.  Understand match score and missing skills.

5.  Save or apply to better-targeted opportunities.

# 3. Product Scope

## 3.1 Included in MVP

- French UI and French email templates.

- Landing page, public job search, job detail pages.

- France Travail API ingestion as primary job source.

- Raw job records and normalized jobs.

- Google, GitHub, and email/password authentication.

- Email verification and password reset.

- Anonymous quick-match teaser.

- PDF CV upload and parsing.

- Manual profile completion.

- Flat canonical skill taxonomy with aliases.

- Rule-based candidate-job fit scoring.

- Recommendation ranking and stored recommendations.

- Controlled OpenRouter LLM explanations and extraction support.

- Saved jobs, match history, email preferences, weekly digest.

- Django Admin dashboard and operational monitoring.

- Privacy basics: consent, policies, delete CV, delete account.

## 3.2 Excluded from MVP

- Employer/recruiter/training-center dashboards.

- Payments/subscriptions.

- Belgium/Luxembourg/Canada/Switzerland jobs.

- LinkedIn profile import, LinkedIn login, Facebook login.

- Auto-apply, chatbot, mobile app, salary prediction, company reviews,
  messaging.

- AI-only scoring or bulk LLM ranking.

- Legal immigration advice or guaranteed employment/relocation claims.

# 4. Personas

| **Persona**         | **Description**                                                              | **Needs**                                                                 |
|---------------------|------------------------------------------------------------------------------|---------------------------------------------------------------------------|
| Junior IT candidate | 0-2 years experience; may target first job, junior role, internship, or PFE. | Realistic recommendations, missing skills, CV guidance.                   |
| Final-year student  | Preparing for PFE, internship, first job, or future France opportunities.    | Market visibility, roadmap, internship filtering, CV/project positioning. |
| Bootcamp graduate   | Candidate entering IT market through bootcamp path.                          | Skill gap roadmap, expectations, project-based proof.                     |
| Mid-level developer | 2-5 years experience targeting France IT roles.                              | Better targeting, stronger CV alignment, advanced skill gaps.             |

Personas are planning profiles. They do not require separate site modes
in MVP.

# 5. User Access Rules

| **User type**      | **Can do**                                                                                    | **Cannot do**                                                             |
|--------------------|-----------------------------------------------------------------------------------------------|---------------------------------------------------------------------------|
| Anonymous visitor  | View landing page, search jobs, view job details, run quick-match teaser.                     | Upload CV, save jobs, receive full recommendations, receive email digest. |
| Authenticated user | Upload CV, complete profile, generate matches, get recommendations, save jobs, manage emails. | Access other users data or admin features.                                |
| Admin user         | Monitor users, profiles, CVs, jobs, ingestion, recommendations, LLM usage, emails.            | Access production secrets from UI.                                        |

# 6. Core User Journeys

## 6.1 Job-First Full Match

6.  User lands on homepage.

7.  User searches France IT jobs or internships.

8.  User opens job detail page.

9.  User clicks Check my match.

10. User signs up/logs in.

11. User uploads CV.

12. System extracts profile data.

13. User confirms and completes missing fields.

14. System calculates fit score and explanation.

15. User saves job or opens source application link.

## 6.2 Anonymous Quick-Match Teaser

16. Anonymous user opens a job.

17. User enters 3-5 skills, experience level, and French level.

18. System returns estimated teaser score, matched skills, and likely
    missing skills.

19. User is prompted to create an account for full CV analysis and
    recommendations.

## 6.3 Profile-First Recommendations

20. User signs up/logs in.

21. User uploads CV.

22. System extracts profile data.

23. User completes profile.

24. System computes recommended France jobs/internships.

25. Dashboard shows ranked recommendations and missing skills.

# 7. Public Pages

| **Page**     | **Requirements**                                                                                                                   |
|--------------|------------------------------------------------------------------------------------------------------------------------------------|
| /            | French landing page with product headline, problem, how it works, target users, France-first scope, CTAs.                          |
| /jobs        | Public job search from local DB with filters and active jobs only by default.                                                      |
| /jobs/\[id\] | Job detail page with title, company, location, contract, description, skills, freshness, source link, quick-match/full-match CTAs. |
| /cv-checker  | Explains CV upload, profile extraction, recommendations, and missing skill analysis; login needed for full upload.                 |
| /login       | Google, GitHub, email/password login.                                                                                              |
| /register    | Google, GitHub, email/password registration with verification for email signup.                                                    |
| /privacy     | Privacy Policy page.                                                                                                               |
| /terms       | Terms page.                                                                                                                        |

# 8. Private Dashboard Pages

| **Page**                     | **Requirements**                                                                                                          |
|------------------------------|---------------------------------------------------------------------------------------------------------------------------|
| /dashboard                   | Profile completeness, CV status, top recommendations, top missing skills, saved jobs, match history, email digest status. |
| /dashboard/profile           | Editable profile: phone, location, LinkedIn, GitHub, portfolio, target roles, target type, languages, preferences.        |
| /dashboard/cv                | Upload/replace active PDF CV, parse status, extracted fields, warnings, delete CV.                                        |
| /dashboard/recommendations   | Ranked jobs with fit score, missing skills, risk flags, filters, freshness.                                               |
| /dashboard/matches           | Historical match analyses with score breakdown and details.                                                               |
| /dashboard/saved-jobs        | Saved jobs with active/stale/expired labels and remove action.                                                            |
| /dashboard/email-preferences | Weekly digest and product update preferences.                                                                             |
| /dashboard/account           | Account settings, delete account/data action.                                                                             |

# 9. Authentication Requirements

- Support Google OAuth, GitHub OAuth, and email/password.

- Email/password users must verify email.

- OAuth users must still complete profile fields.

- If the same verified email appears across providers, the system should
  avoid duplicate accounts where safely possible.

- LinkedIn and Facebook are excluded from MVP.

# 10. Profile Requirements

## 10.1 Profile Fields

- Full name, email, phone, location.

- LinkedIn URL, GitHub URL, portfolio URL, personal website.

- Current level: Student, Internship seeker, Junior, Mid-level, Senior.

- Years of experience.

- Target roles.

- Target country: France for MVP.

- Target type: summer internship, standard internship, PFE/end-of-study
  internship, first job, junior job, mid-level job.

- French level and English level.

- Main technologies and skills.

- Relocation preference and remote preference.

## 10.2 Completeness Score

| **Field group**                       | **Weight** |
|---------------------------------------|------------|
| Active CV uploaded                    | 20         |
| Main skills                           | 20         |
| Target role/type                      | 15         |
| Experience level/years                | 15         |
| French/English level                  | 10         |
| Contact/profile links                 | 10         |
| Location/relocation/remote preference | 10         |

Completeness labels: below 50 = incomplete; 50-79 = usable; 80+ =
strong.

# 11. CV Upload and Parsing Requirements

- MVP accepts PDF only.

- User has one active CV and may replace it.

- Replacing CV triggers parsing and recommendation refresh.

- User may delete CV.

- System must require explicit consent before processing CV.

CV parsing should attempt to extract name, email, phone, location,
LinkedIn, GitHub, portfolio, website, skills, work experience, projects,
education, certifications, languages, and estimated years of experience.

Parse statuses: pending, processing, parsed, parsed_with_warnings,
failed.

# 12. Job Ingestion Requirements

- Primary source: France Travail API Offres d emploi.

- Future alternance source: La Bonne Alternance API if needed.

- External API is used by scheduled ingestion, not per user search.

- Store raw payloads and normalized jobs.

- Track first_seen_at, last_seen_at, last_fetched_at, source status, and
  normalized status.

- Ingestion every 3-6 hours; stale/expiry check every 6-12 hours; full
  cleanup daily.

- High-intent revalidation can refresh a specific old job on
  detail/apply click.

## 12.1 Job Statuses

- active

- stale

- expired

- removed

- archived

Public search shows active jobs by default. Saved jobs may show
stale/expired labels.

# 13. Normalized Job Requirements

- Source name and source job ID.

- Title, company, location, country.

- Contract type, remote type, internship/job type.

- Description and source URL.

- Published date, expiry date if available, first seen, last seen, last
  fetched.

- Required skills, optional skills, experience level, language
  requirements.

- Status and normalization/skill extraction status.

Normalization must tolerate missing source fields. Raw payload remains
the source audit trail.

# 14. Job Search Requirements

- Search local normalized jobs only.

- Filters: keyword, role, skill, location, contract type, internship/job
  type, remote type, experience level, date posted.

- Sort options: newest, most relevant, recently seen, best match for
  logged-in users with profile.

- Job result card shows title, company, location, contract,
  internship/job label, remote type, freshness, extracted skills, and
  View job CTA.

# 15. Skill Taxonomy Requirements

MVP uses a flat canonical skill taxonomy with aliases. Matching must use
canonical skills, not raw extracted strings.

| **Model**             | **Fields / purpose**                                               |
|-----------------------|--------------------------------------------------------------------|
| Skill                 | canonical_name, category, is_active.                               |
| SkillAlias            | skill, alias, normalized_alias.                                    |
| UnknownSkillCandidate | raw skill text, source type, source ID, first seen, review status. |

- Start with 200-300 canonical IT skills.

- Use 500-1000 aliases.

- Unknown extracted skills go to admin review.

- LLM can suggest skills but cannot bypass canonical mapping for
  scoring.

# 16. Matching Requirements

Final candidate-job fit score must be deterministic and explainable. LLM
may support extraction or explanation but is not the scoring authority.

| **Fit score component**        | **Weight** |
|--------------------------------|------------|
| Technical skills match         | 45%        |
| Experience level match         | 20%        |
| Role/title match               | 15%        |
| Language fit                   | 10%        |
| Location/remote/relocation fit | 10%        |

## 16.1 Match Output

- Overall fit score and score breakdown.

- Strong matched skills.

- Missing required and optional skills.

- Experience fit, language fit, location/remote fit.

- Risk flags and recommended actions.

## 16.2 Risk Flags and Profile Signals

- Risk flags: experience_too_low, missing_required_skills,
  french_level_missing, english_level_missing, profile_incomplete,
  job_may_be_expired, internship_type_unclear.

- Profile improvement signals: missing_github, missing_linkedin,
  missing_portfolio. These do not reduce fit score unless the job
  explicitly requires them.

## 16.3 Score Labels

| **Score range** | **Label**      |
|-----------------|----------------|
| 80-100          | Strong match   |
| 65-79           | Good potential |
| 50-64           | Partial match  |
| Below 50        | Weak match     |

# 17. Recommendation Requirements

Recommendations are included in MVP and must be stored instead of
recomputed on every page load.

## 17.1 Active User Definition

Active user = logged in within the last 14 days and has a usable profile
with an active CV or enough manual profile data.

## 17.2 Recommendation Triggers

- CV uploaded or replaced.

- Profile updated.

- New jobs imported.

- Dashboard opened and recommendations are stale.

- Nightly refresh for active users.

## 17.3 Recommendation Algorithm

26. Get user profile and active CV/profile version.

27. Pre-filter active jobs by target role, target type, skill overlap,
    location/remote preferences.

28. Compute deterministic fit score for candidate jobs.

29. Apply ranking score using fit score plus freshness/user preference
    boosts and stale-job penalty.

30. Store top recommendations with score breakdown and reasons.

Recommendation is stale if computed_at is older than 24 hours, the user
profile changed, or the user CV changed.

# 18. AI / LLM Requirements

- Provider: OpenRouter.

- Allowed: CV extraction assistance, job skill extraction assistance,
  match explanation, CV improvement suggestions, missing skill roadmap.

- Forbidden: final score alone, bulk ranking all jobs, every search
  result, no-cache calls, employment guarantees, legal immigration
  advice.

- Cache CV analysis by cv_hash + prompt_version.

- Cache job analysis by source_job_id + job_updated_at + prompt_version.

- Cache match explanation by cv_hash + job_id + prompt_version.

- Track LLM usage logs with prompt type, model/provider, token/cost
  estimate, cache hit/miss, errors.

# 19. Email Requirements

- Required transactional emails: email verification, password reset.

- Optional MVP transactional email: CV analysis completed.

- Weekly recommendation digest is opt-in only.

- Instant high-match alerts are later.

- Digest sends only when user email is verified, opted in, active within
  last 14 days, has usable profile, and has new relevant
  recommendations.

# 20. Saved Jobs Requirements

- Authenticated users can save jobs.

- Saved jobs store user, job, saved date, and status.

- Expired/stale jobs remain visible with warning labels.

- User can remove saved jobs.

# 21. Privacy and Data Rights Requirements

- Privacy Policy page and Terms page are required.

- CV upload requires explicit consent checkbox.

- User can delete CV.

- User can delete account and associated CV/profile/match/recommendation
  data.

- Recommendation emails require opt-in and unsubscribe/preferences link.

- CV files are never public.

- Admin access to CVs and personal data is restricted to staff.

- Platform must avoid employment, relocation, visa, or legal guarantees.

# 22. Admin Dashboard Requirements

Django Admin is acceptable for MVP. Admin must support monitoring, not
only CRUD.

- Users, social accounts, email verification status, last login.

- Profiles, completeness, target role/type, skills, language levels.

- CV uploads, parse status, errors, extracted data.

- Job sources, raw job records, normalized jobs, freshness/status.

- Skill taxonomy, aliases, unknown skill candidates.

- Ingestion runs: fetched, created, updated, expired/stale, errors.

- Match results and recommendations.

- LLM usage logs and cost/cache indicators.

- Email events and delivery failures.

# 23. Data Entities

- User

- SocialAccount

- Profile

- CVUpload

- CVParsedData

- JobSource

- RawJobRecord

- NormalizedJob

- Skill

- SkillAlias

- UnknownSkillCandidate

- JobSkill

- MatchResult

- Recommendation

- SavedJob

- EmailPreference

- EmailEvent

- LLMUsageLog

- IngestionRun

- AccountDeletionRequest or deletion audit record if needed.

# 24. Non-Functional Requirements

| **Area**        | **Requirement**                                                                                         |
|-----------------|---------------------------------------------------------------------------------------------------------|
| Performance     | Public job search must load quickly; dashboard must not wait on long recommendations or LLM calls.      |
| Reliability     | Ingestion, parsing, email, and LLM failures must be logged and visible in admin.                        |
| Security        | CV files private; admin restricted; OAuth secrets in env; uploaded files validated; user data isolated. |
| Privacy         | Consent, deletion, no public CVs, opt-in emails, no unnecessary data collection.                        |
| Scalability     | Handle thousands of jobs, hundreds/low-thousands of users, background jobs, cached LLM outputs.         |
| Maintainability | Scoring logic testable, score breakdown stored, prompt versions tracked, normalization source-specific. |

# 25. Error and Empty States

| **State**               | **Message / behavior**                                                                       |
|-------------------------|----------------------------------------------------------------------------------------------|
| No jobs found           | No matching jobs found. Try removing filters or searching another skill.                     |
| CV parse failed         | We could not extract enough data from your CV. You can still complete your profile manually. |
| Profile incomplete      | Complete your profile to improve recommendations.                                            |
| Recommendations pending | Your recommendations are being prepared. Existing jobs can still be searched manually.       |
| Job expired             | This job may no longer be active. Application availability is not guaranteed.                |

# 26. MVP Acceptance Criteria

## 26.1 Public Website

- Landing page works.

- Public job search works from local database.

- Job detail page works.

- Anonymous quick-match teaser works.

## 26.2 Authentication

- Email/password signup and verification work.

- Google login works.

- GitHub login works.

- Logout works.

- Duplicate account risk is handled by email matching where safe.

## 26.3 CV/Profile

- User can upload PDF CV with consent.

- System extracts basic data.

- User can complete/edit profile.

- Completeness score works.

- User can replace and delete CV.

## 26.4 Jobs

- France Travail ingestion imports jobs.

- Raw records stored.

- Normalized jobs stored.

- Job freshness statuses tracked.

- Expired/stale handling works.

## 26.5 Matching and Recommendations

- User can generate match score.

- Score breakdown shown.

- Strong/missing skills shown.

- Recommendations generated and stored.

- Recommendations refresh after CV/profile change.

## 26.6 AI and Email

- LLM explanations are optional and cached.

- LLM usage is logged.

- Verification/password reset emails work.

- Weekly digest can be enabled/disabled and is not sent without opt-in.

## 26.7 Admin and Privacy

- Admin can monitor users, CVs, jobs, ingestion, skills, matches,
  recommendations, LLM, email events.

- Privacy Policy and Terms exist.

- Delete CV and delete account/data actions work.

# 27. Implementation Priority

| **Phase**                     | **Build focus**                                                                           |
|-------------------------------|-------------------------------------------------------------------------------------------|
| 1\. Foundation                | Django project, PostgreSQL, auth, layout, landing page, profile, admin.                   |
| 2\. Job Data                  | France Travail integration, raw/normalized jobs, ingestion worker, search, job detail.    |
| 3\. CV/Profile                | CV upload, PDF parsing, extracted preview, manual profile completion, completeness score. |
| 4\. Skill Taxonomy            | Canonical skills, aliases, unknown skill review, CV/job skill normalization.              |
| 5\. Matching                  | Rule-based fit score, match result page, quick-match teaser.                              |
| 6\. Recommendations           | Recommendation worker, stored recommendations, dashboard, saved jobs.                     |
| 7\. AI Support                | OpenRouter integration, cached explanations/extraction support, usage logs.               |
| 8\. Emails and Privacy Polish | Email preferences, weekly digest, policy pages, deletion flows, error states.             |

# 28. Locked Product Decisions

- Product name: TuniTech Abroad.

- Candidate market: Tunisia.

- First destination market: France.

- Job source: France Travail API Offres d emploi.

- Future alternance source: La Bonne Alternance API.

- Primary UI language: French.

- Backend: Django.

- Frontend: Django templates + HTMX + Tailwind.

- Database: PostgreSQL.

- Background jobs: Redis + Celery/RQ.

- Auth: Google, GitHub, email/password.

- LLM: OpenRouter, controlled and cached.

- Scoring: rule-based fit score.

- Recommendations: included in MVP.

- Admin: Django Admin included in MVP.

- LinkedIn profile import: excluded from MVP.

- GDPR/privacy basics: included in MVP.

# 29. Next Document

After BRD and PRD review/validation, the next document is Technical
Architecture v1. It should define Django app structure, database schema,
background workers, job ingestion pipeline, skill taxonomy
implementation, CV parsing pipeline, matching engine, recommendation
engine, OpenRouter service, email service, admin implementation,
privacy/data deletion flow, deployment plan, and testing strategy.

# 30. References Used for Planning

- France Travail API Offres d emploi:
  https://www.data.gouv.fr/dataservices/api-offres-demploi

- La Bonne Alternance developer/API space:
  https://labonnealternance.apprentissage.beta.gouv.fr/espace-developpeurs

- CNIL recruitment and GDPR guide:
  https://www.cnil.fr/fr/le-guide-du-recrutement

- LinkedIn Profile API restriction note:
  https://learn.microsoft.com/en-us/linkedin/shared/integrations/people/profile-api
