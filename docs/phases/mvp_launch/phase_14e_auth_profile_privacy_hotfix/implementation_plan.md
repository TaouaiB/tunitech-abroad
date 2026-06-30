# Phase 14E — Production Auth / Profile / Privacy Hotfix

## Goal Description
Fix production-blocking user account issues related to OAuth login, immediate account deletion, and profile completeness gating, without relying on Celery or creating a new frontend architecture.

## Proposed Changes

### config/settings/base.py
- [MODIFY] Add `SOCIALACCOUNT_EMAIL_AUTHENTICATION = True` and `SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True` to enable connecting existing accounts with verified OAuth emails and avoiding duplicate signups.

### apps/dashboard/views.py
- [MODIFY] `dashboard_profile` to use the profile score directly to determine if the profile is incomplete, setting `is_complete_enough = score >= 50` for the template context.

### templates/dashboard/profile.html
- [MODIFY] Update the logic to only show "Profil incomplet" if `is_complete_enough` is false.
- [MODIFY] If `is_complete_enough` is true, show the correct copy: "Profil prêt pour les recommandations".

### apps/recommendations/services/query.py
- [MODIFY] Update `get_dashboard_recommendations` to block recommendations only if the completeness score is `< 50`, instead of blocking on any missing fields.

### apps/privacy/services/account_deletion.py
- [MODIFY] Update `AccountDeletionService.request_deletion` to call `process_request` synchronously for immediate deletion rather than dispatching a Celery task.

### templates/dashboard/account.html
- [MODIFY] Remove the "Suppression en cours" pending state UI, as deletions will now complete immediately and log the user out.

## Verification Plan
1. Test existing user logging in with Google verified email.
2. Test new user OAuth login without email confirmation.
3. Test account deletion executes immediately and logs the user out.
4. Test profile completeness gating unlocks at `>= 50` score.
