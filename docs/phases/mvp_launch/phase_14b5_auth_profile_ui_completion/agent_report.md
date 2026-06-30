# Phase 14B.5 Agent Final Report

## A. Full Route/Template Audit & Allauth UI Coverage
All `/accounts/` pages and installed allauth templates were audited and confirmed to be styled with the project's Tailwind CSS classes. This includes:
- `/accounts/login/` (`login.html`)
- `/accounts/signup/` (`signup.html`)
- `/accounts/password/set/` (`password_set.html`)
- `/accounts/confirm-email/` (`email_confirm.html`)
- `/accounts/3rdparty/` (`socialaccount/connections.html`)

## B. Profile Truth
A central, authoritative method `ProfileCompletenessService.get_missing_fields(profile)` was created. It uses the exact requested French UI labels (e.g., `Nom complet`, `Niveau de carrière`, `Années d’expérience`). This logic is now uniformly used across:
- The dashboard profile view (`apps/dashboard/views.py`) to show suggestions and missing fields alerts.
- The `ProfileCompletenessService.calculate` method.
- The `RecommendationQueryService` to formulate the exact `blocked_reason`.

`target_country` was removed from the user-visible UI form (`ProfileForm`).

## C. CV Parse / Profile Sync
- The CV parser extracts phone, location, and links and seamlessly updates the profile if those fields are missing.
- `current_level` is inferred conservatively based on `estimated_years_experience` if it is not explicitly captured.
- Experience is taken solely from deterministic regex extraction (preventing hallucinations).
- `target_country` references were completely avoided in extraction and profile sync.
- Profile completeness score is recalculated immediately after saving.

## D. Recommendations Blocked Reason
The `RecommendationQueryService` now sources the blocked reason using the exact `get_missing_fields` output. If the profile is usable and active jobs exist, cards are displayed correctly.

## E. Email Template/Domain Proof
The `seed_demo_data.py` script automatically initializes the Django `Site` (ID=1) to `localhost:8000`, solving the `example.test` domain issue.
Custom email overrides were added for:
- `email_confirmation_subject.txt`
- `email_confirmation_message.txt`
- `account_already_exists_subject.txt`
- `account_already_exists_message.txt`

These provide clear, user-facing instructions and use the correct `activate_url`.

## F. Provider Data Mapping Tests
Signals were added to `apps/accounts/signals.py` for both `user_signed_up` and `social_account_added`. 
They correctly map the provider's `name` / `full_name`, `avatar_url` (from `picture` or `avatar_url`), and `github_url` directly to the `CandidateProfile`.

An `avatar_url` field was successfully added to `CandidateProfile` via migration.

## G. OAuth Connection Page Description
The `/dashboard/account/connections/` (`socialaccount/connections.html`) template was styled and now:
- Shows the connection state for Google and GitHub.
- Offers safe connect and disconnect actions.
- Displays an honest explanation about how providers may reuse the browser session.
- Displays a prominent **"Mot de passe manquant"** CTA prompting the user to define a password if they only signed up via OAuth.

## H. Full Test Results
```text
Found 101 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
----------------------------------------------------------------------
Ran 101 tests in 5.825s

OK
Destroying test database for alias 'default'...
```

## I. Security Grep Results
Grep for `OpenRouter` confirmed that it is only used in the `apps/llm/` service files. No OpenRouter calls exist in Django views.

## Final Verdict
```text
BLOCKED_HUMAN_VISUAL_SIGNOFF
```
