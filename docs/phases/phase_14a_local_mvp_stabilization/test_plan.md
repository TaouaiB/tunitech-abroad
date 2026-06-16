# Test Plan

No browser testing. All checks must be automated through Django tests, service tests, template rendering tests, or management command tests.

## Test groups to add or repair

### CV parsing tests

Create tests under appropriate existing app test structure, for example:

```text
apps/cvs/tests/test_deterministic_extractor.py
apps/cvs/tests/test_parsing_service.py
apps/cvs/tests/test_profile_prefill.py
```

Required assertions:

- Extracts `aymen.bensalah.test@example.com`.
- Extracts `+216 55 123 456`.
- Extracts `Aymen Ben Salah`.
- Extracts `Tunis, Tunisia` or normalized equivalent.
- Extracts and normalizes `https://linkedin.com/in/aymen-bensalah-test`.
- Extracts and normalizes `https://github.com/aymen-bensalah-test`.
- Extracts and normalizes `https://aymen-dev.example.com`.
- Extracts skills including JavaScript, React, Next.js, Node.js, Express.js, MongoDB, PostgreSQL, Docker, Git, GitHub, Tailwind CSS.
- Does not treat section titles and random phrases as confirmed skills.
- Profile fields are prefilled when empty.
- Existing profile full_name is not overwritten by different CV name.
- Conflict warning is stored when extracted CV identity conflicts with non-empty profile identity.

### Recommendations tests

Create or repair tests under:

```text
apps/recommendations/tests/
apps/dashboard/tests/
```

Required assertions:

- Usable profile + active CV or enough manual profile + active jobs -> creates `JobRecommendation` rows.
- Incomplete profile -> no recommendations and clear blocked state.
- No active jobs -> clear blocked state.
- Dashboard recommendations view does not compute heavy recommendations synchronously.
- Service is idempotent.
- Re-running refresh does not duplicate recommendations.
- Recommendation page does not stay in infinite refreshing state after successful zero-result run.

### Quick match tests

Create or repair tests under:

```text
apps/matching/tests.py
apps/matching/tests/test_quick_match.py
```

Required assertions:

- Anonymous POST works.
- Changed skill input changes result where expected.
- Same job + same session + different skills creates separate session/result or updates with fresh payload.
- No LLM call.
- No CV creation.
- Template contains HTMX reset behavior for disabled/processing state.

### Safe error page tests

Create or repair tests under:

```text
apps/core/tests.py
apps/core/tests/test_error_pages.py
```

Required assertions:

- With `DEBUG=False`, `/does-not-exist/` returns custom 404.
- 404 body does not contain `Using the URLconf`, `urlpatterns`, `Traceback`, `.env`, `settings`, or secret names.
- `/recommendations/` does not expose Django debug URL pattern data.
- Broken links to `/recommendations/` are removed or route is redirected safely.

### LLM tests

Unit tests must mock network calls.

Required assertions:

- LLM disabled -> service returns disabled/fallback result, no crash.
- Invalid LLM output -> validation failure stored, no score change.
- Rate limit enforced.
- Cache hit avoids client call if cache model/service exists.
- Usage log written with metadata only, no secrets.
- Match explanation cannot alter `fit_score`.

Real validation is separate and limited; see `real_validation.md`.

### France Travail tests

Unit tests must mock network calls.

Required assertions:

- Small sync command calls service/client layer.
- Raw records are created/updated idempotently.
- Changed payload updates hash.
- Normalization creates/updates NormalizedJob.
- Public job search does not call FranceTravailClient.
- Credentials are not printed in command output.

Real validation is separate and limited; see `real_validation.md`.

## Test execution rule

After each repair:

1. Run the smallest failing test.
2. Fix root cause.
3. Re-run that test.
4. Run related app tests.
5. Run full suite before final report.

Maximum repair loops: 8 full loops. A loop means: run tests -> inspect failure -> fix root cause -> rerun.
