# Phase 15I — GLM Review Report

## Reviewer Identity
- Agent: GLM 5.2
- Role: Second-pass reviewer (after Gemini implementation)
- Phase: 15I (Production Readiness and Deployment Plan)
- Date: 2026-06-21

This is a GLM review. It is not a Codex report and does not claim Codex verification.

## Verdict

```text
REPAIRED_PASS
```

Phase 15I is a documentation/policy phase that prepares for deployment without
deploying. All required artifacts exist and are policy-correct. The only working
tree code change is `.env.example`, which already matches the expected
production LLM defaults; no repair was needed to it. No blockers were found.

One pre-existing test-suite condition (8 failing tests in Phase 14 modules,
unrelated to Phase 15I) is documented below as a remaining risk. It does not
block Phase 15I because Phase 15I touches neither the failing modules nor any
application code.

## Files Reviewed

### Phase 15I plan artifacts (docs/phases/phase_15i_production_readiness_deployment_plan/)
- MANIFEST.md
- README_PHASE_15I.md
- tasks.md
- acceptance.md
- manual_readiness_checklist.md
- production_env_policy.md
- phase_15j_deployment_runbook_outline.md
- agent_report.md
- prompt_gemini.md / prompt_glm_review.md

### Deployment docs (docs/deployment/)
- README_PHASE_15I_DEPLOYMENT_DOCS.md
- production_env_policy.md
- static_private_media_policy.md
- rate_limiting_abuse_controls.md
- monitoring_healthchecks.md
- backup_restore_policy.md
- privacy_final_review.md
- legal_wording_final_pass.md
- email_oauth_domain_checklist.md
- phase_15j_deployment_runbook_outline.md
- production_smoke_checklist.md

### Code/config reviewed
- .env.example (only modified tracked file)
- config/settings/base.py
- config/settings/production.py
- docker-compose.yml
- .gitignore
- apps/jobs/views.py and other views (France Travail isolation check)
- apps/jobs/services/ingestion.py, france_travail/client.py (France Travail scope check)

## Mission Verification

| Requirement | Status | Notes |
|---|---|---|
| production `.env.example` uses placeholders only | PASS | All secret fields blank (`OPENROUTER_API_KEY=`, `FRANCE_TRAVAIL_CLIENT_SECRET=`, `EMAIL_HOST_PASSWORD=`, OAuth secrets, DB password). No real keys. |
| LLM automatic token spending disabled by default | PASS | `.env.example`: `LLM_ENABLED=True`, `CV_LLM_EXTRACTION_ENABLED=False`, `JOB_ENRICHMENT_ENABLED=False`, `JOB_ENRICHMENT_MAX_PER_INGESTION_RUN=0`, `JOB_ENRICHMENT_DAILY_LIMIT=0`, `OPENROUTER_CIRCUIT_BREAKER_ENABLED=True`, `OPENROUTER_ENRICHMENT_RATE_LIMIT=1/m`. Matches expected production defaults. LLM code retained. |
| Whitenoise/static/private media policy correct | PASS | `production.py` STORAGES uses Whitenoise only for `staticfiles`; default storage is `FileSystemStorage`. `PRIVATE_MEDIA_ROOT` (base.py:244) is separate from `STATIC_ROOT`/`STATICFILES_DIRS` and never wired into Whitenoise/staticfiles. |
| Caddy/Nginx plan does not expose CV/private media | PASS | `static_private_media_policy.md` mandates private media never served directly by Whitenoise/Caddy/Nginx; access only via authenticated Django views with ownership checks. |
| Rate limiting / abuse-control plan exists | PASS | `rate_limiting_abuse_controls.md` defines per-action limits (login, signup, reset, CV upload, quick match, recommendations, save/unsave, email, admin). Implementation deferred to Phase 15J as documented. |
| Monitoring/health checks plan exists | PASS | `monitoring_healthchecks.md` covers web health endpoint, Gunicorn/Celery/beat systemd status, Celery heartbeat freshness, Redis/Postgres connectivity, disk usage, app metrics. |
| Backup/restore policy exists and requires restore testing | PASS | `backup_restore_policy.md` defines daily pg_dump + private media archive, encryption, retention (7 daily / 4 weekly), logging, and explicit restore steps with a mandatory pre-launch restore test on staging/local. |
| Privacy final checklist exists | PASS | `privacy_final_review.md` covers CV privacy, ownership validation, soft deletion, account/CV deletion flows, unsubscribe, admin access, log hygiene. |
| Legal wording final pass exists | PASS | `legal_wording_final_pass.md` covers no visa/job/relocation guarantee, fit-score role, LLM suggestions, target audience, privacy statement. |
| Email/OAuth/domain checklist exists | PASS | `email_oauth_domain_checklist.md` covers domain placeholders, ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS, Google/GitHub OAuth callbacks, email sender setup, SPF/DKIM/DMARC, unsubscribe URLs, no secrets in docs. |
| Phase 15J runbook outline exists | PASS | `phase_15j_deployment_runbook_outline.md` outlines target architecture and 7-step deployment sequence (system prep, DB, app, Django, systemd, Caddy, verification). |
| Production smoke checklist exists | PASS | `production_smoke_checklist.md` covers public/auth, job browsing, candidate features, operations/background tasks, privacy/security. |
| No real secrets exposed | PASS | Secret scan of working tree diff (excluding `.env`/`.env.*`) returned "OK: no obvious secrets in diff". `.env.example` placeholders only. `.gitignore` protects `.env`/`.env.*` and whitelists `!.env.example`. |
| No forbidden stack introduced | PASS | No React/Next.js/Angular/FastAPI/Flask/MongoDB/SQLAlchemy/Prisma/SPA. Stack remains Django + HTMX + Tailwind + PostgreSQL + Redis + Celery. |
| Public search does not call France Travail | PASS | France Travail client imports confined to `apps/jobs/services/france_travail/client.py`, `apps/jobs/services/ingestion.py`, a management command, and tests. No `views.py` imports the live client. Public search reads local PostgreSQL only. |
| Deployment was planned, not started | PASS | No Caddyfile/nginx.conf/systemd `.service`/Django Dockerfile committed. `docker-compose.yml` is Phase 0 compliant (postgres + redis only). No servers provisioned. |

