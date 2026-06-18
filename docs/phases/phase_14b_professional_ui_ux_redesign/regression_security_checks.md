# Regression and Security Checks

Run before final report.

## Placeholder text

```bash
grep -R "Phase 1 Note\|Lorem\|example.test\|future phase" templates apps -n || true
```

Expected: no user-facing placeholder remains.

## CV privacy

```bash
grep -R "\.file.url\|cv.file.url\|raw_text" templates apps --exclude-dir="tests" -n || true
```

Expected:

- no user-facing template exposes private file URL
- no template displays full raw CV text
- test references are acceptable only if safe

## External API boundary

```bash
grep -R "FranceTravailClient\|search_offers" apps/jobs/views.py apps/jobs/services/search.py templates -n || true
```

Expected:

- no public search path calls France Travail

## LLM boundary

```bash
grep -R "OpenRouter\|LLM" apps/*/views.py templates -n || true
```

Expected:

- no OpenRouter call from views
- no unsafe template trigger calling LLM directly
- display copy is okay if existing safe backend route exists

## Forbidden stack

```bash
grep -R "react\|nextjs\|next.js\|vue\|angular\|bootstrap\|material-ui" package.json templates static apps -n 2>/dev/null || true
```

Expected:

- no new forbidden frontend framework

## Secrets

```bash
git --no-pager diff -- . ':!.env' | grep -iE "OPENROUTER_API_KEY|FRANCE_TRAVAIL_CLIENT_SECRET|client_secret|access_token|Bearer " || echo "OK: no obvious secrets in diff"
```

Expected:

```text
OK: no obvious secrets in diff
```

## Git hygiene

```bash
git status --short
find . -type d -name "__pycache__" -print
find . -name "*.pyc" -print
find . -maxdepth 5 -name "*.pdf" -print
find . -maxdepth 5 -name "*.sqlite3" -print
```

Do not stage accidental files.
