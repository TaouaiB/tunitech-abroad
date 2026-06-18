# Phase 14B.5 Prompt — Auth/Profile Truth + Full UI Coverage Repair

You are working on TuniTech Abroad, a Django/HTMX/Tailwind France-first job intelligence platform for Tunisian IT candidates.

Read every file in:

```text
docs/phases/phase_14b5_auth_profile_ui_completion/
```

Then execute this phase only. Do not start another phase.

## Hard rules

- Do not deploy.
- Do not commit.
- Do not add React/Vite/Vue/Angular/SPA.
- Do not call OpenRouter from Django views.
- Do not call France Travail from public search.
- Do not expose raw CV text or CV file URLs.
- Do not store OAuth access tokens in profile.
- Use Django templates + Tailwind + HTMX.
- Final verdict must be `BLOCKED_HUMAN_VISUAL_SIGNOFF` unless there is a real failure.

## Manual blockers to fix

1. `/accounts/3rdparty/` has no design.
2. `/accounts/password/set/` has no design.
3. Other allauth pages may still be unstyled; audit all of them.
4. OAuth GitHub/Google flows do not clearly support linking providers later.
5. OAuth-created accounts need a visible set-password option.
6. Google/GitHub provider data is not reliably used to fill profile.
7. Avatar/photo from provider is not captured/displayed.
8. Target country appears in profile/CV UI even though MVP is France-only.
9. CV parse/profile/recommendations still disagree about missing fields.
10. Recommendation page lists fields as missing when profile UI/DB has them.
11. Emails still say `example.test` or confusing confirmation/reset copy.

## Required implementation

### A. Full route/template audit

Before coding, enumerate all `/accounts/` and `/dashboard/` pages and installed allauth templates. Create a temporary checklist in your notes or `implementation_plan.md`. You must not only style pages already reported by Baha.

### B. Profile truth

Create or confirm one authoritative missing-field method in the profile service layer. Use it everywhere:

- profile page
- dashboard profile card
- recommendations blocked state
- tests

Do not list phone/location missing if profile DB has phone/location.

Rename UI labels:

- `Current level` -> `Niveau de carrière`
- `Years experience` -> `Années d’expérience`
- `Target roles` -> `Rôles ciblés`
- `Target type` -> `Type d’opportunité recherchée`
- `Remote preference` -> `Préférence télétravail`
- `Relocation preference` -> `Mobilité / relocalisation`

Remove `target_country` from user-visible UI.

### C. CV parse/profile sync

- Fill empty profile phone/location/link fields from parsed CV.
- Infer `current_level` only when obvious.
- Do not hallucinate years experience.
- Do not hallucinate target country.
- Recalculate completion after parse/save.
- CV page must show extracted fields clearly.

### D. Recommendations

- Recommendation blocked reason must be exact and sourced from the same missing-field service.
- If profile usable and active jobs exist, recommendations must show cards.
- Do not show `Aucune offre ne correspond` for incomplete profiles.

### E. Allauth UI coverage

Style every user-facing account/socialaccount page, including but not limited to:

- `/accounts/3rdparty/`
- `/accounts/password/set/`
- `/accounts/confirm-email/`
- token email confirmation template
- password reset/change templates
- email management templates
- social signup/error/provider connection templates

Use one reusable visual system.

### F. Email copy/domain

- Configure local Site/domain/name so allauth does not use `example.test`.
- Override allauth email templates that produce user-visible emails.
- Verification email must include a confirmation link.
- Duplicate-account email must not pretend to be a confirmation email.

### G. Social connections

Add or fix:

```text
/dashboard/account/connections/
```

It must show Google and GitHub state, connect actions, safe disconnect actions, and set-password CTA where relevant.

Explain provider account switching honestly. GitHub/Google may reuse the browser provider session. Provide user-facing guidance rather than pretending the app can always force account selection.

### H. Provider data and avatar

Use provider data where available:

- full name
- email
- GitHub profile URL
- avatar/photo URL

If no model field exists for avatar, add a narrow `avatar_url` field to the profile model with a migration. Store URL only. Do not download or proxy the image now.

## Required commands

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py migrate --settings=config.settings.local
python manage.py seed_demo_data --settings=config.settings.local
python manage.py test apps.accounts apps.profiles apps.cvs apps.recommendations apps.dashboard --settings=config.settings.local
python manage.py test --settings=config.settings.local
```

If a migration is intentionally needed for `avatar_url`, create it, then rerun migration checks.

## Required proof

In final report include:

- all `/accounts/` pages/templates audited
- all pages styled
- profile DB vs missing fields proof
- recommendation blocked reason proof
- OAuth connection page screenshot/description
- provider data mapping tests
- email template/domain proof
- full test results
- security grep results

Final verdict must be:

```text
BLOCKED_HUMAN_VISUAL_SIGNOFF
```

unless something fails, then use `FAIL`.
