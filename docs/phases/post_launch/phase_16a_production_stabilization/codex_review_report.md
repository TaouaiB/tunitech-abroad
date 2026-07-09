# Codex Verification Report — Phase 16A — Production Stabilization

## 1. Summary

```text
Status: PASS_WITH_DEPLOYMENT_FOLLOWUP
Branch: dev
Commit/hash if available: not committed
```

Phase 16A repo verification passed after intent-preserving repairs. Required local checks and full tests pass. Production smoke shows the deployed app has HTTPS login behavior, but deployed `/robots.txt` and `/sitemap.xml` still return 404, so the repo changes need deployment before production acceptance is complete.

## 2. Tickets completed

```text
- TTA-16A-001: PASS. Production settings include SECURE_PROXY_SSL_HEADER, ACCOUNT_DEFAULT_HTTP_PROTOCOL, SECURE_SSL_REDIRECT, SESSION_COOKIE_SECURE, and CSRF_COOKIE_SECURE.
- TTA-16A-002: REPAIRED_PASS. Google verified-email linking moved through adapter/service logic; unsafe verified/unverified collisions stop with a clear message path.
- TTA-16A-003: REPAIRED_PASS locally. Routes/templates/tests added for robots.txt and sitemap.xml; production smoke still 404 until deploy.
- TTA-16A-004: PASS. External job descriptions no longer use `safe`; line breaks are preserved through escaped rendering.
- TTA-16A-005: REPAIRED_PASS. PDF upload validates extension, content type, `%PDF-` header, size, and pointer reset.
- TTA-16A-006: PASS. Match formula is exactly technical 45%, experience 20%, role/title 15%, language 10%, location 10%.
- TTA-16A-007: REPAIRED_PASS. LLM disabled mode returns disabled/skipped result with zero tokens and no fake validated extraction.
- TTA-16A-008: REPAIRED_PASS. Homepage uses real latest active jobs through a service and shows an honest empty state.
```

## 3. Files changed

```text
apps/accounts/adapters.py
apps/accounts/services/oauth_linking.py
apps/accounts/tests.py
apps/core/services/homepage.py
apps/core/test_home_cta.py
apps/core/views.py
apps/cvs/services/upload.py
apps/cvs/tests/test_services.py
apps/jobs/tests/test_views.py
apps/llm/services/client.py
apps/llm/services/job_enrichment.py
apps/llm/tests/test_14d_enrichment.py
apps/llm/tests/test_client.py
apps/matching/services/scoring.py
apps/matching/tests.py
config/settings/production.py
config/urls.py
templates/core/home.html
templates/jobs/job_detail.html
templates/robots.txt
templates/sitemap.xml
docs/phases/post_launch/phase_16a_production_stabilization/codex_review_report.md
```

Other pre-existing worktree changes were observed and not modified by Codex, including broad docs path deletions/additions and `apps/skills/services/phase_15d_decisions.py`.

## 4. Migrations

```text
none
```

## 5. Commands run

```bash
python manage.py test apps.accounts apps.core apps.jobs.tests.test_views apps.cvs.tests.test_services apps.llm.tests.test_client apps.llm.tests.test_14d_enrichment apps.matching.tests --settings=config.settings.local
# PASS: Ran 157 tests OK

python manage.py check --settings=config.settings.local
# PASS: System check identified no issues (0 silenced).

python manage.py makemigrations --check --dry-run --settings=config.settings.local
# PASS: No changes detected

python manage.py test --settings=config.settings.local
# PASS: Ran 558 tests OK

git diff --check
# PASS: no output

curl -I https://www.tuniatlas.com/accounts/login/
# 301 Location: https://tuniatlas.com/accounts/login/

curl -I https://tuniatlas.com/accounts/login/
# 200; Set-Cookie includes Secure; HSTS present

curl -I https://tuniatlas.com/robots.txt
# 404 on currently deployed production

curl -I https://tuniatlas.com/sitemap.xml
# 404 on currently deployed production
```

## 6. Tests

```text
passed: 558 full-suite tests
failed: 0 local tests
skipped: none observed
```

Added/updated coverage for verified OAuth linking, unsafe OAuth collisions, robots/sitemap routes, XSS-safe job description rendering, PDF magic-byte/content-type validation, exact match formula, disabled LLM behavior, and homepage real latest jobs.

## 7. Manual/browser checks

```text
Local browser checks: not run; covered by Django route/template tests.
Production HTTP smoke: run with curl -I.
Production result: login HTTPS checks pass; robots.txt and sitemap.xml are still 404 until deployment.
```

## 8. Architecture compliance

```text
views thin: yes
services own logic: yes
Celery tasks thin: yes; not changed
public_id preserved: yes
CV privacy preserved: yes
no secrets logged: yes
phase boundary respected: yes
```

## 9. Intent-preserving fixes

```text
- Moved OAuth verified-email collision decision into `OAuthAccountLinkingService` and kept adapter as allauth integration layer.
- Replaced fake/mock disabled LLM response with explicit disabled response and skipped enrichment result.
- Replaced homepage query-in-view with `HomepageService.latest_public_jobs()`.
- Replaced external job description `safe` rendering with escaped line-break rendering.
- Added direct `%PDF-` header validation while preserving content-type and size checks.
- Updated Phase 15G regression expectation to match Phase 16A formula correction.
```

## 10. Intent-changing fixes or disagreements

```text
none
```

## 11. Risks / follow-ups

```text
- Production `/robots.txt` and `/sitemap.xml` currently return 404 because repo changes are not deployed yet.
- Worktree includes broad unrelated docs deletions/additions and one unrelated Phase 15D service path change; those should be reviewed separately before commit.
- OAuth unsafe collision redirects to login with a Django message; final UX copy can be browser-reviewed after deployment.
```

## 12. Ready for senior review

```text
yes, with deployment follow-up required for production robots.txt and sitemap.xml smoke.
```
