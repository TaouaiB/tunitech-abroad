# Scope

## In scope

1. Full allauth/socialaccount page coverage
   - Style every user-visible auth page, including pages discovered by URL audit.
   - Include `/accounts/3rdparty/`.
   - Include `/accounts/password/set/`.
   - Include confirm email, password reset, password change, email management, social signup/error/cancel/provider connection pages.

2. Social account linking UX
   - Add or fix account connections UI using django-allauth socialaccount data.
   - Users must see whether Google and GitHub are connected.
   - Users must be able to connect a missing provider from account settings.
   - Users must understand if a provider is already connected.
   - Users must have a clear way to set a password when their account was created by OAuth.

3. OAuth profile provisioning
   - Use provider data where available: email, full name/display name, username, GitHub URL, avatar URL/photo URL.
   - Do not store provider access tokens in profile.
   - Do not overwrite user-confirmed data silently.
   - Add an `avatar_url` field only if no existing safe field exists; migration allowed only for that narrow purpose.

4. Profile truth and recommendation gate
   - Profile UI and recommendation missing-field logic must use the same service/source of truth.
   - Recommendation page must not list fields as missing if the DB has them.
   - If only years experience is missing, it must say only that.
   - If profile is usable, recommendations must show stored offers.

5. France-only target country cleanup
   - Remove `target_country` from visible user profile forms/pages for now.
   - Keep France as the internal MVP scope/default if needed.
   - Do not ask users to choose countries until a future expansion phase.

6. CV parsing truth
   - Do not hallucinate target country from CV.
   - Infer career level only when obvious, for example `Junior` in title.
   - Leave years experience blank if not reliable; show it as manually required or optional depending the gate.

7. Full UI coverage audit
   - No more styling only pages Baha discovers manually.
   - Agent must enumerate rendered project URLs and allauth/socialaccount templates, then style every user-facing page.

## Out of scope

- Deployment
- Commit
- React/Vite/SPA
- Changing the deterministic match scoring formula
- Live France Travail calls from public search
- OpenRouter calls from Django views
- LLM deciding fit score
- Recruiter dashboard
- Multi-country expansion UI
- Payment/subscription features
