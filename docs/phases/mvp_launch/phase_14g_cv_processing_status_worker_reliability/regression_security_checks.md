# Regression & Security Checks — Phase 14G

Run these before final report.

## No CV private file leakage

```bash
grep -R "file.url\|cv.file.url\|upload.file.url\|raw_text\|extracted_text" templates apps -n 2>/dev/null || true
```

If results appear, inspect them. It is a blocker if user-facing templates expose private CV file URLs or raw extracted CV text.

## No OpenRouter/LLM in views

```bash
grep -R "OpenRouter\|OPENROUTER\|OpenRouterClient\|run_llm\|llm" apps/*/views.py apps/*/views templates -n 2>/dev/null || true
```

Stored text display is not necessarily a blocker, but any view-time LLM call is a blocker.

## No internal integer IDs in user-facing CV routes

```bash
grep -R "CVUpload.objects.get(id=\|cv_id\|<int:" apps templates -n 2>/dev/null || true
```

Inspect results. User-facing CV status/detail routes should use UUID `public_id`.

## Soft-delete manager check

```bash
grep -R "CVUpload.all_objects" apps templates -n 2>/dev/null || true
```

`all_objects` is allowed only for admin/privacy/deletion/internal tasks. It is a blocker in user-facing views.

## Secrets check

```bash
git diff -- . ':!.env' | grep -iE "OPENROUTER_API_KEY|FRANCE_TRAVAIL_CLIENT_SECRET|client_secret|access_token|password|secret" || echo "OK: no obvious secrets in diff"
```

Test fixture passwords may appear; real secrets are a blocker.
