# Phase 16H Batch 4 — Codex Review Report

**Date:** 2026-07-02
**Reviewer:** Codex (Antigravity Agent)
**Status:** ✅ PASS WITH REPAIRS

---

## Summary

Batch 4 implemented the v16 visual port for recommendations, saved jobs, and match detail
pages. After Codex repairs (trailing whitespace + CSS deduplication), all required automated
checks pass. Two residual concerns are flagged for senior review before approval.

---

## Files Changed by Gemini (Batch 4)

| File | Change type |
|---|---|
| `templates/dashboard/recommendations.html` | Visual port — scoped in `<main class="recommendations-v16">` |
| `templates/dashboard/saved_jobs.html` | Visual port — scoped in `<main class="saved-v16">` |
| `templates/matching/match_detail.html` | Visual port — scoped in `<main class="match-v16">` |
| `templates/recommendations/partials/recommendation_card.html` | Refactored card to `job-card` layout with `match-badge` score ring |
| `templates/recommendations/partials/recommendation_list.html` | Updated states (pending/stale/failed/empty) to v16 pattern |
| `static/src/css/app.css` | Added scoped component rules for Batch 4 page wrappers |
| `apps/matching/tests.py` | Adjusted assertions to match new copy strings |
| `apps/recommendations/tests/test_integration.py` | Adjusted assertions + minor cleanup |
| `docs/phases/post_launch/phase_16h_ui_ux_overhaul/batch4_gemini_report.md` | New (untracked) |

## Files Changed by Codex (Repairs)

| File | Change type |
|---|---|
| `templates/dashboard/recommendations.html` | Removed trailing whitespace on blank line 19 |
| `apps/recommendations/tests/test_integration.py` | Removed trailing whitespace on 6 lines (476, 480, 493, 501, 505, 507) |
| `static/src/css/app.css` | Deduplicated shared rule blocks; added Batch 4 scopes to `--var` blocks |

---

## Scope Verdict

**PASS — Batch 4 stayed inside allowed scope.**

| Check | Result |
|---|---|
| `templates/base.html` changed | NO |
| `templates/jobs/` changed | NO |
| `templates/account/` changed | NO |
| `templates/dashboard/profile.html` changed | NO |
| `templates/dashboard/cv_manage.html` changed | NO |
| `templates/dashboard/account.html` changed | NO |
| `templates/core/about.html` changed | NO |
| `apps/core/models.py` changed | NO |
| `apps/core/forms.py` / `migrations/` changed | NO |
| New models / migrations | NONE |
| OpenRouter / LLM / France Travail calls | NONE |
| Notification bell / Notification model | NONE |
| i18n / language switcher | NONE |
| ContactMessage / About backend | NONE |

---

## Recommendations Verdict

**PASS WITH NOTE**

- Auth (`@login_required` via `apps/dashboard/views.py`) preserved — redirect to login confirmed by existing tests.
- Existing refresh form preserved with CSRF token.
- Feedback form HTMX behavior not touched (views.py untouched).
- Empty/blocked/stale states rendered from real `result` context — no fake data.
- Algorithm/scoring service untouched.

**Note:** The `recommendations.html` template removed the sidebar (`{% include 'dashboard/sidebar.html' %}`).
Confirm this was expected for the v16 full-width layout.

---

## Saved Jobs Verdict

**PASS**

- Auth preserved — redirect to login confirmed.
- Cards iterate over real `saved_jobs` queryset.
- Links use `saved_job.job.public_id` — no integer IDs exposed.
- `{% include 'jobs/partials/save_button.html' with job=saved_job.job is_saved=True %}` preserved.
- Empty state is a real conditional, not placeholder content.
- `is_publicly_visible` filter preserved to guard inactive job display.

---

## Match Detail Verdict

**PASS WITH CONCERN**

- Deterministic scoring fields displayed correctly: `fit_score`, `technical_skills_score`,
  `experience_score`, `language_score`, `role_title_score`.
- No formula change — scores come from existing `match` context variable.
- `llm_explanation_status == "generated"` gate preserved — LLM section only shows when generated.
- `llm_explanation_status="failed"` does NOT become a deterministic match failure.
- `match.job.public_id` used for save button and "Retour à l'offre" link.
- No raw CV file paths or MEDIA_URL exposed.
- `non_it_low_relevance_job` and `insufficient_job_technical_signal` risk flag checks preserved.

**Concern:** The `"Mobilité / contrat"` static advisory block was removed and the corresponding
test assertions (`"Mobilité / contrat"`, `"Vérifiez la localisation"`) were also removed.
This is a UI copy decision (removing static mobility/visa advice). Senior reviewer should confirm intent.

---

## CSS / Theme Verdict

**PASS WITH REPAIR APPLIED**

**Original defect:** Batch 4 added `.recommendations-v16`, `.saved-v16`, `.match-v16` to
each existing rule block from Batches 1–3, resulting in each shared utility rule appearing
**4×** in the file. CSS file grew from 1,011 lines to 2,762 lines (+1,751 redundant lines).

**Repair applied:** Python deduplication collapsed repeated rule blocks to one selector group
per rule. Three new scopes added to the `--var` light/dark blocks. CSS now 2,132 lines.

**Residual:** Some `@media` breakpoint blocks retain the 4× duplication pattern inherited
from Batches 1–3. This is a pre-existing pattern outside Batch 4 repair scope.

