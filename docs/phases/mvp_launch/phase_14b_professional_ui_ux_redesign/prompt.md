# Phase 14B Prompt — Paste into Gemini / Antigravity

```text
You are working on TuniTech Abroad Phase 14B — Professional UI/UX Redesign and Browser QA.

Read AGENTS.md first.
Then read all files in:
docs/phases/phase_14b_professional_ui_ux_redesign/

If available, read:
docs/phases/phase_14a_local_mvp_stabilization/agent_report.md

Also read relevant planning documents if present:
docs/planning/PRD_v1.pdf
docs/planning/BRD_v1.pdf
docs/planning/Implementation_Roadmap_v1.pdf
docs/planning/Service_Contracts_v1.pdf
docs/planning/Page_URL_View_Map_v1.pdf

Work only on Phase 14B.

Current project status:
- Backend/local MVP stabilization is complete.
- Real OpenRouter smoke validation passed in Phase 14A.
- Real France Travail Offres d’emploi v2 ingestion passed in Phase 14A.
- Local DB has normalized active jobs.
- Current weakness is UI/UX: pages look like raw Django prototype, not a professional modern product.

Main goal:
Transform the existing Django/HTMX/Tailwind UI into a professional, modern, youthful, France-first MVP interface without changing the approved stack or adding future product features.

Design direction:
- Modern SaaS/job intelligence platform.
- Youthful, clean, confident.
- France-first.
- Friendly for Tunisian IT students, juniors, bootcamp graduates, internship seekers, and mid-level developers.
- Professional enough for a portfolio/recruiter demo.
- French UI by default.
- Technical terms may remain in English where natural.

Approved frontend stack:
- Django templates
- Tailwind CSS
- HTMX
- Minimal Alpine.js only if already needed and justified

Forbidden:
- React
- Next.js
- Vue
- Angular
- SPA architecture
- FastAPI
- MongoDB
- SQLAlchemy
- Bootstrap
- Material UI
- paid UI kits
- new backend product features
- deployment
- committing

Hard architecture rules:
- Views stay thin.
- Services own business logic.
- Celery tasks call services only.
- Models store data only.
- No OpenRouter/LLM calls from views.
- No live France Travail call during normal /jobs/ search.
- Public search reads local PostgreSQL only.
- Public URLs use UUID public_id, never internal integer IDs.
- CV files remain private.
- Never print or commit secrets.
- Do not expose raw CV text in UI.

Pages to redesign/check:
- /
- /jobs/
- /jobs/<uuid>/
- /accounts/login/
- /accounts/signup/
- /accounts/password/reset/
- /accounts/password/change/
- /accounts/email/
- /dashboard/
- /dashboard/profile/
- /dashboard/cv/
- /dashboard/recommendations/
- /dashboard/matches/
- /dashboard/matches/<uuid>/
- /dashboard/saved-jobs/
- /dashboard/email-preferences/
- /dashboard/account/
- /dashboard/settings/delete-account/
- /privacy/
- /terms/
- custom 404
- custom 500

UI system tasks:
1. Create or update a shared design system in templates:
   - layout container
   - navigation
   - cards
   - buttons
   - badges
   - forms
   - alerts
   - empty states
   - loading states
   - score blocks
   - skill chips
   - job cards
   - dashboard cards
   - danger zones

2. Update base template:
   - responsive navigation
   - logged-in/logged-out nav
   - consistent footer
   - mobile-friendly layout
   - no placeholder phase text
   - no example.test text

3. Homepage:
   - modern hero
   - clear value proposition
   - CTAs: Explorer les offres, Analyser mon CV
   - how-it-works section
   - target users section
   - France-first scope
   - feature cards: offres, CV, matching, compétences manquantes, recommandations
   - no fake claims

4. Jobs page:
   - professional filter panel
   - responsive job cards
   - better skill chips
   - badges for contract/remote/experience/freshness
   - empty state
   - pagination styling
   - keep search local PostgreSQL only

5. Job detail page:
   - strong header
   - meta badges
   - readable description
   - skills section
   - quick match card
   - full match CTA
   - save job CTA
   - source link
   - stale/expired warning if applicable

6. Quick match:
   - improve visual design
   - maintain HTMX behavior
   - loading state
   - result card
   - no stale button state
   - no LLM
   - no CV
   - no recommendations

7. Dashboard:
   - summary cards
   - profile completeness
   - CV status
   - recommendations preview
   - saved jobs preview
   - matches preview
   - missing skills preview if data exists
   - clear next actions

8. Profile page:
   - group fields into sections:
     Informations personnelles
     Présence professionnelle
     Objectif France
     Langues
     Expérience
     Compétences
     Préférences
   - improve labels/help text
   - show completion guidance
   - preserve backend behavior

9. CV page:
   - upload zone
   - consent box
   - active CV card
   - parse status
   - parsed fields summary
   - warnings
   - detected-but-not-applied values if available
   - delete/replace actions
   - never expose private file URL
   - never show raw full CV text

10. Recommendations:
   - incomplete profile blocked state
   - no jobs state
   - failed run state
   - pending state only when truly pending
   - recommendation cards with fit score, title, company, location, missing skills, reasons, save CTA
   - no infinite refreshing state

11. Match pages:
   - score hero
   - score label
   - score breakdown bars
   - matched skills
   - missing skills
   - risk flags
   - recommended actions
   - job summary
   - LLM explanation area only if existing route/service exists; do not invent unsafe LLM-from-view logic

12. Saved jobs:
   - saved job cards
   - stale/expired labels
   - empty state
   - remove action styling

13. Email preferences:
   - clear preferences form
   - digest explanation
   - unsubscribe/status copy

14. Account/delete:
   - account settings layout
   - danger zone
   - confirmation design
   - serious deletion warning

15. Auth pages:
   - login/signup/password reset/change/email pages styled consistently
   - social buttons
   - validation errors
   - email verification copy

16. Legal/error pages:
   - privacy and terms readable
   - custom 404/500 polished
   - DEBUG=False custom 404 must not expose URL patterns

Content/copy rules:
- French UI by default.
- Remove “Phase 1 Note”.
- Remove “future phase” placeholder text.
- Remove “example.test”.
- Remove “Lorem ipsum”.
- Do not claim guaranteed jobs, visas, or relocation.
- Do not claim AI decides final score.
- Do not claim real production scale.

Autonomous loop:
Maximum repair loops: 15.

For each loop:
1. Inspect current UI/templates/static/forms.
2. Implement a coherent batch of improvements.
3. Run focused tests.
4. Run full tests when needed.
5. Start local server.
6. Use browser testing to inspect pages visually.
7. Check server logs and browser console if available.
8. Fix exact root cause.
9. Repeat until acceptance passes.

Required commands:
cd ~/Projects/tunitech-abroad
source .venv/bin/activate
docker compose up -d postgres redis || true
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py migrate --settings=config.settings.local
python manage.py seed_demo_data --settings=config.settings.local
python manage.py test --settings=config.settings.local

Start server for browser QA:
python manage.py runserver 127.0.0.1:8000 --settings=config.settings.local

Browser QA checklist:
- home page loads and looks modern
- jobs page has polished filters/cards
- job detail looks polished
- quick match result looks polished and does not get stuck
- signup/login pages look polished
- dashboard looks like real MVP, not placeholder
- profile form is grouped and readable
- CV page shows useful upload/parse states
- recommendations page has clean states/cards
- match detail has score breakdown and missing skills
- saved jobs page looks polished
- email preferences page looks polished
- account/delete pages are clear
- privacy/terms readable
- custom 404 works under DEBUG=False
- mobile viewport does not break layouts

Regression/security checks:
- grep -R "Phase 1 Note\|Lorem\|example.test\|future phase" templates apps -n || true
- grep -R "\.file.url\|cv.file.url\|raw_text" templates apps --exclude-dir="tests" -n || true
- grep -R "FranceTravailClient\|search_offers" apps/jobs/views.py apps/jobs/services/search.py templates -n || true
- grep -R "OpenRouter\|LLM" apps/*/views.py templates -n || true

Acceptance:
- Full Django tests pass.
- No migrations unless clearly needed.
- No secrets printed.
- No CV file URL exposed.
- No raw CV text exposed.
- /jobs/ still uses local PostgreSQL.
- Quick match still anonymous and LLM-free.
- Dashboard no longer shows placeholder phase text.
- Recommendations page has clear non-stuck states.
- Main pages visually coherent on desktop and mobile.
- No page looks like default Django/admin prototype.
- No React/Next/Vue/SPA added.
- No deployment performed.
- No commit performed.

Final report must include:
1. PASS / FAIL / BLOCKED
2. Design summary
3. Pages redesigned
4. Components created/updated
5. Files changed
6. Commands run and results
7. Browser pages tested
8. Mobile checks done
9. Bugs found and fixed
10. Remaining visual weaknesses
11. Security/privacy checks
12. Confirmation no forbidden stack was added

Do not claim PASS if:
- Full tests were not run.
- Browser QA was not done.
- Main pages still look unstyled.
- Placeholder phase text remains.
- Mobile layout is broken.
- CV private file URL is exposed.
- OpenRouter is called from a view/template.
- France Travail is called from public search.
- React/Next/Vue/SPA was added.
```
