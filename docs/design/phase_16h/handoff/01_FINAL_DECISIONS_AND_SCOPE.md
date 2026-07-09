# Final Decisions and Scope

## Final accepted UI version

**TuniAtlas full prototype v16 is final.**

Do not keep iterating visually unless a real implementation constraint requires a small adjustment.

## Product direction

TuniAtlas is a jobs-first platform for Tunisian tech talent targeting jobs abroad, currently France-focused.

Core user flow:

1. User lands on jobs page.
2. User browses jobs without signing in.
3. Auth is required for CV/profile/recommendations/saved jobs/settings.
4. User creates account or uses OAuth.
5. User completes profile stepper.
6. User uploads CV.
7. User receives recommendations and match scores.
8. User applies externally on the job source website.

## Locked page strategy

- `index.html` is the landing page and jobs page.
- No separate dashboard.
- No separate stage/alternance pages. Stage and alternance are filters/tabs inside the jobs page.
- Footer only needs About us link.
- About page contains contact/privacy/terms/delete-account summary areas but should stay compact.
- No admin UI in this prototype.

## Locked job behavior

- Job cards only have Save action.
- Applying/postulating happens only in job detail or match score page.
- Applications happen on external websites.
- Do not add “already applied” state.
- Do not show expired jobs.
- Do not add urgent job state.
- France-only filter exists and is checked/disabled.
- Job freshness labels: Today, 1 day ago, 2 days ago, 3 days ago, then date.

## Locked auth/profile behavior

- Header menu contains: Profile, Settings, Sign out.
- No More menu.
- No arrows inside account menu.
- Auth includes Google/GitHub buttons and email/password fields.
- Signup has verify password validation while typing.
- Password minimum is 6 characters and validates live.
- Email fields validate live while typing.
- Account activation means email confirmation, not password creation.
- Account activation banner says user must confirm email sent to mailbox.
- OAuth signup still routes to Step 1: create password.
- Profile stepper final logic: Set password → CV → Profile.

## Locked language/theme behavior

- Header has dark/light switch.
- Header has EN/FR switch.
- The EN/FR switch must translate visible UI labels on all pages.
- Preserve concise French copy.
- Do not add long explanations in either language.

## Locked wording style

Use compact labels and action text. Avoid unnecessary helper text.

Remove/avoid wording such as:

- OAuth account.
- Optional.
- Check extracted data.
- Upload or replace file.
- or email
- Any repeated explanation below obvious labels.

Keep only:

- labels
- actions
- validation errors
- status text
- short user-facing state text

## What is allowed after v16

Allowed only if needed during implementation:

- Convert repeated HTML to reusable templates/components.
- Map static prototype data to backend data.
- Replace demo interactions with real Django/HTMX endpoints.
- Preserve responsive/mobile behavior.
- Preserve styling tokens.
- Make minor accessibility improvements if visual result remains the same.

## What is not allowed

- Redesigning the UI.
- Changing colors/theme/typography.
- Adding extra explanatory text.
- Adding new visible pages unless required by backend flow.
- Adding already-applied/expired/urgent job states.
- Adding admin UI.
- Splitting stage/alternance into separate pages.
