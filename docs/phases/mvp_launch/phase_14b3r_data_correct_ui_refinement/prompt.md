# Prompt — Phase 14B.3R

You are working on TuniTech Abroad Phase 14B.3R — Data-correct UI Refinement with Multi-CV Coverage.

Read these files first:

```text
docs/phases/phase_14b3r_data_correct_ui_refinement/README.md
docs/phases/phase_14b3r_data_correct_ui_refinement/scope.md
docs/phases/phase_14b3r_data_correct_ui_refinement/boundaries.md
docs/phases/phase_14b3r_data_correct_ui_refinement/observed_issues.md
docs/phases/phase_14b3r_data_correct_ui_refinement/visual_reference_analysis.md
docs/phases/phase_14b3r_data_correct_ui_refinement/multi_cv_fixture_requirements.md
docs/phases/phase_14b3r_data_correct_ui_refinement/tasks.md
docs/phases/phase_14b3r_data_correct_ui_refinement/acceptance.md
docs/phases/phase_14b3r_data_correct_ui_refinement/test_plan.md
docs/phases/phase_14b3r_data_correct_ui_refinement/regression_security_checks.md
```

Also read `AGENTS.md`.

## Mission

Fix the failed product flow and UI correctness from Phase 14B/14B.1/14B.2.

Do not do another broad redesign. Fix the data-correct user journey:

```text
CV parse → profile application → truthful completion → recommendation eligibility → recommendation display → polished state UI
```

## Known confirmed failures

- `website_url` has previously become `https://Next.js`. This must never happen.
- Fresh extractor gets Aymen CV location/linkedin/github/portfolio, but `target_roles` is still empty.
- Raw skills are noisy and include countries/employers/section titles.
- Profile application does not reliably clean stale bad profile values.
- Recommendations can show vague no-match state when profile is incomplete.
- Profile completion has had contradictory values.
- UI still needs stronger design based on the provided visual reference, but using Django/Tailwind/HTMX only.

## Hard rules

- No deploy.
- No commit.
- No React, Next.js, Vue, Angular, Vite, SPA.
- No Bootstrap/Material UI.
- No external icon packages.
- No OpenRouter from views.
- No France Travail live call from public `/jobs/` search.
- No raw CV text in UI.
- No private CV file URL in UI.
- No secrets printed.
- Do not change deterministic scoring formula.
- Do not hallucinate missing CV fields.
- Do not hardcode the Aymen CV only.

## Required implementation

### 1. Multi-CV extractor tests

Add at least five raw text fixtures as described in `multi_cv_fixture_requirements.md`.

Tests must cover:

- clean English CV
- French junior/stage CV
- student/PFE CV
- messy multiline links CV
- incomplete CV

Aymen fixture must assert:

```text
extracted_location = Tunis, Tunisia
extracted_linkedin_url = https://linkedin.com/in/aymen-bensalah-test
extracted_github_url = https://github.com/aymen-bensalah-test
extracted_portfolio_url = https://aymen-dev.example.test
website_url is empty or https://aymen-dev.example.test, never https://Next.js
target_roles contains all roles from TARGET ROLES section
raw_skills excludes noise
```

### 2. URL extraction

Fix deterministic extractor:

- Accept protocol-less links.
- Normalize to `https://`.
- Prefer explicit labels.
- Never extract skill tokens as websites.
- Add negative tests for `Next.js`, `React`, `Node.js`, `Django`, `PostgreSQL`.

### 3. Target roles

Extract target roles from sections:

```text
TARGET ROLES
RÔLES CIBLÉS
POSTES CIBLÉS
OBJECTIF
TARGET POSITION
```

Stop at next section heading. Return clean list.

### 4. Skill cleanup

Use taxonomy/allowlist where available. Filter noise:

- countries
- cities when used as location
- employers
- section headings
- months/years
- sentence fragments
- project names unless in known technical skills

Keep real tech skills.

### 5. Profile application

- Empty fields get filled from parsed CV.
- Existing full_name is not silently overwritten if different.
- Bad CV-derived stale `website_url=https://Next.js` is cleaned/replaced by valid extracted portfolio/website.
- Do not wipe user-entered fields unless invalid and known CV-derived.
- Create/update ProfileSkill rows from clean skills.
- Recalculate profile completion after parse.

### 6. Profile completion

- Fix split-brain between `profile_completion_score` and `completion_percentage`.
- One value must drive UI.
- Empty profile must not show 100%.
- Partial CV profile should have realistic percentage.
- Complete profile should reach useful threshold.

### 7. Recommendations

- Incomplete profile returns blocked state with exact missing fields.
- Complete profile + active jobs generates/stores recommendations.
- `RecommendationRun` must not say success when skipped for incomplete profile.
- Distinguish:
  - incomplete profile
  - no active jobs
  - no matching jobs
  - failed generation
  - recommendations available

### 8. UI correctness and visual refinement

Use `visual_reference_analysis.md`.

Improve:

- CV page extracted field display
- detected-but-not-applied fields
- profile missing fields
- recommendations blocked/ready cards
- match result clarity if touched
- quick match readability if touched
- French labels

Do not expose raw CV text or file URL.

## Required commands

Run all:

```bash
cd ~/Projects/tunitech-abroad
source .venv/bin/activate

docker compose up -d postgres redis || true

python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py migrate --settings=config.settings.local
python manage.py seed_demo_data --settings=config.settings.local
python manage.py test apps.cvs apps.profiles apps.recommendations apps.matching --settings=config.settings.local
python manage.py test --settings=config.settings.local
```

## Browser/headless checks

Start server:

```bash
python manage.py runserver 127.0.0.1:8000 --settings=config.settings.local
```

Check at least:

- `/dashboard/cv/`
- `/dashboard/profile/`
- `/dashboard/recommendations/`
- `/dashboard/matches/`
- one match detail
- `/jobs/`
- one job detail
- quick match
- login/signup/password reset

## Human sign-off

Do not mark PASS until Baha manually approves the Chrome UI. If everything else passes but Baha has not approved, use:

```text
BLOCKED_HUMAN_VISUAL_SIGNOFF
```

## Final report

Fill:

```text
docs/phases/phase_14b3r_data_correct_ui_refinement/agent_report.md
```

Use the template in `agent_report_template.md`.
