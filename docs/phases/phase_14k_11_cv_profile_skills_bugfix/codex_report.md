# Phase 14K-11 Codex Report - CV Profile Prefill + Skills Restore + Profile Layout Fix

## Final Verdict

Passed. The latest uploaded CV owner path was used for diagnostics and verification. The real parsed CV for `baha.edine.taouai@gmail.com` now prefills career/target fields, creates profile skills, recalculates profile completion above zero, and renders a profile skills section without exposing private CV file URLs or raw CV text.

No commit was made.

## Files Changed For This Phase

- `apps/cvs/services/deterministic_extractor.py`
- `apps/cvs/services/parsing.py`
- `apps/cvs/tests/test_services.py`
- `apps/dashboard/views.py`
- `apps/skills/services/normalizer.py`
- `templates/dashboard/profile.html`
- `static/src/css/app.css`
- `static/css/app.css` (rebuilt by `npm run css:build`)
- `docs/phases/phase_14k_11_cv_profile_skills_bugfix/codex_report.md`

Existing unrelated uncommitted Phase 14K-9/14K-10 files were already present and were not intentionally reset or reverted.

## Latest CV Owner Diagnostic

Diagnostic source: `CVUpload.all_objects.order_by("-uploaded_at").first().user`, not latest user.

Before fix, latest CV:

- Owner: `baha.edine.taouai@gmail.com`
- File: `test_cv_junior_full_stack_aymen_ben_salah.pdf`
- `public_id`: `179e4708-d1d6-4a2d-820f-f389ea21fe80`
- `parse_status`: `parsed`
- `CandidateProfile`: existed
- Filled: name, phone, location, LinkedIn, GitHub, portfolio, French, English
- Broken/missing: `current_level`, `years_experience`, `target_type`, `target_roles`, `target_job_types`, profile skills
- `profile_completion_score`: 47 in local DB at first diagnostic
- `ProfileSkill` count: 0
- `CVParsedData.merged_json`: already contained `current_level=junior`, fluent languages, target roles, and raw skills
- `warnings_json`: `[]`

After reparse with the fixed service:

- `current_level`: `junior`
- `years_experience`: `1.0`
- `target_type`: `internship`
- `target_roles`: `["Junior Full Stack Developer", "Frontend Developer", "Backend Developer", "Web Developer Intern", "Software Developer Intern", "React Developer", "Node.js Developer"]`
- `target_job_types`: `["internship"]`
- `french_level`: `fluent`
- `english_level`: `fluent`
- `profile_completion_score`: 85
- `ProfileSkill` count: 22
- Created skills include: CSS3, Django, Docker, Express.js, Git, GitHub, HTML5, JavaScript, Jest, Linux, MongoDB, Mongoose, Next.js, Node.js, PostgreSQL, Postman, Prisma, React, REST API, SQL, Tailwind CSS, TypeScript
- `warnings_json`: `[]`

## Root Causes

Skills were missing from the DB, not only hidden in the template. `ProfileSkill` rows were not created for the manual QA profile. The normalizer only matched exact aliases, so common CV phrases such as `TypeScript basics`, `REST API design`, `Django basics`, `Docker basics`, `SQL basics`, `Linux/Fedora`, and `Jest basics` were often left as unmatched candidates instead of resolving to existing canonical skills.

The profile page also did not render profile skills at all, so even valid `ProfileSkill` rows would not have been visible there.

Career and target profile fields were partially parsed but not robustly mapped into the profile. The parser did not infer `target_type` / `target_job_types`, did not estimate experience from dated experience spans, and only saved safe prefill values during parsing. Existing non-empty profile values are still preserved.

The profile save button used the sticky save class at the bottom of the form in a way that could look detached near the footer. It is now contained in a normal form footer on desktop, with mobile sticky behavior preserved.

## What Was Fixed

- Added conservative current-level normalization from embedded seniority tokens.
- Added dated experience estimation from month/year ranges such as `September 2024 - August 2025`.
- Added target type inference from roles, with internship taking precedence when intern roles are present.
- Added target job type prefill from inferred target type.
- Kept safe prefill behavior: only empty profile fields are filled.
- Extended skill normalization with conservative candidate variants for common qualifiers and phrases.
- Passed `ProfileSkill` rows into the dashboard profile view while keeping the view thin.
- Added a `Compétences` section to `templates/dashboard/profile.html` showing confirmed/user skills, CV-detected skills, source/confidence badges, and an empty state.
- Kept raw CV text and CV file URLs out of the profile response.
- Moved the save button into a clean form footer.

