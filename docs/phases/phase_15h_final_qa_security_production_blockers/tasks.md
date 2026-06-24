# Phase 15H Tasks — Final QA, Security, and Production Settings Blocker Fixes

## Task 0 — Preflight and cleanup

Run:

```bash
cd ~/Projects/tunitech-abroad
source .venv/bin/activate

git status --short --branch
rm -f 'Issue:' ettings.local tailwindcss 'tunitech-abroad@1.0.0'

git status --short --branch
```

Do not delete:

```text
agent_report.md
docs/reports/
var/
```

But do not commit them.

## Task 1 — Keep dependency/security fixes permanent

Ensure:

```text
requirements/base.txt: python-dotenv==1.2.2
requirements/production.txt includes whitenoise and gunicorn
```

Do not downgrade `python-dotenv`.

Run:

```bash
python -m pip install -r requirements/base.txt
python -m pip install -r requirements/production.txt
pip-audit
```

Expected:

```text
No known vulnerabilities found
```

## Task 2 — Production static files must pass

The repo currently uses Whitenoise in production settings. Keep it unless you intentionally refactor production static settings.

Required:

```bash
python manage.py collectstatic --dry-run --noinput --settings=config.settings.production
```

must pass.

If keeping Whitenoise:

- `whitenoise==6.8.2` remains in `requirements/production.txt`.
- `whitenoise.middleware.WhiteNoiseMiddleware` remains in production middleware.
- `CompressedManifestStaticFilesStorage` remains valid.

If removing Whitenoise, you must update settings and requirements consistently. Do not leave half-configured static storage.

## Task 3 — Saved jobs must not leak internal classification/debug text

Problem seen in browser:

```text
Classified as non-IT or explicitly excluded
```

This must never display on user-facing pages.

Audit:

```bash
grep -R "Classified as non-IT\|explicitly excluded\|excluded_non_it\|low relevance\|low confidence\|provider_blocked\|reserved\|unclassified" \
  templates apps -n 2>/dev/null
```

Required behavior:

- Public/search/recommendations/saved/match/dashboard pages must not display internal machine/debug strings.
- Admin pages may display internal diagnostic statuses.
- Saved jobs page should either:
  - hide excluded/non-public/unpublished saved jobs from the main list, or
  - show a generic French unavailable state with remove button.

Allowed user-facing labels:

```text
Offre indisponible
Offre expirée
Offre ancienne
Non publiée
```

Forbidden user-facing labels:

```text
Classified as non-IT or explicitly excluded
excluded_non_it
low_confidence
low_relevance
provider_blocked
validation_error
reserved
unclassified
```

Recommended architecture:

- Add/extend a saved-job presentation helper/service.
- View calls service.
- Template renders safe display fields only.
- Do not put job eligibility logic directly in template.

Tests:

- Saved job pointing to excluded/non-public/removed job does not render internal reason.
- Saved job pointing to unavailable job still allows unsave/remove.
- User A cannot see User B saved jobs.
- Active public saved job still displays normally.

## Task 4 — Fix `/jobs` relevance / `Plus pertinentes` sort

Problem: Browser testing showed `Plus pertinentes` does not work reliably.

Expected behavior:

- `q=python&sort=relevance` returns Python-relevant jobs before unrelated jobs.
- `q=django&sort=relevance` returns Django-relevant jobs before unrelated jobs.
- If no query exists, `sort=relevance` should not pretend relevance exists. It should fall back to newest or stable default.
- Public search must read local PostgreSQL only.
- No France Travail API call in public job search.

Audit:

```bash
grep -R "sort.*relevance\|relevance\|pertinent\|SearchRank\|search_vector\|order_by" \
  apps/jobs templates/jobs -n 2>/dev/null
```

Implementation guidance:

- Keep ranking in `JobSearchService`, not templates.
- For keyword searches, use PostgreSQL full-text rank and/or deterministic weighted fallback.
- If search rank is weak because `search_vector` is stale or null, repair search vector population/update.
- Make the UI label clear: `Plus pertinentes` for keyword relevance, separate from authenticated `Meilleure compatibilité` if that exists.

Tests:

- Relevance sort orders matching jobs first.
- Relevance without query falls back to newest/stable default.
- Public search does not call `FranceTravailClient`.
- Sort parameter is preserved through filter form/select.

## Task 5 — Repair Operations Dashboard metrics

