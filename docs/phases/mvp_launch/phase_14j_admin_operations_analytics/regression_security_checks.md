# Phase 14J Regression and Security Checks

Run after implementation.

## Stack and frontend boundaries

```bash
grep -R "cdn.tailwindcss.com" templates config static -n || true
grep -R "React\|Next.js\|next/\|createRoot\|vue\|angular\|Vite" package.json templates static apps -n 2>/dev/null || true
```

Non-empty matches must be inspected. Skill names like React in job text are fine. Framework runtime imports are not fine.

## External-call boundaries

```bash
grep -R "FranceTravailClient\|france_travail" apps/*/views.py apps/*/admin.py templates -n 2>/dev/null || true
grep -R "OpenRouterClient\|OPENROUTER\|run_llm\|llm" apps/*/views.py apps/*/admin.py templates -n 2>/dev/null || true
```

Admin actions should not call external clients directly. They may call services/tasks if existing architecture supports it.

## CV privacy

```bash
grep -R "file.url\|cv.file.url\|upload.file.url\|raw_text\|extracted_text" templates apps/*/admin.py apps -n 2>/dev/null || true
```

Non-empty backend/test/admin exclusion matches are expected. User-facing templates and admin list displays must not expose raw CV text or public CV links.

## Public IDs

```bash
grep -R "<int:" apps templates config -n 2>/dev/null || true
```

No public app route should expose integer IDs.

## Secrets

```bash
git diff -- . ':!.env' | grep -iE "OPENROUTER_API_KEY|FRANCE_TRAVAIL_CLIENT_SECRET|client_secret|access_token|password|secret|api_key|token" || echo "OK: no obvious secrets in diff"
```

If non-empty, inspect manually. Test names mentioning tokens may be safe, but real secrets are blocker.

## Admin sensitive list displays

Inspect:

```bash
grep -R "list_display" apps/*/admin.py -n
```

Blockers:

- raw CV text in list display
- raw unsubscribe token in list display
- LLM raw prompt/response payload in list display
- API keys/secrets in list display
- CV direct file URL in list display