## Tests Added/Updated

Added `CVServiceTests.test_aymen_cv_prefills_profile_skills_and_profile_page_safely`.

It proves:

- Candidate identity/contact/link fields are filled.
- `current_level` is inferred as `junior`.
- `years_experience` is estimated from dated experience.
- target roles are populated.
- language levels map from professional working proficiency to `fluent`.
- common aliases and qualifier variants create `ProfileSkill` rows.
- `profile_completion_score` is recalculated above 0.
- `/dashboard/profile/` renders `Compétences` and skill badges.
- profile response does not include CV filename, `raw_text`, or raw experience text.

## Commands Run

```bash
source .venv/bin/activate
python manage.py shell --settings=config.settings.local -c '<latest CV owner diagnostic>'
python manage.py test apps.cvs.tests.test_services apps.profiles.tests --settings=config.settings.local --parallel 1
python manage.py shell --settings=config.settings.local -c '<reparse latest CV>'
python manage.py shell --settings=config.settings.local -c '<post-fix latest CV owner diagnostic>'
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test --settings=config.settings.local --parallel 1
npm run css:build
python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
python manage.py shell --settings=config.settings.local -c '<route smoke with HTTP_HOST=localhost>'
grep -R "file.url\|cv.file.url\|upload.file.url\|raw_text\|raw_request_json\|raw_response_text\|raw_response_json" templates apps -n 2>/dev/null || true
grep -R "<int:" apps templates config -n 2>/dev/null || true
git diff -- . ':!.env' ':!.env.*' | grep -iE "sk-or-|Bearer [A-Za-z0-9_.-]{20,}|OPENROUTER_API_KEY=.*[^=]|FRANCE_TRAVAIL_CLIENT_SECRET=.*[^=]|EMAIL_HOST_PASSWORD=.*[^=]" || echo "OK: no obvious secrets in diff"
git diff --check
git diff --cached --check || true
```

## Final Check Results

- `python manage.py check --settings=config.settings.local`: passed
- `python manage.py makemigrations --check --dry-run --settings=config.settings.local`: passed, no changes detected
- Focused CV/profile tests: passed, 18 tests
- Full test suite: passed, 442 tests
- `npm run css:build`: passed; existing Browserslist/caniuse-lite warning shown
- `collectstatic --dry-run`: passed, 2 static files would be copied, 134 unmodified
- `git diff --check`: passed
- `git diff --cached --check || true`: passed

## Route Smoke Results

Authenticated as the latest CV owner with `HTTP_HOST=localhost`:

- `/dashboard/profile/`: 200
- `/dashboard/cv/`: 200
- `/dashboard/`: 200
- `/dashboard/recommendations/`: 200
- `/jobs/`: 200

## Privacy/Security Grep Classification

`file.url` / raw data grep:

- No template hits exposing CV file URLs or raw CV text.
- Expected hits remain in model/service/admin/test code for private storage, raw text extraction/storage, and security tests.
- New profile test explicitly verifies the profile response does not include the uploaded filename, `raw_text`, or raw experience text.

`<int:` grep:

- No hits in `apps`, `templates`, or `config`.

Secrets grep:

- `OK: no obvious secrets in diff`

## Remaining Manual Checks

- Browser-check `/dashboard/profile/` on mobile and desktop to confirm the save footer placement and skill chips look correct in the real viewport.
- If preferred product behavior is to classify mixed junior + internship targets as `any` instead of `internship`, adjust the inference rule. The current rule chooses `internship` when explicit intern roles are present.
- Review unmatched CV skill candidates later for taxonomy additions such as HTMX, VS Code, manual QA, API testing, and CI basics if the product wants these as canonical skills.

## Commit Recommendation

Do not commit until the unrelated existing Phase 14K-9/14K-10 worktree changes are reviewed. When ready, commit this phase separately from those existing changes, for example:

```bash
git add apps/cvs/services/deterministic_extractor.py apps/cvs/services/parsing.py apps/cvs/tests/test_services.py apps/dashboard/views.py apps/skills/services/normalizer.py templates/dashboard/profile.html static/src/css/app.css static/css/app.css docs/phases/phase_14k_11_cv_profile_skills_bugfix/codex_report.md
git commit -m "Fix CV profile prefill and restore profile skills"
```
