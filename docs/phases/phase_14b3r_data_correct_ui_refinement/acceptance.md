# Acceptance — Phase 14B.3R

## Overall verdict rules

PASS requires all of these:

- full test suite passes
- multi-CV fixture tests pass
- extractor accepts required fields and rejects noise
- profile application works
- recommendations states work
- UI pages render correctly
- security/privacy greps pass
- Baha manually approves Chrome visual/product flow

If all automated gates pass but Baha has not visually approved:

```text
BLOCKED_HUMAN_VISUAL_SIGNOFF
```

## CV extraction gates

For the Aymen CV fixture:

- `extracted_name = Aymen Ben Salah`
- `extracted_email = aymen.bensalah.test@example.test`
- `extracted_phone` contains `+216 55 123 456`
- `extracted_location = Tunis, Tunisia`
- `extracted_linkedin_url = https://linkedin.com/in/aymen-bensalah-test`
- `extracted_github_url = https://github.com/aymen-bensalah-test`
- `extracted_portfolio_url = https://aymen-dev.example.test`
- `website_url` is empty or `https://aymen-dev.example.test`
- `website_url` is never `https://Next.js`
- `target_roles` includes:
  - Junior Full Stack Developer
  - Frontend Developer
  - Backend Developer
  - Web Developer Intern
  - Software Developer Intern
  - React Developer
  - Node.js Developer

## Multi-CV coverage gates

At least five fixtures must exist and pass:

- clean English CV
- French CV
- student/PFE CV
- messy multiline links CV
- incomplete CV

## Skill noise gates

Raw or saved skills must not include obvious noise:

- section headings
- countries
- employers
- dates/months
- full sentence fragments
- project names unless explicitly allowed

Hard forbidden saved skills:

```text
PROJECTS
EDUCATION
PROFESSIONAL EXPERIENCE
CERTIFICATIONS
LANGUAGES
Tunis
Tunisia
France
Belgium
Luxembourg
Canada
Local Clients
DigitalBridge Labs
Private University of Tunis
March 2025
August 2025
and role
and error cases
```

## Profile application gates

After parsing the Aymen CV into an empty/partial profile:

- phone filled
- location filled
- LinkedIn filled
- GitHub filled
- portfolio or website filled with valid portfolio, not `Next.js`
- target roles filled if model supports it
- language fields filled with valid values
- profile skills created
- profile completion increases
- existing non-empty different full_name is not silently overwritten
- detected-but-not-applied name conflict is visible or stored as warning

## Profile completion gates

- empty profile does not show 100%
- `profile_completion_score` and `completion_percentage` are aligned or one is removed/normalized
- UI uses the authoritative score
- missing fields are listed clearly

## Recommendation gates

For incomplete profile:

- no fake `success` run with zero recommendations
- blocked state gives exact missing fields
- UI does not say generic `Aucune offre ne correspond`

For complete profile + active jobs:

- recommendations are generated or displayed
- `JobRecommendation.objects.filter(user=user).count() > 0`
- recommendation cards show job title/company/score/missing skills/actions

For no active jobs:

- explicit no-jobs state

For generation failure:

- explicit failed state

## UI gates

- CV page shows all extracted fields available in `CVParsedData`
- profile page uses French labels
- profile page shows missing fields
- recommendations page has first-class blocked/ready/no-jobs/no-match/failed states
- logged-in users do not see signup CTAs
- quick match does not look like raw native form
- match detail has clear score/breakdown/actions
- mobile layout acceptable

## Security gates

- no raw CV text in templates
- no CV file URL in templates
- no private media URL in templates
- no secrets in diff
- no OpenRouter calls from views/templates
- no France Travail client call from public search path
- no forbidden frontend stack

## Commands required

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py migrate --settings=config.settings.local
python manage.py seed_demo_data --settings=config.settings.local
python manage.py test apps.cvs apps.profiles apps.recommendations apps.matching --settings=config.settings.local
python manage.py test --settings=config.settings.local
```
