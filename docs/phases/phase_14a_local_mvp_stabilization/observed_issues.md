# Observed Current Issues From Local Testing

The agent must treat these as starting evidence and verify them in code/tests before fixing.

## 1. Anonymous quick match stale result / stuck processing state

Observed behavior:

- Anonymous quick match works the first time.
- User presses Chrome back button.
- User adds `React` as a skill.
- Match button still appears stuck in processing.
- Clicking again shows the previous result instead of recalculating with changed skills.

Required repair direction:

- Server must not cache quick match results incorrectly across changed form payloads.
- HTMX target/swap must update only the result area, not destroy the form state incorrectly.
- Button disabled/processing state must reset after request completion and browser back/forward cache restore.
- Add no-browser regression tests using Django client/template assertions.

## 2. `/recommendations/` 404 leaks DEBUG URLconf data

Observed behavior:

- `/recommendations/` returns Django debug 404 page showing URL patterns when `DEBUG=True`.

Required repair direction:

- Correct canonical private URL is `/dashboard/recommendations/`.
- With `DEBUG=False`, 404 must use safe custom template and must not expose URLconf patterns.
- Optional: add redirect from `/recommendations/` to `/dashboard/recommendations/` if product navigation currently links wrongly.
- Fix wrong links that point to `/recommendations/`.

## 3. Dashboard recommendations stay pending forever

Observed behavior:

- `/dashboard/recommendations/` shows refreshing/pending state.
- Recommendation runs may show success but zero stored recommendations.

Required repair direction:

- Recommendation page must distinguish: incomplete profile, no active CV, no active jobs, refresh in progress, refresh failed, zero matches after scoring.
- For usable profile + active jobs, `JobRecommendation` rows must be generated and stored.
- Dashboard must read stored recommendations; heavy computation must not block page load.

## 4. CV parser extracts text and skills but not enough structured profile fields

Observed behavior from synthetic PDF:

- Raw text extracted.
- Name extracted into `CVParsedData`.
- Email and phone extracted.
- Many skills extracted.
- Location, LinkedIn, GitHub, portfolio remain blank despite visible values in the PDF text.
- CandidateProfile only filled phone and some skills; profile completion remained low.

Required repair direction:

- Deterministic extractor must handle `LinkedIn: linkedin.com/in/...`, `GitHub: github.com/...`, `Portfolio: domain.example.com` without scheme.
- Extract `Tunis, Tunisia` as location from header/contact line.
- Normalize URLs to `https://...` when needed.
- Store extracted fields in `CVParsedData`.
- Prefill CandidateProfile only where empty; do not silently overwrite user-confirmed or non-empty fields.
- If CV name conflicts with existing profile full name, keep profile value and surface a warning/conflict.

## 5. LLM implementation incomplete or not fully wired

Observed behavior:

- Settings showed `LLM_ENABLED=True` and OpenRouter key exists.
- LLM app models list only `LLMRequestLog`.
- Search found no visible explain route.

Required repair direction:

- Align code with actual model names, or add missing models/migrations only if required by current schema and acceptance.
- Controlled LLM service must support real call, cache/rate-limit/logging behavior, and disabled/failure-safe mode.
- Match explanation endpoint must exist only if within MVP scope and must call service, not OpenRouter from view.
- Real LLM validation must be service-level and limited.

## 6. Real France Travail ingestion command missing or insufficient

Observed behavior:

- Existing command list showed fixture ingestion and seed source only.
- No clear small real France Travail sync command appeared.

Required repair direction:

- If service/client exists, add/repair a safe management command for small real ingestion smoke.
- It must call ingestion service/client only, persist raw records, normalize locally, and report counts.
- It must not be used by public job search.
- It must not print credentials.

## 7. ProfileSkill model field mismatch risk

Observed behavior:

- A shell script attempted `ProfileSkill.objects.update_or_create(profile=p, skill=skill, ...)` and failed because current `ProfileSkill` fields were `raw_name`, `normalized_name`, etc., not `skill`.

Required repair direction:

- Do not blindly change schema unless necessary.
- Inspect current model and schema/migrations.
- Tests and services must use actual model fields.
- If the implementation intentionally diverged from planning schema, report the divergence and stabilize without breaking migrations.
