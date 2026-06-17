# Codex Verification Prompt — Phase 14B.3R

You are verifying Phase 14B.3R. Do not implement broad changes unless a verification command reveals a small obvious defect that blocks verification. Prefer reporting over rewriting.

Read:

```text
AGENTS.md
docs/phases/phase_14b3r_data_correct_ui_refinement/README.md
docs/phases/phase_14b3r_data_correct_ui_refinement/acceptance.md
docs/phases/phase_14b3r_data_correct_ui_refinement/agent_report.md
```

## Verify hard gates

Run:

```bash
cd ~/Projects/tunitech-abroad
source .venv/bin/activate

git status --short
git diff --stat

python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py migrate --settings=config.settings.local
python manage.py seed_demo_data --settings=config.settings.local
python manage.py test apps.cvs apps.profiles apps.recommendations apps.matching --settings=config.settings.local
python manage.py test --settings=config.settings.local
```

## Verify extractor acceptance

Run a shell check or inspect tests to prove:

- location = Tunis, Tunisia
- LinkedIn normalized
- GitHub normalized
- portfolio normalized
- `website_url` is not `https://Next.js`
- target roles are extracted
- noise skills are filtered
- at least five CV fixtures exist

## Verify profile/recommendations

Prove:

- empty/incomplete profile has blocked state with exact missing fields
- complete profile + active jobs creates recommendations
- no fake success run with zero recommendations for incomplete profile
- profile completion is not contradictory

## Verify UI/security

Run greps from `regression_security_checks.md`.

Check rendered pages with Django client or browser/headless if available:

- `/dashboard/cv/`
- `/dashboard/profile/`
- `/dashboard/recommendations/`
- `/jobs/`
- job detail
- quick match
- match detail

## Verdict rules

Return one of:

```text
PASS
FAIL
BLOCKED
BLOCKED_HUMAN_VISUAL_SIGNOFF
```

Use `BLOCKED_HUMAN_VISUAL_SIGNOFF` if all automated/browser checks pass but Baha has not manually approved Chrome visual/product flow.

Do not claim PASS if:

- one CV fixture only
- `https://Next.js` can still occur
- recommendations remain vague empty state
- profile completion is contradictory
- raw CV text or CV URL exposed
- forbidden stack added
- full tests not run
