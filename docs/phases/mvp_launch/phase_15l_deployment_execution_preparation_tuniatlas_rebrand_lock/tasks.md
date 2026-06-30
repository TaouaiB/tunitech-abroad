# Phase 15L Tasks

## 1. Preflight

- [ ] Confirm branch is `dev` and synced with `origin/dev`.
- [ ] Confirm working tree is clean before starting.
- [ ] Confirm no `.env` file is read, printed, edited, created, or committed.
- [ ] Confirm no actual deployment or external server action is performed.

## 2. TuniAtlas public rebrand lock

- [ ] Add or place logo assets under a safe static path, for example `static/img/brand/`.
- [ ] Add favicon assets if available; if not available, document a blocking TODO instead of inventing low-quality assets.
- [ ] Replace public-facing `TuniTech Abroad` text with `TuniAtlas` / `TuniAtlas Jobs`.
- [ ] Update browser titles and SEO title/description.
- [ ] Update navbar/header/footer public branding.
- [ ] Update homepage/landing page copy.
- [ ] Update auth/account pages visible to users.
- [ ] Update email templates visible to users.
- [ ] Update admin site branding if currently visible as old public brand.
- [ ] Keep repo/internal code names unchanged.

## 3. Deployment execution decisions

Create or update docs under `docs/deployment/` or this phase folder covering:

- [ ] Hosting provider and server-size decision, with final purchase still manual.
- [ ] Domain plan: `tuniatlas.com` primary, `tuniatlas.tn` later/defensive.
- [ ] DNS plan: apex/root and `www` behavior.
- [ ] Email provider plan for transactional email and optional mailbox.
- [ ] Backup destination plan.
- [ ] Manual production `.env` fill checklist, placeholders only.
- [ ] LLM automatic spending disabled in production.
- [ ] Private media/CV serving and backup rules re-confirmed.
- [ ] Exact Phase 15M deployment order summary.

## 4. Production env and docs alignment

- [ ] Update `.env.example` only if needed, placeholders only.
- [ ] Update Phase 15J deployment docs if they still refer to old public domain/name.
- [ ] Do not put real secrets, real passwords, real API keys, or private emails in docs.
- [ ] Confirm production LLM values remain safe:

```env
LLM_ENABLED=True
CV_LLM_EXTRACTION_ENABLED=False
JOB_ENRICHMENT_ENABLED=False
JOB_ENRICHMENT_MAX_PER_INGESTION_RUN=0
JOB_ENRICHMENT_DAILY_LIMIT=0
OPENROUTER_CIRCUIT_BREAKER_ENABLED=True
OPENROUTER_ENRICHMENT_RATE_LIMIT=1/m
```

## 5. Verification

- [ ] Run local Django checks.
- [ ] Run migration dry-run check.
- [ ] Run full tests.
- [ ] Run CSS build.
- [ ] Run local and production collectstatic dry-runs.
- [ ] Run production deploy check.
- [ ] Run `pip-audit`, `bandit`, `npm audit`.
- [ ] Run secret grep.
- [ ] Run old public name grep and classify allowed/blocked occurrences.
- [ ] Manual browser smoke for public branding.

## 6. Reports

- [ ] Gemini writes `agent_report.md`.
- [ ] Sonnet writes `sonnet_review_report.md`.
- [ ] No `codex_report.md` and no fake GLM report.
