# Regression and Security Checks — Phase 14H-C

Run after implementation:

```bash
grep -R "cdn.tailwindcss.com" templates config static -n || true
grep -R "React\|Next.js\|next/\|createRoot\|vue\|angular" package.json templates static apps -n 2>/dev/null || true
grep -R "FranceTravailClient\|france_travail" apps/*/views.py templates -n 2>/dev/null || true
grep -R "OpenRouterClient\|OPENROUTER\|run_llm\|llm" apps/*/views.py templates -n 2>/dev/null || true
grep -R "file.url\|cv.file.url\|upload.file.url\|raw_text\|extracted_text" templates apps -n 2>/dev/null || true
git diff -- . ':!.env' | grep -iE "OPENROUTER_API_KEY|FRANCE_TRAVAIL_CLIENT_SECRET|client_secret|access_token|password|secret" || echo "OK: no obvious secrets in diff"
git status --short | grep node_modules && echo "ERROR: node_modules is visible to git" || echo "OK: node_modules not visible"
```

Interpretation:
- `cdn.tailwindcss.com` must produce no matches.
- React/Next/Vue/Angular must produce no real dependency or app code matches.
- France Travail/OpenRouter matches in views/templates are blockers unless they are harmless static text in docs/tests outside the app path.
- `match.llm_explanation` display in a template is allowed; it is stored explanation display, not an LLM call.
- raw CV text/file URL must not appear in templates. Matches in models/services/tests/admin exclusions may be okay but must be reviewed.
