# Codex Verification Prompt — Phase 15G Matching Explanation and Recommendation UX Hardening

You are Codex verifying Phase 15G for TuniTech Abroad.

Start from Warp using:

```bash
codex-tunitech
```

Do not use plain `codex` if the project relies on the rootless Podman socket.

## Mission

Verify, repair if needed, and report on Phase 15G.

This is not a feature expansion phase. It is a strict quality hardening pass for match explanation and recommendation UX.

## Files to read first

- `AGENTS.md`
- `docs/phases/phase_15g_matching_explanation_recommendation_ux_hardening/tasks.md`
- `docs/phases/phase_15g_matching_explanation_recommendation_ux_hardening/scoring_policy.md`
- `docs/phases/phase_15g_matching_explanation_recommendation_ux_hardening/noisy_skill_policy.md`
- `docs/phases/phase_15g_matching_explanation_recommendation_ux_hardening/refresh_recommendations_policy.md`
- Gemini agent report, if present.

## What to verify

Architecture:

- No forbidden stack.
- No OpenRouter/LLM call from views/templates/models/admin display.
- No France Travail call from public search/match/recommendation views.
- Views thin.
- Business logic in services/presentation helpers.
- No matching formula overbuild.
- No UI redesign.
- No CV privacy leak.
- No secrets in diff.

Functional requirements:

1. Location does not affect final score.
2. Mobility/location note remains informational.
3. `JSON` is hidden from missing/optional/recommendation display when implied by stronger skills.
4. Specific advanced JSON/XML skills are not globally suppressed.
5. `Angular` or true required missing skills still appear.
6. Redundant `À renforcer / Compétences obligatoires non détectées` card is removed.
7. `Actions recommandées` is French.
8. `Actions recommandées` is red/priority-styled when required skills are missing.
9. Recommendation refresh button exists.
10. Refresh endpoint is POST-only, authenticated, CSRF-protected, and calls service/task only.
11. Tests cover the above.

## Agent behavior

You may fix in-scope issues yourself.

Do not block on staged/unstaged/mixed worktree state unless there is a real architecture/product/security/privacy/dependency issue.

Block only for:

- forbidden stack
- provider calls in views/templates
- France Travail calls in public views
- secret exposure
- CV privacy leak
- public integer ID regression
- phase boundary violation
- tests still failing after repair

## Commands to run

```bash
cd ~/Projects/tunitech-abroad
source .venv/bin/activate

git status --short --branch
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test --settings=config.settings.local --parallel 1
npm run css:build
python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
git diff --check
```

Security greps:

```bash
grep -R "OpenRouterClient\|OPENROUTER\|run_llm\|client.chat\|_make_request" apps/*/views.py templates -n 2>/dev/null || true
grep -R "FranceTravailClient\|search_offers\|api.francetravail" apps/*/views.py templates -n 2>/dev/null || true
grep -R "file.url\|cv.file.url\|upload.file.url\|raw_text\|raw_response_text\|raw_response_json" templates apps -n 2>/dev/null || true
git diff -- . ':!.env' ':!.env.*' | grep -iE "sk-or-|Bearer [A-Za-z0-9_.-]{20,}|OPENROUTER_API_KEY=.*[^=]|FRANCE_TRAVAIL_CLIENT_SECRET=.*[^=]|EMAIL_HOST_PASSWORD=.*[^=]" || echo "OK: no obvious secrets in diff"
```

## Report

Create:

```text
docs/phases/phase_15g_matching_explanation_recommendation_ux_hardening/codex_report.md
```

Use the template.

Verdict must be one of:

```text
PASS
REPAIRED_PASS
BLOCKED
FAIL
```

PASS only if all checks pass and no repairs were needed.
REPAIRED_PASS if you fixed in-scope issues and all checks pass.
BLOCKED only for true blockers.
FAIL only if the implementation remains wrong after reasonable repair.
