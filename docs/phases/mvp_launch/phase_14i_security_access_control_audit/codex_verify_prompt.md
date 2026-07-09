# Phase 14I Codex Verification Prompt

Run this from Warp using:

```bash
codex-tunitech
```

Do not use plain `codex` if `codex-tunitech` is the configured wrapper for rootless Podman/DOCKER_HOST.

Read first:

```text
AGENTS.md
docs/phases/phase_14i_security_access_control_audit/README.md
docs/phases/phase_14i_security_access_control_audit/tasks.md
docs/phases/phase_14i_security_access_control_audit/acceptance.md
docs/phases/phase_14i_security_access_control_audit/preflight.md
docs/phases/phase_14i_security_access_control_audit/regression_security_checks.md
docs/phases/phase_14i_security_access_control_audit/manual_browser_security_signoff.md
```

Verify Gemini's Phase 14I implementation only.

Hard boundary:

```text
Do not deploy.
Do not commit.
Do not start Phase 14J.
Do not redesign UI.
Do not add product features.
Do not change stack.
```

You must verify:

```text
docs/audits/security_access_matrix.md exists and is specific
docs/audits/security_findings_14i.md exists and is specific
private route tests exist
IDOR tests with two users exist
CV privacy tests exist
admin boundary tests exist
HTMX ownership/mutation tests exist where applicable
public_id/integer route audit exists
external-call isolation greps are clean or explained
secret greps are clean or explained
all checks pass against real local PostgreSQL/Redis setup
```

Run preflight and checks:

```bash
source .venv/bin/activate

python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test --settings=config.settings.local --parallel 1
git diff --check

grep -R "cdn.tailwindcss.com" templates config static -n || true
grep -R "React\|Next.js\|next/\|createRoot\|vue\|angular\|Vite" package.json templates static apps -n 2>/dev/null || true
grep -R "FranceTravailClient\|france_travail" apps/*/views.py templates -n 2>/dev/null || true
grep -R "OpenRouterClient\|OPENROUTER\|run_llm\|llm" apps/*/views.py templates -n 2>/dev/null || true
grep -R "file.url\|cv.file.url\|upload.file.url\|raw_text\|extracted_text" templates apps -n 2>/dev/null || true
grep -R "<int:" apps templates config -n 2>/dev/null || true
git diff -- . ':!.env' | grep -iE "OPENROUTER_API_KEY|FRANCE_TRAVAIL_CLIENT_SECRET|client_secret|access_token|password|secret" || echo "OK: no obvious secrets in diff"
```

You may fix defects only if they are inside Phase 14I security/access scope. If you fix anything, rerun all checks.

Report format:

```text
VERIFICATION_SCOPE:
FILES_REVIEWED:
AUTOMATED_CHECKS:
SECURITY_GREP_RESULTS:
TEST_COVERAGE_ASSESSMENT:
SECURITY_FINDINGS:
FIXES_APPLIED_BY_CODEX:
REMAINING_RISKS:
HUMAN_BROWSER_ADMIN_SIGNOFF_REQUIRED:
FINAL_VERDICT:
```

Verdict rules:

```text
FINAL_VERDICT: FAIL
```

Use FAIL if any automated check fails, tests are missing, audit docs are placeholder, or any serious security issue remains.

```text
FINAL_VERDICT: BLOCKED_HUMAN_SECURITY_SIGNOFF
```

Use this only if automated verification passes and the only blocker is Baha's manual Chrome/admin signoff.

Do not write PASS unless Baha has already completed and documented manual Chrome/admin security signoff.
