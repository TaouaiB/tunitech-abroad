# Regression and Security Checks

Run:

```bash
grep -R "Phase 1 Note\|Lorem\|example.test\|future phase" templates apps config -n --exclude-dir="__pycache__" || true
```

There must be no user-facing `example.test` except in test fixtures explicitly asserting it is absent.

CV privacy:

```bash
grep -R "\.file.url\|cv.file.url\|raw_text\|private_media" templates apps --exclude-dir="tests" --exclude-dir="__pycache__" -n || true
```

No template should render raw CV text or CV file URL.

LLM boundary:

```bash
grep -R "OpenRouter\|OPENROUTER\|LLM" apps/*/views.py templates -n || true
```

No OpenRouter/LLM in views/templates.

France Travail boundary:

```bash
grep -R "FranceTravailClient\|search_offers" apps/jobs/views.py apps/jobs/services/search.py templates -n || true
```

No live API from public search.

Forbidden frontend stack:

```bash
grep -R "react\|nextjs\|next.js\|vue\|angular\|vite\|bootstrap\|material-ui\|lucide-react" package.json templates static apps -n 2>/dev/null || true
```

Allowed matches only:

- skill taxonomy/test data mentioning React/Next.js as candidate skills
- extractor tests preventing false URL extraction

Secrets:

```bash
git --no-pager diff -- . ':!.env' | grep -iE "OPENROUTER_API_KEY|FRANCE_TRAVAIL_CLIENT_SECRET|client_secret|access_token|Bearer |EMAIL_HOST_PASSWORD|SECRET_KEY" || echo "OK: no obvious secrets in diff"
```

Target country UI removal:

```bash
grep -R "target_country\|Pays cible\|Target country" templates -n || true
```

No user-facing target country field should remain.
