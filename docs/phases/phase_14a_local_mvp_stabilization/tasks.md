# Tasks

## TTA-14A-000 — Preflight and current-state audit

Run preflight commands from `preflight.md`.

Deliverables:

- Confirm branch and working tree state.
- Confirm PostgreSQL is reachable.
- Confirm Redis/cache is reachable or report blocker.
- Confirm full test discovery finds tests.
- Record current failing tests before changing code.
- Inspect current models/services/routes/templates before modifying.

Acceptance:

- No edits before preflight summary is known.
- If DB is unreachable and cannot be started once safely, report `BLOCKED_DB`.

## TTA-14A-001 — Stabilize CV extraction and profile prefill

Repair deterministic and optional LLM extraction so the sample text-based PDF produces useful structured data.

Must support at minimum:

- Full name in `CVParsedData`.
- Email.
- Tunisian phone.
- Location from contact/header line.
- LinkedIn URL with or without scheme.
- GitHub URL with or without scheme.
- Portfolio URL with or without scheme.
- Website URL where present.
- Main technical skills without excessive noisy phrases.
- Estimated years experience if reliably extracted by LLM or deterministic heuristic.
- Languages if present.
- Warnings for conflicts and low-confidence fields.

Rules:

- CandidateProfile can be prefilled only where fields are empty.
- Do not silently overwrite non-empty/user-confirmed profile fields.
- If CV extracted name differs from existing profile name, keep profile name and add warning.
- Profile completeness must recalculate after parse.
- CV parsing failure must not break upload page.

Tests:

- Service test with synthetic raw CV text.
- PDF fixture test using real text-based PDF generated in tests or fixtures.
- Profile prefill test where profile fields are empty.
- Conflict test where profile full_name is non-empty and differs from extracted CV name.
- URL normalization tests.

## TTA-14A-002 — Stabilize recommendations end-to-end

Repair stored recommendations so usable profile + active jobs produces visible recommendations.

Rules:

- Dashboard reads stored recommendations.
- Heavy recommendation generation should be service/task-driven, not synchronous in template.
- Incomplete profile must show clear blocked state, not infinite refreshing.
- Active jobs count zero must show clear blocked state.
- Failed recommendation run must show clear recoverable state.
- Success run with zero recommendations must be explainable in status, not hidden as infinite pending.

Tests:

- Usable profile + active jobs creates stored `JobRecommendation` rows.
- Incomplete profile creates no recommendations and returns blocked state.
- No active jobs returns blocked state.
- Stale recommendations are handled.
- Dashboard/recommendations view does not perform external calls.
- Recommendation service does not use LLM as scoring authority.

## TTA-14A-003 — Stabilize quick match no-browser behavior

Repair the anonymous quick match stale result/stuck processing issue.

Rules:

- Quick match must be recalculated when posted skills change.
- Result must not be reused from previous payload unless payload is identical and explicitly cached safely.
- Button/form processing state must reset after HTMX request and browser back/forward cache restore.
- Quick match remains anonymous.
- Quick match does not call LLM.
- Quick match does not store CV.

Tests:

- POST quick match with one skill set returns result A.
- POST same job with changed skill set returns different result B when score/matched/missing skills should differ.
- Template contains safe HTMX state reset hooks.
- No LLM service is called.
- Rate limiting still exists or is tested if implemented.

## TTA-14A-004 — Safe routes, custom 404/500, and wrong links

Repair route/template behavior without browser testing.

Rules:

- Canonical recommendations URL is `/dashboard/recommendations/`.
- No templates should link to `/recommendations/` unless a deliberate redirect exists.
- With `DEBUG=False`, unknown routes must not show Django URLconf debug output.
- 404 and 500 templates must not expose secrets, settings, traceback, URL patterns, or environment info.

Tests:

- `/dashboard/recommendations/` returns expected auth behavior.
- `/recommendations/` either redirects safely or returns custom safe 404.
- `override_settings(DEBUG=False)` test confirms safe 404 content.
- Template grep/static assertion catches wrong links.

## TTA-14A-005 — Real OpenRouter LLM service validation

Run a controlled real LLM validation from service layer only.

Rules:

- Maximum 2 real OpenRouter calls.
- Do not print key.
- Do not print full raw CV text.
- Use a tiny synthetic CV/match payload.
- Validate JSON/schema shape.
- Save/log request metadata without secrets.
- Cache second identical request if cache exists.
- If LLM disabled or credentials missing, report `BLOCKED_REAL_LLM`, not PASS.

Tests:

- Unit tests use mocks.
- One optional real integration command/test guarded by env variable.
- Failure mode does not break CV parse or match detail.

## TTA-14A-006 — Real France Travail small ingestion validation

Repair or add a management command that performs a small real ingestion smoke when credentials exist.

Rules:

- Command must call service/client layer only.
- Maximum 10 offers.
- Persist RawJobRecord.
- Normalize to NormalizedJob.
- No public search external call.
- No secrets printed.
- If credentials missing or provider unavailable, report `BLOCKED_REAL_FRANCE_TRAVAIL`, not PASS.

Tests:

- Unit tests mock FranceTravailClient.
- Command test verifies counts and no credential logging.
- Public `/jobs/` search test asserts FranceTravailClient is not called.

## TTA-14A-007 — Full regression and final report

Run final acceptance commands.

Required:

- `python manage.py check --settings=config.settings.local`
- `python manage.py makemigrations --check --dry-run --settings=config.settings.local`
- `python manage.py migrate --settings=config.settings.local`
- `python manage.py test --settings=config.settings.local`
- Service-level CV/recommendation/LLM/ingestion smoke commands from `acceptance.md`
- Secret scan commands from `acceptance.md`

Final state:

- If all pass including real LLM and real data: `PASS`.
- If code/tests pass but external credentials/API unavailable: `BLOCKED_EXTERNAL_VALIDATION`.
- If tests fail: `FAIL`.
- If DB unavailable: `BLOCKED_DB`.