## Commands Run

```bash
cd ~/Projects/tunitech-abroad
source .venv/bin/activate

git status --short --branch
# -> dev...origin/dev; only .env.example modified; Phase 15I docs untracked

python manage.py check --settings=config.settings.local
# -> System check identified no issues (0 silenced).

python manage.py makemigrations --check --dry-run --settings=config.settings.local
# -> No changes detected

python manage.py test --settings=config.settings.local --parallel 1
# -> Ran 546 tests in 93.056s
# -> FAILED (failures=8)
# Failures are PRE-EXISTING in Phase 14 modules (see Remaining Risks).

npm run css:build
# -> Done in 861ms.

python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
# -> 2 static files copied, 134 unmodified.

python manage.py check --deploy --settings=config.settings.production
# -> System check identified no issues (0 silenced).

python manage.py makemigrations --check --dry-run --settings=config.settings.production
# -> No changes detected

python manage.py collectstatic --dry-run --noinput --settings=config.settings.production
# -> 2 static files copied, 129 unmodified.

pip-audit
# -> No known vulnerabilities found

bandit -r apps config -x "*/tests.py,*/tests/*,*/test_*.py,*/migrations/*,*/fixtures/*"
# -> No issues identified. (1 nosec B104 skipped in config/settings/local.py:16)

npm audit --omit=dev
# -> found 0 vulnerabilities

git diff --check
# -> clean (exit 0)

git diff -- . ':!.env' ':!.env.*' | grep -iE "sk-or-|Bearer [A-Za-z0-9_.-]{20,}|OPENROUTER_API_KEY=.*[^=]|FRANCE_TRAVAIL_CLIENT_SECRET=.*[^=]|EMAIL_HOST_PASSWORD=.*[^=]" || echo "OK: no obvious secrets in diff"
# -> OK: no obvious secrets in diff
```

Additional verification performed:
- Stashed `.env.example` change and re-ran the 8 failing tests on clean HEAD
  (`160fb1b`): same 8 failures. Confirms they are pre-existing and not caused
  by Phase 15I.
- Confirmed `.gitignore` ignores `.env`/`.env.*` and whitelists `!.env.example`.
- Confirmed France Travail live client is not imported by any `views.py`.
- Confirmed no Caddyfile/nginx/systemd/Django-Dockerfile present; only
  Phase 0 `docker-compose.yml` (postgres + redis).

## Repairs Made

None. No small in-scope repair was required:

- `.env.example` already matches the expected production LLM defaults exactly.
- All Phase 15I artifacts are present and policy-correct.
- No real secrets, no private media exposure, no forbidden stack, no live
  France Travail calls from public search, no deployment started.

## Remaining Risks

1. **Pre-existing test failures (NOT introduced by Phase 15I).**
   8 failures exist on clean HEAD `160fb1b` in Phase 14 modules:
   - `apps.jobs.tests.test_14f_automated_it_ingestion` (4 failures)
   - `apps.llm.tests.test_14d_enrichment` (3 failures)
   - `apps.jobs.tests.test_14j_budget_controls` (1 failure)

   Phase 15I modifies only `.env.example` (placeholders) and adds
   documentation. It does not touch these modules. These failures predate
   Phase 15I and should be addressed in a separate Phase 14 follow-up, not
   Phase 15I. They are flagged here for transparency per the AGENTS.md
   "final check results" rule.

2. **Rate limiting is plan-only.** `rate_limiting_abuse_controls.md` documents
   intended limits; actual `django-ratelimit`/Redis service wiring is a
   Phase 15J TODO. Confirm guardrails are applied before public launch.

3. **Stray `agent_report.md` in repo root.** An untracked `agent_report.md`
   exists at the repository root (left over from Phase 15F). It is not part
   of Phase 15I but should be removed or moved to `docs/reports/` before
   commit to keep the tree clean.

4. **Manual pre-launch items remain.** Backup restore test, OAuth callback
   configuration, SPF/DKIM/DMARC, and the production smoke checklist are
   operational tasks deferred to Phase 15J.

## Commit Recommendation

Phase 15I is ready to commit on `dev`. Suggested steps:

1. Remove the stray root-level `agent_report.md` (Phase 15F leftover) or move
   it to `docs/reports/`.
2. Stage the Phase 15I deliverables:
   - `.env.example`
   - `docs/deployment/*` (Phase 15I docs)
   - `docs/phases/phase_15i_production_readiness_deployment_plan/`
3. Commit on `dev` with a message such as:
   `Complete Phase 15I production readiness and deployment plan`.
4. Do NOT merge to `main` until the pre-existing Phase 14 test failures are
   triaged (recommended separate follow-up), per the AGENTS.md git workflow
   where `dev` = active work and `main` = stable.

No blockers for Phase 15I itself.
