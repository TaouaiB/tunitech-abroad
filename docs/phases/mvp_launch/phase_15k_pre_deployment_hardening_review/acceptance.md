# Phase 15K Acceptance Criteria

- [x] All 546 unit tests pass.
- [x] No `makemigrations` dry-run checks indicate missing migrations.
- [x] Production deploy checks via `manage.py check --deploy --settings=config.settings.production` identify no critical issues.
- [x] `pip-audit`, `bandit`, and `npm audit` return successfully with no unacknowledged critical vulnerabilities.
- [x] `git diff` shows no tracked `.env` modifications or exposed API keys.
- [x] Static and private media policies confirm no direct public access to private resumes.
- [x] `LLM_ENABLED` spending and token controls are properly constrained with sensible and safe defaults (disabled enrichment by default).
- [x] `FRANCE_TRAVAIL_CLIENT_SECRET`, `OPENROUTER_API_KEY` are safely referenced from environment variables and never hardcoded in `.py` sources.
