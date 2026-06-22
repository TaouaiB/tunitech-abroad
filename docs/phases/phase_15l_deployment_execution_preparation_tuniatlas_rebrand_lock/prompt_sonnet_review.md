# Sonnet Review Prompt — Phase 15L

You are Sonnet reviewing Phase 15L after Gemini implementation.

You are not Codex, not GLM, and not Opus.
Do not create `codex_report.md` or `glm_review_report.md`.
Create `sonnet_review_report.md` only.

## Phase

Phase 15L — Deployment Execution Preparation + TuniAtlas Public Rebrand Lock

## Review mission

Verify that Gemini performed a safe public rebrand and deployment preparation without overbuilding or breaking deployment safety.

## Critical checks

### Brand

- Public-facing UI uses `TuniAtlas` / `TuniAtlas Jobs`.
- Tagline is `Tech careers abroad for Tunisian talent` where tagline is displayed.
- SEO title is `TuniAtlas — Tech Jobs Abroad for Tunisians` or consistent page-specific variant.
- Old name `TuniTech Abroad` is not visible in public templates, browser title, public emails, navbar, footer, homepage.
- Repo/internal package names were not renamed.

### Scope control

- No big UI/UX design-pack redesign.
- No matching/scoring logic changes.
- No new product features.
- No actual deployment.
- No external server/DNS/domain purchase action.
- `.env` not read, edited, printed, created, or committed.

### Security/deployment safety

- LLM automatic spending remains disabled by production examples.
- CV/private media remains private.
- No Caddy/Nginx public media exposure introduced.
- No France Travail call from public views.
- No OpenRouter call from views/templates/models/admin display.
- No real secrets in tracked files or diff.

### Deployment decisions

- `docs/deployment/phase_15l_deployment_decisions.md` exists and is practical.
- `docs/deployment/phase_15l_final_pre_deploy_checklist.md` exists and is practical.
- Domain plan is `tuniatlas.com` primary, `tuniatlas.tn` later.
- Phase order remains 15M deployment, 15N smoke test, 15O Opus security audit, 15P launch fixes.

## Commands to run

Run without `|| true`, except the final grep command may use `|| true` because old-name matches can be manually classified.

```bash
cd ~/Projects/tunitech-abroad
source .venv/bin/activate

git status --short --branch
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test --settings=config.settings.local --parallel 1
npm run css:build
python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
python manage.py check --deploy --settings=config.settings.production
python manage.py collectstatic --dry-run --noinput --settings=config.settings.production
pip-audit
bandit -r apps config -x "*/tests.py,*/tests/*,*/test_*.py,*/migrations/*,*/fixtures/*"
npm audit --omit=dev
git diff --check
git diff -- . ':!.env' ':!.env.*' | grep -iE "sk-or-|Bearer [A-Za-z0-9_.-]{20,}|OPENROUTER_API_KEY=.*[^=]|FRANCE_TRAVAIL_CLIENT_SECRET=.*[^=]|EMAIL_HOST_PASSWORD=.*[^=]" || echo "OK: no obvious secrets in diff"
grep -R "TuniTech Abroad\|tunitech abroad\|Tunitech Abroad" templates static apps config docs/deployment .env.example -n || true
```

## Allowed repairs

You may make small in-scope repairs only:

- missed public text replacement
- stale doc wording
- wrong report identity
- unsafe `.env.example` placeholder/default
- favicon/logo broken path
- trailing whitespace

Block instead of repairing if the issue requires broad architecture/product changes.

## Report

Create:

```text
docs/phases/phase_15l_deployment_execution_preparation_tuniatlas_rebrand_lock/sonnet_review_report.md
```

Verdict:

```text
PASS / REPAIRED_PASS / BLOCKED / FAIL
```

Include:

- files reviewed
- commands run and results
- repairs made, if any
- old-name grep classification
- remaining risks
- commit recommendation
