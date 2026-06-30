# Regression and Security Checks

Run these from repo root:

```bash
git diff -- . ':!.env' | grep -iE "OPENROUTER_API_KEY|FRANCE_TRAVAIL_CLIENT_SECRET|client_secret|access_token|password|secret" || echo "OK: no obvious secrets in diff"

grep -R "cdn.tailwindcss.com" templates config static -n || true
grep -R "React\|Next.js\|next/\|createRoot\|vue\|angular" package.json templates static apps -n 2>/dev/null || true
grep -R "FranceTravailClient\|france_travail" apps/*/views.py templates -n 2>/dev/null || true
grep -R "OpenRouterClient\|OPENROUTER\|run_llm\|llm" apps/*/views.py templates -n 2>/dev/null || true
grep -R "file.url\|cv.file.url\|upload.file.url\|raw_text\|extracted_text" templates apps -n 2>/dev/null || true
grep -R "CVUpload.objects.get(id=\|cv_id\|<int:" apps templates -n 2>/dev/null || true
grep -R "SocialAccount.objects.filter(id=.*request.POST\|disconnect_id" apps templates -n 2>/dev/null || true
grep -R "CELERY_BEAT_SCHEDULE = {}" config -n || true

git status --short --ignored | grep node_modules && echo "ERROR: node_modules visible" || echo "OK: node_modules not visible"
find . -maxdepth 4 -name 'celerybeat-schedule*' -print
```

Review grep output manually. Some false positives are expected:

- React/Vue/Angular as job skills or placeholders.
- Stored `match.llm_explanation` display.
- `raw_text` in models/services/tests/admin exclusions.
