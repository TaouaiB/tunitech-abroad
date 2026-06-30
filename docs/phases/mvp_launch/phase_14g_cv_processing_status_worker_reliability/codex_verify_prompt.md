# Codex Verification Prompt — Phase 14G

Read and execute this exactly.

You are Codex verifying Phase 14G only: CV Processing Status UX + Worker Reliability.

Do not commit.
Do not deploy.
Do not start Phase 14H.
Fix Phase 14G issues only if found.

## Required preflight

Use Warp command:

```bash
codex-tunitech
```

This ensures rootless Podman/Docker socket environment is correct.

Verify worktree:

```bash
cd ~/Projects/tunitech-abroad
source .venv/bin/activate
git status --short --branch
```

## Verify implementation

Check these areas:

- CV upload view remains thin.
- CV status endpoint uses `public_id` UUID.
- User cannot access another user's CV status.
- CV file URLs are never exposed in templates.
- Raw extracted CV text is not exposed in templates.
- `CVUpload.objects` is used for user-facing access, not `all_objects`.
- `CVUpload.all_objects` appears only in admin/privacy/deletion/internal code.
- Celery `parse_cv` task calls a service; parsing logic is not moved into views.
- UI has clear queued/processing/completed/failed states.
- HTMX polling stops on terminal state.
- Local dev worker guidance exists.
- No OpenRouter calls from Django views.
- No matching score logic changes.
- Phase 14F ingestion/enrichment behavior remains intact.

## Required commands

Run:

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test apps.cvs apps.profiles apps.matching apps.recommendations --settings=config.settings.local
python manage.py test --settings=config.settings.local
git diff --check
```

Run security greps:

```bash
grep -R "file.url\|cv.file.url\|upload.file.url\|raw_text\|extracted_text" templates apps -n 2>/dev/null || true
grep -R "OpenRouter\|OPENROUTER\|OpenRouterClient\|run_llm\|llm" apps/*/views.py apps/*/views templates -n 2>/dev/null || true
grep -R "CVUpload.objects.get(id=\|cv_id\|<int:" apps templates -n 2>/dev/null || true
grep -R "CVUpload.all_objects" apps templates -n 2>/dev/null || true
git diff -- . ':!.env' | grep -iE "OPENROUTER_API_KEY|FRANCE_TRAVAIL_CLIENT_SECRET|client_secret|access_token|password|secret" || echo "OK: no obvious secrets in diff"
```

## Manual/local proof if possible

With Redis and Celery available:

```bash
celery -A config worker --loglevel=info --concurrency=2
```

Then upload a CV from browser and confirm:

- queued/status component appears
- worker receives `apps.cvs.tasks.parse_cv`
- status eventually becomes completed or failed safely
- no private URL leak

If browser proof is not possible, state clearly: `BLOCKED_HUMAN_VISUAL_SIGNOFF`.

## Verdict

Return exactly one:

```text
FAIL
BLOCKED_HUMAN_VISUAL_SIGNOFF
```

Use `FAIL` for any failing check, phase boundary violation, privacy regression, or untested critical behavior.
Use `BLOCKED_HUMAN_VISUAL_SIGNOFF` only if automated checks pass and browser/admin signoff remains.
