# Gemini Prompt — Phase 15H Final QA, Security, and Production Settings Blocker Fixes

You are working on TuniTech Abroad. Follow the existing Django monolith architecture strictly.

## Mission

Implement Phase 15H only:

```text
Final QA, Security, and Production Settings Blocker Fixes
```

Fix the remaining deployment blockers found by manual QA and security scans.

## Read first

- `docs/phases/phase_15h_final_qa_security_production_blockers/README_PHASE_15H.md`
- `docs/phases/phase_15h_final_qa_security_production_blockers/tasks.md`
- `docs/phases/phase_15h_final_qa_security_production_blockers/acceptance.md`

Also inspect existing code before editing.

## Context from latest checks

Known current state:

- `requirements/base.txt` has been updated locally to `python-dotenv==1.2.2`; keep it.
- `requirements/production.txt` includes Whitenoise and Gunicorn.
- Production `collectstatic` passes after installing production requirements.
- `pip-audit` passes.
- Bandit still reports:
  - silent `except: pass` in CV/privacy/saved-job code
  - MD5 in `apps/llm/services/job_enrichment.py`
  - MD5 in `apps/llm/services/request_runner.py`
  - `urllib.request.urlopen` in `apps/llm/services/client.py`
  - local-only `0.0.0.0` warning
  - FranceTravailClient empty-secret default style
- Manual browser QA found saved jobs leaking `Classified as non-IT or explicitly excluded`.
- Browser QA found `Plus pertinentes` sort is not trustworthy.
- Operations dashboard metric labels/counts are confusing.

## Hard rules

- No React, Next.js, Angular, FastAPI, MongoDB, SQLAlchemy, SPA architecture.
- No OpenRouter/LLM call from views/templates/models/admin display.
- No France Travail live API call from public job search.
- Views stay thin.
- Business logic in services/presentation helpers.
- No real secrets in files, logs, reports, prompts, tests.
- Do not log raw CV text or full LLM prompt/payload.
- Do not expose internal job classification/debug statuses on user-facing pages.

## Required fixes

1. Saved jobs internal text leak:
   - User-facing saved jobs page must not display internal classifications/debug reasons.
   - Use safe French labels or hide unavailable items.
   - Keep remove/unsave available.
   - Add tests.

2. Relevance sort:
   - Fix `/jobs/?q=<term>&sort=relevance` to sort relevant local PostgreSQL jobs first.
   - Relevance without query falls back safely.
   - Public search must not call France Travail.
   - Add tests.

3. Operations dashboard metrics:
   - Clarify source of LLM usage vs job enrichment cost/counts.
   - Reduce ambiguous `Other/unclassified` where known status reasons exist.
   - Add tests.

4. Security/code quality:
   - Keep `python-dotenv==1.2.2`.
   - Keep production static config consistent with Whitenoise and production requirements.
   - Replace MD5 with SHA-256 in production LLM services.
   - Replace `urllib.request.urlopen` with `requests.post()` or equivalent fixed-url safe implementation.
   - Replace silent `except: pass` with safe logging.
   - Clean FranceTravailClient constructor default style if simple.
   - Handle local `0.0.0.0` Bandit false positive without weakening production.

## Verification commands

Run all from tasks.md. Minimum:

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test --settings=config.settings.local --parallel 1
npm run css:build
python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
python manage.py check --deploy --settings=config.settings.production
python manage.py makemigrations --check --dry-run --settings=config.settings.production
python manage.py collectstatic --dry-run --noinput --settings=config.settings.production
pip-audit
bandit -r apps config -x "*/tests.py,*/tests/*,*/test_*.py,*/migrations/*,*/fixtures/*"
npm audit --omit=dev
git diff --check
```

## Report

Create:

```text
docs/phases/phase_15h_final_qa_security_production_blockers/agent_report.md
```

Use the template.
