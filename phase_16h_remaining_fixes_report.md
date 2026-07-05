# Phase 16H Remaining Exactness Fixes — Report

## Summary
All owner correction items have been applied across auth, recommendations, saved-jobs, profile/settings, and header navigation. 646 tests pass. CSS rebuilt. Screenshots taken.

---

## 1. Auth

### Redirects
- `LOGIN_REDIRECT_URL = "/jobs/"` and `LOGOUT_REDIRECT_URL = "/jobs/"` in `config/settings/base.py`.
- Login with valid credentials POSTs to `/accounts/login/` and returns `302 → /jobs/`.
- Logout POSTing the form on `/accounts/logout/` returns `302 → /jobs/`.
- Updated `apps/accounts/tests.py` assertion to expect `/jobs/` after login.

### Typing / field errors
- `data-validate` added to both login and signup email/password forms in `templates/account/login.html` and `templates/account/signup.html`.
- `v16_ui.js` client-side validation now runs on auth forms too. Invalid fields get `.invalid`/`.has-error`, forms get `.shake`, and a toast shows `Corrigez les champs en rouge` (mapped from `Fix highlighted fields`).
- Server-side non-field errors still render inline as Django `has-error` blocks.
- The form still POSTs normally to allauth after client validation passes.

### Wrong-credentials notification
- Allauth renders the standard error in a `field has-error` block. No fake success toast exists. The `data-success` attributes were removed in earlier phases and are not present on auth forms.

---

## 2. Header Nav (base.html)

- Removed `Profil` and `Paramètres` from the authenticated main nav.
- Authenticated main nav is now:
  - Offres
  - Recommandations
  - Favoris
  - À propos
  - Avatar dropdown (Profil / Paramètres / Déconnexion)
- Anonymous nav unchanged:
  - Offres
  - Recommandations
  - À propos
  - Connexion

---

## 3. Recommendations

- **Removed** the conditional `Détails` button from `templates/recommendations/partials/recommendation_card.html`.
- The card still shows the match badge and save button.
- Updated `apps/recommendations/tests/test_integration.py` assertion: changed `assertContains` the match detail link to `assertNotContains`.

---

## 4. Saved Jobs / Favoris

- Added `remove_card=True` parameter when including the save button partial in `templates/dashboard/saved_jobs.html`.
- In `templates/jobs/partials/save_button.html`, the unsave form now conditionally includes `hx-on::after-request` that removes the closest `article.job-card` on successful unsave.
- This means clicking the unsave button on the `/dashboard/saved-jobs/` page will remove the card via HTMX without a full page reload.

---

## 5. Profile → Progression Block

- Simplified the `Progression` notice list in both `templates/dashboard/profile.html` and `templates/dashboard/cv_manage.html`.
- **Before**: dot + bold label + `.small` sub-line (e.g., `Requis pour se connecter par email`, `CV actif détecté`, `Infos manuelles`).
- **After**: dot + bold label only, matching the prototype `profile-setup.html` minimal style.
- This prevents overflow/awkward wrapping and keeps the items cleanly inside the sticky aside card.

---

## 6. Settings / Paramètres (Prototype match)

All settings subpages now use the consistent 5-tab nav and mobile-toggle pattern from `prototype_full_v16/settings.html`.

### Account (`templates/dashboard/account.html`)
- Nav: Compte | Email | Sécurité | Connexions | Supprimer
- Mobile toggle `data-settings-toggle="account"`
- Content wrapped in `.settings-mobile-section.mobile-section-open`

### Email preferences (`templates/dashboard/email_preferences.html`)
- Same nav.
- Mobile toggle `data-settings-toggle="email"`
- Form wrapped in `#email.settings-mobile-section.mobile-section-open`

### Security (`templates/account/password_change.html`)
- Refactored from a standalone card into the full settings grid with nav.
- Mobile toggle `data-settings-toggle="security"`
- Form wrapped in `#security.settings-mobile-section.mobile-section-open`

### Connections (`templates/dashboard/connections.html`)
- Added missing `Sécurité` nav link.
- Added mobile toggle and `.settings-mobile-section` wrapper around the card.

### Delete account (`templates/dashboard/delete_account.html`)
- Added missing `Sécurité` nav link.
- Added mobile toggle `data-settings-toggle="danger"`.
- Restored missing `<form method="post">` opening tag (was accidentally dropped in a prior edit).
- Form now wraps content properly and is closed by `</form>`.

---

## 7. CV Manage

- Progression block simplified to match profile (dot + bold label only, no `.small` sub-lines).

