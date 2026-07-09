# Codex Prompt — Phase 16A Senior Cleanup / Commit Hygiene Repair

You are Codex performing a strict senior-review cleanup pass for TuniAtlas Phase 16A.

Current context:
- Product: TuniAtlas / TuniAtlas Jobs.
- Historical/internal name: TuniTech Abroad.
- Current branch should be `dev`.
- Gemini implemented Phase 16A.
- Codex already performed one verification/repair pass and reported local PASS with 558 tests.
- Senior review found that the code is close, but the worktree is not safe to merge because Phase 16A code changes are mixed with broad unrelated documentation moves/deletions and one Phase 15D path change.

Absolute scope:
- Work only on Phase 16A cleanup and commit hygiene.
- Do not start Phase 16B.
- Do not implement job ingestion/search/country-neutral UI hardening now.
- Do not deploy to production.
- Do not commit unless explicitly requested by Baha after this pass.
- Do not print secrets.
- Do not touch `.env`, private media, production secrets, or real CV files.

Read first:
- docs/phases/post_launch/GLOBAL_AGENT_RULES_v1_1.md
- docs/phases/post_launch/shared/execution_policy.md
- docs/phases/post_launch/shared/gemini_codex_tiebreak_policy.md
- docs/phases/post_launch/phase_16a_production_stabilization/tasks.md
- docs/phases/post_launch/phase_16a_production_stabilization/acceptance.md
- docs/phases/post_launch/phase_16a_production_stabilization/codex_review_report.md

Senior-review findings to resolve:

## 1. Worktree hygiene is currently a blocker

The review pack showed around 499 changed files with very large documentation deletions/additions. This cannot be merged as a single Phase 16A code change.

Required action:
1. Run:
   - `git status --short --branch`
   - `git diff --name-status`
   - `git diff --stat`
2. Classify every changed path into one of these groups:
   - `PHASE_16A_CODE`: settings, accounts OAuth linking, robots/sitemap, safe job description rendering, PDF validation, match formula, LLM disabled cleanup, homepage latest jobs, and tests for those items.
   - `PHASE_16A_REPORTS`: Phase 16A report files only.
   - `DOCS_RELOCATION_OR_V3_PACK`: old MVP docs moved under `docs/phases/mvp_launch/`, new post-launch phase docs under `docs/phases/post_launch/`, and v1.1 planning docs under `docs/planning/post_launch/`.
   - `UNRELATED_OR_ACCIDENTAL`: anything else.
3. Do not blindly delete or restore documentation. The docs relocation may be intentional. Instead, produce a clear split plan showing what should be committed separately.
4. If any old MVP docs are deleted from their old flat location and are NOT present under `docs/phases/mvp_launch/`, restore or flag them as accidental.
5. If `apps/skills/services/phase_15d_decisions.py` changed only because docs moved to `docs/phases/mvp_launch/`, classify it as `DOCS_RELOCATION_SUPPORT`, not Phase 16A. Do not include it in the Phase 16A code commit recommendation.

Expected output:
- A new report section named `Commit Split Recommendation` with exact path groups.
- Clear instruction whether the repo needs two commits:
  1. docs relocation / v3 pack commit
  2. Phase 16A code stabilization commit

## 2. OAuth unsafe collision message is provider-specific but adapter supports Google and GitHub

Current issue:
- The unsafe collision message says `Connexion Google...` while the adapter supports both Google and GitHub.

Required fix:
- Make the message provider-neutral, for example `Connexion sociale non liée automatiquement...` or derive provider display name safely.
- Keep the logic in the service/adapter split.
- Keep verified-email linking strict:
  - verified provider email + verified local email -> link allowed
  - unverified provider email -> no silent link
  - unverified local email -> no silent link
- Update/keep tests.

## 3. LLM disabled response still uses a method name containing “mock”

Current issue:
- `OpenRouterClient._get_mock_response()` now returns disabled data, but the method name still says mock.

Required fix:
- Rename it to `_get_disabled_response()` or equivalent.
- Update `_make_request()` and tests accordingly.
- Keep behavior explicit:
  - disabled result
  - zero tokens
  - no fake success
  - no fake extraction contaminating data

## 4. Do not reintroduce `python-magic`

Gemini originally added `python-magic`, but Codex removed it and used direct `%PDF-` header validation.

Required check:
- Confirm `requirements/base.txt` does not contain `python-magic` unless the project intentionally accepts native `libmagic` deployment dependency.
- For this cleanup pass, prefer no `python-magic` dependency.
- PDF validation must still check:
  - `.pdf` extension
  - content type is `application/pdf`
  - header starts with `%PDF-`
  - oversized file rejected
  - pointer reset after validation

## 5. Re-run required checks

After repairs, run:

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test --settings=config.settings.local
git diff --check
```

If the full test suite is too slow, still run it unless it genuinely blocks. Do not claim success without the final summary.

## 6. Produce a review package in the project directory

Create the review zip inside the project root, not `$HOME`.

Use a filename like:

```text
./phase16a_senior_cleanup_review_pack_YYYYMMDD_HHMMSS.zip
```

The zip must include:
- `git/status_short.txt`
- `git/diff_name_status.txt`
- `git/diff_stat.txt`
- `git/full_diff.patch`
- `reports/codex_phase16a_senior_cleanup_report.md`
- command outputs from all checks

Do not include `.env`, private media, real CV files, node_modules, `.venv`, or secrets.

## 7. Final report required

Write:

```text
docs/phases/post_launch/phase_16a_production_stabilization/codex_phase16a_senior_cleanup_report.md
```

The report must include:
- Status: PASS / PARTIAL / FAIL
- Exact fixes made
- Files changed by this cleanup pass
- Full test results
- Commit split recommendation
- Whether Phase 16A code can be committed separately
- Whether docs relocation must be committed separately
- Remaining production deploy follow-up for `/robots.txt` and `/sitemap.xml`
- Confirmation that Phase 16B was not started

Stop after the report and review zip are produced.