Problem: Operations dashboard has confusing/inconsistent fields, e.g. cost today non-zero while LLM calls today says zero, large `other/unclassified`, and mixed enrichment/usage metrics.

Required behavior:

- Metrics must have clear definitions.
- Do not mix `LLMUsageLog` and `JobEnrichment` counters under one vague label.
- If cost comes from enrichment rows, label it as enrichment cost.
- If call count comes from usage logs, label it as usage-log calls.
- If both are shown, show both separately.
- Reduce `Other/unclassified` by mapping known skip/status reasons into visible categories.
- Admin-only internal statuses are allowed on admin operations page.
- User-facing pages must not display these internal statuses.

Suggested grouping:

```text
LLM Usage Logs Today
- calls
- failures
- estimated cost

Job Enrichment Records
- success
- pending
- processing
- failed
- skipped
- validation_error
- permanent_blocked
- retry_eligible

Active Jobs Without Successful Enrichment
- eligible
- skipped low relevance
- skipped low confidence
- non-FR/excluded country
- existing pending/reservation
- no enrichment required / not selected
- other
```

Tests:

- Dashboard view returns 200 for staff.
- Non-staff cannot access.
- LLM cost/calls use consistent source or labels make source explicit.
- Known status reasons do not fall into `other/unclassified` when mapping exists.

## Task 6 — Fix Bandit production findings

Run after changes:

```bash
bandit -r apps config -x "*/tests.py,*/tests/*,*/test_*.py,*/migrations/*,*/fixtures/*"
```

### 6.1 Silent `except: pass`

Fix in:

```text
apps/cvs/services/deletion.py
apps/cvs/services/upload.py
apps/cvs/tasks.py
apps/privacy/services/account_deletion.py
apps/recommendations/services/saved_jobs.py
```

Replace silent pass with safe logging.

Rules:

- Do not log full CV text.
- Do not log full provider payloads.
- Do not log secrets/tokens.
- Keep non-critical side-effect failures non-fatal where intentionally non-fatal.

Example pattern:

```python
logger.warning("Failed to remove previous CV file during CV replacement", exc_info=True)
```

### 6.2 Replace MD5 in LLM services

Fix:

```text
apps/llm/services/job_enrichment.py
apps/llm/services/request_runner.py
```

Replace MD5 with SHA-256:

```python
hashlib.sha256(value.encode("utf-8")).hexdigest()
```

Expected side effect: old cached/enrichment hashes may no longer match once and may be recomputed. That is acceptable.

### 6.3 Replace `urllib.request.urlopen` in OpenRouter client

Prefer `requests.post()` using a fixed settings-defined OpenRouter URL.

Rules:

- Do not accept arbitrary user-provided URLs.
- Timeout must remain.
- Error handling must preserve current behavior.
- Do not log API key or full prompt/CV text.
- Tests should cover success, HTTP error, missing API key, disabled LLM.

### 6.4 FranceTravailClient false positive cleanup

Change constructor defaults from empty strings to `None` if straightforward:

```python
def __init__(self, client_id: str | None = None, client_secret: str | None = None):
```

Behavior must remain the same.

### 6.5 Local settings `0.0.0.0`

This is local-only. Either:

- remove `0.0.0.0` from local `ALLOWED_HOSTS`, or
- add a targeted `# nosec B104` with comment explaining local development only.

Do not weaken production settings.

## Task 7 — Verification commands

Run:

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

Expected:

```text
Full tests OK
Local collectstatic OK
Production collectstatic OK
pip-audit clean
npm audit clean
Bandit: no unresolved high/medium production findings
No obvious secrets in diff
```

## Task 8 — Manual browser QA after code fixes

Manually verify:

- `/dashboard/saved-jobs/` has no internal classification/debug text.
- Removed/unavailable saved jobs are hidden or generic `Offre indisponible` with remove button.
- `/jobs/?q=django&sort=relevance` orders Django jobs first.
- `/jobs/?q=python&sort=relevance` orders Python jobs first.
- `/admin/operations/` metrics are understandable and internally consistent.
- No public page displays `excluded_non_it`, `provider_blocked`, `validation_error`, `reserved`, `unclassified`, etc.

## Task 9 — Reports

Create:

```text
docs/phases/phase_15h_final_qa_security_production_blockers/agent_report.md
```

Codex verifier creates:

```text
docs/phases/phase_15h_final_qa_security_production_blockers/codex_report.md
```
