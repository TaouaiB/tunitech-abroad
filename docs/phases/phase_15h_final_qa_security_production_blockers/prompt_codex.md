# Codex Verification Prompt — Phase 15H Final QA, Security, and Production Settings Blocker Fixes

You are Codex verifying Phase 15H for TuniTech Abroad.

Start from Warp using:

```bash
codex-tunitech
```

Do not use plain `codex` if the project relies on the rootless Podman socket.

## Mission

Verify and repair Phase 15H if needed.

This is a blocker-fix phase, not deployment.

## Read first

- `AGENTS.md`
- `docs/phases/phase_15h_final_qa_security_production_blockers/tasks.md`
- `docs/phases/phase_15h_final_qa_security_production_blockers/acceptance.md`
- Gemini agent report, if present.

## Verify

Manual QA fixes:

- Saved jobs page does not expose internal classification/debug text.
- Unavailable/excluded/non-public saved jobs are hidden or generically labelled in French.
- `Plus pertinentes` sort works with keyword searches.
- Relevance without keyword falls back safely.
- Operations dashboard metrics are clearly defined and internally consistent.

Security/production fixes:

- `python-dotenv==1.2.2` remains in requirements.
- Production collectstatic passes.
- `pip-audit` passes.
- Bandit has no unresolved high/medium production findings.
- Silent `except: pass` fixed or justified safely.
- MD5 replaced with SHA-256 in LLM services.
- OpenRouter client no longer uses unsafe arbitrary URL opening.
- No secrets exposed.

Architecture:

- No forbidden stack.
- Views thin.
- Logic in services/presentation helpers.
- No OpenRouter in views/templates/models/admin display.
- No France Travail live calls from public search.
- No CV privacy regression.
- No public integer ID regression.

## You may repair

You may fix in-scope issues yourself. Do not block for minor fixable issues.

Block only for:

- forbidden stack
- secret exposure
- CV privacy leak
- public integer ID regression
- provider calls from views/templates
- France Travail live calls from public search
- tests/security scans still failing after repair
- phase boundary violation

## Commands

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
python manage.py makemigrations --check --dry-run --settings=config.settings.production
python manage.py collectstatic --dry-run --noinput --settings=config.settings.production

pip-audit
bandit -r apps config -x "*/tests.py,*/tests/*,*/test_*.py,*/migrations/*,*/fixtures/*"
npm audit --omit=dev

git diff --check
git diff -- . ':!.env' ':!.env.*' | grep -iE "sk-or-|Bearer [A-Za-z0-9_.-]{20,}|OPENROUTER_API_KEY=.*[^=]|FRANCE_TRAVAIL_CLIENT_SECRET=.*[^=]|EMAIL_HOST_PASSWORD=.*[^=]" || echo "OK: no obvious secrets in diff"
```

User-facing internal-text grep:

```bash
grep -R "Classified as non-IT\|explicitly excluded\|excluded_non_it\|low relevance\|low confidence\|provider_blocked\|reserved\|unclassified" templates apps -n 2>/dev/null || true
```

If matches are admin-only or tests/docs, classify them. If matches are public templates/views, repair.

## Report

Create:

```text
docs/phases/phase_15h_final_qa_security_production_blockers/codex_report.md
```

Verdict:

```text
PASS / REPAIRED_PASS / BLOCKED / FAIL
```
