# TuniAtlas Gate A.2 Review Agent Prompt

## Role

You are reviewing an implementation of **Gate A.2 — Production trust stabilization patch** for TuniAtlas.

Do not implement new features unless the user explicitly asks you to fix review findings. First produce a strict review.

## Active gate plan

```text
Gate A — Baseline current damage + production trust defects
Gate B — Skill extraction v2
Gate C — CV parser v2
Gate D — Admin anomaly review
Gate E — Rematerialize and compare
Deferred — EN/FR cleanup
```

The implementation must stay within **Gate A.2**.

## Review starting checks

Run and inspect:

```bash
git status --short --branch
git log --oneline --decorate -8
git diff --stat
git diff -- . ':!.env' ':!*.sqlite3'
```

Do not print secrets. If `.env` appears in diff, stop and flag critical issue.

## Review scope

The implementation is allowed to fix only:

```text
1. stale match detail after profile skill changes
2. recommendation refresh/list inconsistency
3. manual signup CSRF 403
4. onboarding redirects
5. password stepper status
6. password mismatch stale message
7. password changed security email
8. contact/about false required errors
9. CV max size 8 MB
10. /jobs total + filtered count
11. /jobs scroll-to-top button
```

## Hard blockers

Flag as blocker if any of these occurred:

```text
- New React/Next/Angular/FastAPI/MongoDB/SQLAlchemy/SPA usage
- Live France Travail calls during normal search
- LLM call from Django view
- Matching score decided by LLM
- Business logic moved into templates
- Model method calls external service/API
- CV file exposed publicly
- Internal integer IDs exposed in public URLs where public_id is required
- CVUpload.objects changed to include soft-deleted CVs
- Secrets printed, committed, or documented
- .env committed or modified
- Broad skill taxonomy/CV parser overhaul done inside Gate A.2
- EN/FR cleanup started instead of minimal fixes
- Migrations created without clear necessity
```

## Architecture checks

Verify:

```text
- Views stay thin.
- Matching/recommendation fixes are in services.
- Account/onboarding logic is centralized enough, not scattered template hacks.
- Contact form fix keeps server-side validation.
- Password changed email uses Django/allauth mail path safely.
- CV size limit is consistent in config, form, UI text, and tests.
- Jobs count uses search/query service context, not duplicate ad-hoc template queries.
- Scroll-to-top is minimal and does not trigger CSS rebuild unless necessary.
```

## Behavioral checks

Confirm via tests or code inspection:

```text
- Adding/removing profile skill invalidates or refreshes old match detail behavior.
- Recommendation score and match detail score agree for same user/job/current profile state.
- Refresh recommendations with unchanged state has stable ordering.
- Manual signup does not 403 after successful POST.
- Manual signup goes to CV step.
- OAuth/no-password user goes to password step.
- Manual user with usable password is not forced to password step.
- Password stepper reflects CV/profile state.
- Password mismatch message clears after correction.
- Password changed email is sent.
- Contact valid submit does not display false required errors.
- 7–8 MB CV accepted; >8 MB rejected.
- /jobs displays total and filtered count.
- Scroll-to-top appears near bottom and works.
```

## Tests to run

Run:

```bash
python manage.py check --settings=config.settings.local
python manage.py test apps.accounts apps.core apps.cvs apps.jobs apps.matching apps.recommendations --settings=config.settings.local
```

If tests fail, classify each failure:

```text
- new real failure
- pre-existing known temporary i18n assertion failure
- unrelated environment failure
```

Known context:

```text
apps.recommendations passes.
Full apps.matching apps.recommendations previously had 2 known temporary matching assertion failures due to UI/i18n assertion text.
Do not accept new backend failures as “known”.
```

## Required review output

Return:

```text
PASS or FAIL

1. Summary
2. Gate scope compliance
3. Architecture compliance
4. Security/privacy findings
5. Test results
6. Blockers
7. Non-blocking issues
8. Exact files requiring changes if FAIL
9. Whether the work is safe to commit after fixes
```

Do not commit. Do not push.