| Check | Result |
|---|---|
| Scoped selectors used (`.recommendations-v16`, `.saved-v16`, `.match-v16`) | YES |
| `static/src/css/app.css` is the source file | YES |
| `static/css/app.css` rebuilt via `npm run css:build` | REBUILT SUCCESSFULLY |
| Large inline `<style>` blocks in templates | NONE |

---

## Tests Verdict

**PASS**

### Focused suite (apps.recommendations, apps.matching, apps.dashboard)

```
Ran 131 tests in 5.850s
OK
```

### Full suite

```
Ran 636 tests in 106.332s
OK
```

Note: `FAILURE: LLM success count (0)` in full suite is a pre-existing infrastructure
limitation (LLM key not available locally). Not caused by Batch 4.

### Test assertion changes — apps/matching/tests.py

| Method | Removed assertions | Added assertions |
|---|---|---|
| `test_match_detail_unavailable_...` | `"Données insuffisantes pour calculer un match fiable"`, `"Offre probablement non IT"` | `"Données insuffisantes"` |
| `test_match_detail_low_confidence_...` | `"estimation prudente"`, `"L'analyse de cette offre est limitée."` | `"À vérifier"` |
| `Phase15GHardeningTests::test_match_detail_renders_correctly_...` | `"Mobilité / contrat"`, `"Vérifiez la localisation"`, `"Compétences requises manquantes"`, `"Points de vigilance"`, `"border-rose-200"` | `"Manquantes"` |

Assessment: Copy string changes are correct. Removing `"border-rose-200"` is correct
(Tailwind class removed in favour of CSS var). Removing the `"Points de vigilance"` assertion
is ambiguous — the heading still exists in the template (line 121). Senior reviewer should
confirm this was intentional.

### Test assertion changes — apps/recommendations/tests/test_integration.py

| Method | Removed | Added |
|---|---|---|
| `test_recommendation_card_hides_placeholder_...` | `"tta-score-ring-prominent"`, `"tta-skill-chip-success"`, `"Vu le"` | `"match-badge"`, `"skill ok"` |
| `test_recommendation_card_hides_match_cta_...` | `"Voir la compatibilité"` | `assertNotContains("Détails")` |
| `test_recommendation_card_warning_copy_...` | `"À renforcer"`, `"Certaines compétences..."`, `"tta-skill-chip-missing"` | `"skill missing"` |
| `test_saved_jobs_card_hides_placeholder_...` | `"Vu le"` | duplicate `assertNotContains` (harmless) |

All class name changes are correct. Old `tta-*` classes replaced with v16 class names.
`"Vu le"` removal reflects the real template change (date in meta span, no prefix label).

---

## Command Results

| Command | Result |
|---|---|
| `git status --short --branch` | `## dev...origin/dev`, 8 modified + 1 untracked |
| `python manage.py check` | System check identified no issues (0 silenced) |
| `python manage.py makemigrations --check --dry-run` | No changes detected |
| Focused test suite (131 tests) | OK |
| Full test suite (636 tests) | OK |
| `npm run css:build` | Done in 927ms |
| `git diff --check` | PASS |
| Custom whitespace scanner | PASS (after Codex repair) |

---

## Required Fixes Before Senior Approval

| # | Issue | Severity | Status |
|---|---|---|---|
| 1 | Trailing whitespace in `recommendations.html:19` | Low | FIXED by Codex |
| 2 | Trailing whitespace in `test_integration.py` (6 lines) | Low | FIXED by Codex |
| 3 | CSS 4× duplication of shared utility rules (+1751 lines) | Medium | FIXED by Codex (partial) |
| 4 | `"Points de vigilance"` assertion removed — may mask regressions | Medium | REVIEW — senior confirm |
| 5 | Sidebar removed from `recommendations.html` | Low | REVIEW — confirm v16 intent |
| 6 | `@media` blocks retain 4× duplication (pre-existing Batch 1-3 pattern) | Low | DEFERRED — out of Batch 4 scope |

---

## Public ID / Privacy Checks

| Check | Result |
|---|---|
| `saved_job.job.public_id` used for all links | YES |
| `rec.job.public_id` used for recommendation links | YES |
| `rec.match_public_id` used for match detail link | YES |
| `match.job.public_id` used in match detail | YES |
| No integer IDs in URL construction | CONFIRMED |
| No `file.url` / `MEDIA_URL` / raw CV paths | NONE |
| `CVUpload.all_objects` used in Batch 4 files | NOT USED |

---

## Phase Boundary Confirmation

- No models, migrations, or backend service logic changed.
- No About/contact backend (Batch 5 scope) introduced.
- No notification system, Notification model, or notification bell added.
- No LLM calls introduced. No new scoring formula. No algorithm change.
- No France Travail live API calls.
- No production deployment performed.

---

## No Commit / No Push / No Deploy

Codex has not committed, pushed, or deployed anything.
All changes remain in the working tree only.

---

## Senior Approval Checklist

Before approving Batch 4 and proceeding to Batch 5:

- [ ] Confirm sidebar removal from `recommendations.html` is intentional for v16 full-width layout
- [ ] Confirm `"Points de vigilance"` assertion removal in `test_match_detail_renders_correctly_with_all_sections` is intentional
- [ ] Confirm residual `@media` CSS duplication (pre-existing Batch 1-3 pattern) is acceptable to defer
- [ ] Manually verify recommendations page, saved jobs page, and match detail page in browser (desktop + mobile, light + dark)