---

## 8. Test Results

```
Found 646 test(s)
Creating test database...
Destroying old test database...
... (full run)
646 tests, OK
```

**Two tests were updated to match the new redirects/UI:**
- `test_existing_normal_email_password_login_still_works`: expected redirect changed from `/dashboard/` → `/jobs/`.
- `test_recommendation_card_hides_placeholder_badges_and_links_existing_match`: changed to assert the match detail link is **not** present (because Details button was removed).

---

## 9. CSS Build

- Ran `npx tailwindcss -i ./static/src/css/app.css -o ./static/css/app.css --minify`
- Built successfully. Output: `static/css/app.css` (≈139KB minified).

---

## 10. Grep Checks

Searched for forbidden patterns (eval, exec, __import__, subprocess, os.system, cv.url, exposed CV URLs, insecure ORM queries, duplicate `data-settings-toggle` attributes, etc.). Only expected matches were found in:
- `docs/` directories (documentation)
- Test files (legitimate `.objects.get` usage)
- Production `apps/cvs/services/deletion.py` (legitimate)
- No dangerous patterns in production templates or JS.

---

## 11. Screenshots

All 13 screenshots saved to `screenshots/`:
1. `01_login.png` — Login page (anonymous)
2. `02_login_error.png` — Wrong credentials error state
3. `03_after_login_redirect.png` — After login redirect (`/jobs/`)
4. `04_recommendations.png` — Recommendations page (no Details button)
5. `05_favoris.png` — Saved jobs page
6. `06_profile.png` — Profile page with clean Progression aside
7. `07_settings_account.png` — Account settings with nav + mobile toggle
8. `08_settings_email.png` — Email preferences
9. `09_settings_security.png` — Password change page in settings grid
10. `10_settings_connections.png` — Connections page with nav
11. `11_settings_delete.png` — Delete account with restored form tag
12. `12_about.png` — About page
13. `13_logout_redirect.png` — Logout confirmation page (POST sends to `/jobs/`)

---

## 12. Risks / Manual Steps Remaining

1. **Logout redirect on GET vs POST**: The `/accounts/logout/` GET shows a confirmation form (standard allauth). When the user POSTs the form, LOGOUT_REDIRECT_URL sends them to `/jobs/`. There is no automatic GET redirect, which is correct for safety—this matches allauth default behavior.
2. **Unsave card removal**: Verified the HTMX `hx-on::after-request` attribute is present in the saved-jobs context (`remove_card=True`). A live browser test with actual HTMX swap is the only way to fully confirm the card disappears.
3. **Auth typing shake/toast**: Verified in v16_ui.js and templates. A live browser test is needed to confirm the visual shake and toast on invalid fields.
4. **FR/EN switch**: Not changed; remains at the last verified state.
5. **Footer**: Not changed; remains at the last verified state.

---

## 13. Files Changed

| File | Change |
|------|--------|
| `config/settings/base.py` | `LOGIN_REDIRECT_URL`, `LOGOUT_REDIRECT_URL` → `/jobs/` |
| `templates/base.html` | Removed Profil/Paramètres from authenticated nav |
| `templates/account/login.html` | Added `data-validate`, error blocks, field IDs |
| `templates/account/signup.html` | Added `data-validate`, error blocks |
| `templates/account/password_change.html` | Refactored into settings grid with nav + toggle |
| `static/js/v16_ui.js` | Auth forms now get client validation + toast before submit |
| `templates/recommendations/partials/recommendation_card.html` | Removed `Détails` button |
| `templates/jobs/partials/save_button.html` |Added conditional `hx-on::after-request` for card removal |
| `templates/dashboard/saved_jobs.html` | Passed `remove_card=True` to save button |
| `templates/dashboard/profile.html` | Simplified Progression notice items |
| `templates/dashboard/cv_manage.html` | Simplified Progression notice items |
| `templates/dashboard/account.html` | Added Sécurité link, mobile toggle wrapper |
| `templates/dashboard/email_preferences.html` | Added Sécurité link, mobile toggle wrapper |
| `templates/dashboard/connections.html` |Added Sécurité link, mobile toggle, section wrapper |
| `templates/dashboard/delete_account.html` | Restored `<form>` tag, added mobile toggle |
| `apps/accounts/tests.py` | Updated login redirect assertion to `/jobs/` |
| `apps/recommendations/tests/test_integration.py` | Updated to assert no match detail link |
| `static/css/app.css` | Rebuilt from Tailwind |

---

All corrections applied. Tests pass. No commits made.
