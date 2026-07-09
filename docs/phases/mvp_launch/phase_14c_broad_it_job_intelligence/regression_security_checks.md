# Regression and Security Checks

## Secret check

```bash
git --no-pager diff -- . ':!.env' | grep -iE "OPENROUTER_API_KEY|FRANCE_TRAVAIL_CLIENT_SECRET|client_secret|access_token|Bearer |EMAIL_HOST_PASSWORD|SECRET_KEY" || echo "OK: no obvious secrets in diff"
```

## Forbidden stack check

```bash
grep -R "react\|nextjs\|vue\|angular\|vite\|bootstrap\|material-ui\|lucide-react" package.json templates static apps -n 2>/dev/null || true
```

Allowed matches only:

- skills/taxonomy terms like React/Vue/Angular as job skills.
- job descriptions or tests.

No frontend framework imports/build pipeline.

## Public live API check

Public job search, job detail, match, recommendation, and dashboard pages must not call France Travail live.

```bash
grep -R "FranceTravailClient\|search_offers\|api.francetravail" \
  apps/jobs apps/matching apps/recommendations apps/dashboard templates/jobs templates/matching templates/recommendations \
  --exclude-dir="tests" --exclude-dir="__pycache__" -n || true
```

Expected: no live France Travail calls from public request flow. Matches inside ingestion services, management commands, docs, or tests must be reviewed and explained.

## LLM-in-view check

```bash
grep -R "OpenRouter\|OPENROUTER\|LLM\|llm" apps templates \
  --include="views.py" --include="*.html" --exclude-dir="tests" --exclude-dir="__pycache__" -n || true
```

Also check view packages if present:

```bash
find apps -path "*/views/*.py" -print -exec grep -n "OpenRouter\|OPENROUTER\|LLM\|llm" {} \; || true
```

Expected: no LLM call from views/templates.

## Raw private data check

```bash
grep -R "raw_text\|file\.url\|cv\.file\.url" templates apps --exclude-dir="tests" --exclude-dir="__pycache__" -n || true
```

Expected: no CV raw text or private file URL in templates.

## Raw internal flag/state leak check

```bash
grep -R "non_it_low_relevance_job\|no_required_skills_extracted\|low_confidence_job_skills\|insufficient_job_technical_signal\|excluded_non_it\|generic_only\|match_confidence" templates -n || true
```

Expected: no raw internal flags/states in templates unless inside safe conditional logic that renders French human labels. Report every match.

## Mapping coverage check

Search tests for required examples:

```bash
grep -R "Data Scientist\|Web Developer\|photographie\|alternance\|support client\|chef de projet commercial\|Java\|Spring\|Angular" apps/*/tests apps/**/tests -n || true
```

Expected: tests cover positive broad IT, weak IT, apprenticeship, and negative non-IT boundaries.

## Root junk cleanup

```bash
find . -maxdepth 1 -type f \( -name 'scratch_*.py' -o -name 'verify.py' \) -print
find . -path './.venv' -prune -o -type f -name '*.pyc' -print | head
```

Expected: no project-root scratch files; no committed pyc files.
