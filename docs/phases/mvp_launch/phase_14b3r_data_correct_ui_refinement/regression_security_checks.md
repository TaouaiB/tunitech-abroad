# Regression and Security Checks

Run after implementation.

## No placeholders

```bash
grep -R "Phase 1 Note\|Lorem\|example.test\|future phase" templates apps -n --exclude-dir="__pycache__" || true
```

`example.test` may appear inside test fixtures or synthetic CV data. It must not appear in live product copy unless clearly inside test-only files.

## CV privacy

```bash
grep -R "\.file.url\|cv.file.url\|raw_text\|private_media" templates apps --exclude-dir="tests" --exclude-dir="__pycache__" -n || true
```

No raw CV text or private CV URL in templates.

## External API boundaries

```bash
grep -R "OpenRouter\|OPENROUTER\|LLM" apps/*/views.py templates -n --exclude-dir="__pycache__" || true
```

No OpenRouter/LLM call from views/templates.

```bash
grep -R "FranceTravailClient\|search_offers" apps/jobs/views.py apps/jobs/services/search.py templates -n --exclude-dir="__pycache__" || true
```

No France Travail live call from public search path.

## Forbidden stack

```bash
grep -R "react\|nextjs\|next.js\|vue\|angular\|vite\|bootstrap\|material-ui\|lucide-react" package.json templates static apps -n 2>/dev/null || true
```

Allowed appearances:

- skill names in tests/fixtures/job data
- CV fixture technology names
- normal job data skills

Forbidden appearances:

- frontend dependencies
- imports
- runtime template/CDN framework usage

## Secrets in diff

```bash
git --no-pager diff -- . ':!.env' | grep -iE "OPENROUTER_API_KEY|FRANCE_TRAVAIL_CLIENT_SECRET|client_secret|access_token|Bearer |EMAIL_HOST_PASSWORD|SECRET_KEY" || echo "OK: no obvious secrets in diff"
```

## Bad URL regression

```bash
grep -R "https://Next.js\|https://React\|https://Node.js\|https://Django\|https://PostgreSQL" . --exclude-dir=".git" --exclude-dir="__pycache__" -n || true
```

No runtime data fixtures should produce those as profile/website values.
