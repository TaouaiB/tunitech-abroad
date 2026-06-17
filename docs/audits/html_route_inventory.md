# HTML Route Inventory

Created before blocker repairs. Updated after the scoped repairs to reflect current styled status. Source files inspected: `config/urls.py`, `apps/*/urls.py`, resolved `django-allauth` account routes, and resolved `django-allauth` socialaccount routes.

Manual Chrome checked is `No` until Baha performs the required human Chrome signoff.

| URL | Name | Source | Template used | Authenticated / anonymous behavior | Styled | Manual Chrome checked |
| --- | --- | --- | --- | --- | --- | --- |
| `/` | `core:home` | `apps/core/urls.py` | `core/home.html` | Anonymous and authenticated users can view. | Yes | No |
| `/health/` | `health` | `config/urls.py` | JSON endpoint, no HTML template | Anonymous and authenticated users can view JSON health. | N/A | No |
| `/privacy/` | `privacy:privacy_policy` | `apps/privacy/urls.py` | `privacy/privacy_policy.html` | Anonymous and authenticated users can view. | Yes | No |
| `/terms/` | `privacy:terms` | `apps/privacy/urls.py` | `privacy/terms.html` | Anonymous and authenticated users can view. | Yes | No |
| `/jobs/` | `jobs:list` | `apps/jobs/urls.py` | `jobs/job_list.html` | Anonymous and authenticated users can search local jobs. | Yes | No |
| `/jobs/<uuid:public_id>/` | `jobs:detail` | `apps/jobs/urls.py` | `jobs/job_detail.html` | Anonymous and authenticated users can view; saved state shown only when authenticated. | Yes | No |
| `/jobs/<uuid:public_id>/save/` | `jobs:save` | `apps/jobs/urls.py` | `jobs/partials/save_button.html` for HTMX, otherwise redirects | Authenticated POST only; anonymous users redirect to login. | Yes | No |
| `/jobs/<uuid:public_id>/unsave/` | `jobs:unsave` | `apps/jobs/urls.py` | `jobs/partials/save_button.html` for HTMX, otherwise redirects | Authenticated POST only; anonymous users redirect to login. | Yes | No |
| `/jobs/<uuid:public_id>/match/` | `matching:create` | `apps/matching/urls.py` | Redirect/service response from class view | Authenticated behavior depends on matching view mixins; route creates a match for a job. | N/A | No |
| `/jobs/<uuid:public_id>/quick-match/` | `matching:quick_match` | `apps/matching/urls.py` | `matching/partials/quick_match_form.html`, `matching/partials/quick_match_result.html` | Public quick match interaction for a job. | Yes | No |
| `/dashboard/` | `dashboard:home` | `apps/dashboard/urls.py` | `dashboard/home.html` | Authenticated only; anonymous users redirect to login. | Yes | No |
| `/dashboard/profile/` | `dashboard:profile` | `apps/dashboard/urls.py` | `dashboard/profile.html` | Authenticated only; anonymous users redirect to login. | Yes | No |
| `/dashboard/cv/` | `dashboard:cv` | `apps/dashboard/urls.py` | `dashboard/cv_manage.html` | Authenticated only; anonymous users redirect to login. | Yes | No |
| `/dashboard/cv/status/<uuid:public_id>/` | `dashboard:cv_status` | `apps/dashboard/urls.py` | `cvs/partials/cv_status.html` | Authenticated owner only; anonymous users redirect to login. | Yes | No |
| `/dashboard/recommendations/` | `dashboard:recommendations` | `apps/dashboard/urls.py` | `dashboard/recommendations.html` | Authenticated only; anonymous users redirect to login. | Yes | No |
| `/dashboard/saved-jobs/` | `dashboard:saved_jobs` | `apps/dashboard/urls.py` | `dashboard/saved_jobs.html` | Authenticated only; anonymous users redirect to login. | Yes | No |
| `/dashboard/email-preferences/` | `dashboard:email_preferences` and `notifications:email_preferences` | `apps/dashboard/urls.py`, `apps/notifications/urls.py` | `dashboard/email_preferences.html` | Authenticated only; anonymous users redirect to login. | Yes | No |
| `/dashboard/account/` | `dashboard:account` | `apps/dashboard/urls.py` | `dashboard/account.html` | Authenticated only; anonymous users redirect to login. | Yes | No |
| `/dashboard/account/connections/` | `dashboard:connections` | `apps/dashboard/urls.py` | `dashboard/connections.html` | Authenticated only; anonymous users redirect to login. | Yes | No |
| `/dashboard/settings/delete-account/` | `dashboard:delete_account` | `apps/dashboard/urls.py` | `dashboard/delete_account.html` | Authenticated only; anonymous users redirect to login. | Yes | No |
| `/dashboard/matches/` | `matching:history` | `apps/matching/urls.py` | `matching/match_history.html` | Authenticated only; anonymous users redirect to login. | Yes | No |
| `/dashboard/matches/<uuid:public_id>/` | `matching:detail` | `apps/matching/urls.py` | `matching/match_detail.html` | Authenticated only; anonymous users redirect to login. | Yes | No |
| `/email/unsubscribe/<uuid:token>/` | `notifications:unsubscribe` | `apps/notifications/urls.py` | `notifications/unsubscribe_success.html` | Anonymous and authenticated users can unsubscribe with a valid token; invalid token returns 404. | Yes | No |
| `/accounts/login/` | `account_login` | `django-allauth account` | `account/login.html` | Anonymous users can log in; authenticated users are already logged in. | Yes | No |
| `/accounts/logout/` | `account_logout` | `django-allauth account` | `account/logout.html` | Authenticated users can log out; anonymous users can still reach the confirmation view. | Yes | No |
| `/accounts/inactive/` | `account_inactive` | `django-allauth account` | `account/account_inactive.html` | Shows inactive-account state. | Yes | No |
| `/accounts/signup/` | `account_signup` | `django-allauth account` | `account/signup.html` | Anonymous users can sign up; authenticated users are already logged in. | Yes | No |
| `/accounts/reauthenticate/` | `account_reauthenticate` | `django-allauth account` | `account/reauthenticate.html` | Authenticated users re-confirm identity for sensitive actions. | Yes | No |
| `/accounts/email/` | `account_email` | `django-allauth account` | `account/email.html` | Authenticated users manage email addresses; anonymous users redirect to login. | Yes | No |
| `/accounts/confirm-email/` | `account_email_verification_sent` | `django-allauth account` | `account/email_verification_sent.html` | Anonymous and authenticated users can view email-verification-sent state. | Yes | No |
| `/accounts/confirm-email/<key>/` | `account_confirm_email` | `django-allauth account` | `account/email_confirm.html` | Anonymous and authenticated users can confirm a valid email token. | Yes | No |
| `/accounts/password/change/` | `account_change_password` | `django-allauth account` | `account/password_change.html` | Authenticated users with usable password change it; anonymous users redirect to login. | Yes | No |
| `/accounts/password/set/` | `account_set_password` | `django-allauth account` | `account/password_set.html` | Authenticated users without usable password set one; anonymous users redirect to login. | Yes | No |
| `/accounts/password/reset/` | `account_reset_password` | `django-allauth account` | `account/password_reset.html` | Anonymous and authenticated users can request password reset. | Yes | No |
| `/accounts/password/reset/done/` | `account_reset_password_done` | `django-allauth account` | `account/password_reset_done.html` | Anonymous and authenticated users can view password-reset-sent state. | Yes | No |
| `/accounts/password/reset/key/<uidb36>-<key>/` | `account_reset_password_from_key` | `django-allauth account` | `account/password_reset_from_key.html` | Anonymous and authenticated users can set a password with a valid reset token. | Yes | No |
| `/accounts/password/reset/key/done/` | `account_reset_password_from_key_done` | `django-allauth account` | `account/password_reset_from_key_done.html` | Anonymous and authenticated users can view reset-complete state. | Yes | No |
| `/accounts/login/code/confirm/` | `account_confirm_login_code` | `django-allauth account` | `account/confirm_login_code.html` | Confirms an email login code when login-by-code is used. | Yes | No |
| `/accounts/3rdparty/` | `socialaccount_connections` | `django-allauth socialaccount` | `socialaccount/connections.html` | Authenticated users manage linked social accounts; anonymous users redirect to login. | Yes | No |
| `/accounts/3rdparty/login/cancelled/` | `socialaccount_login_cancelled` | `django-allauth socialaccount` | `socialaccount/login_cancelled.html` | Anonymous and authenticated users can view cancelled social login state. | Yes | No |
| `/accounts/3rdparty/login/error/` | `socialaccount_login_error` | `django-allauth socialaccount` | `socialaccount/authentication_error.html` | Anonymous and authenticated users can view social login error state. | Yes | No |
| `/accounts/3rdparty/signup/` | `socialaccount_signup` | `django-allauth socialaccount` | `socialaccount/signup.html` | Completes social signup when provider data requires extra fields. | Yes | No |
| `/accounts/social/login/cancelled/` | redirect | `django-allauth socialaccount compatibility route` | Redirect only | Redirects to `/accounts/3rdparty/login/cancelled/`. | N/A | No |
| `/accounts/social/login/error/` | redirect | `django-allauth socialaccount compatibility route` | Redirect only | Redirects to `/accounts/3rdparty/login/error/`. | N/A | No |
| `/accounts/social/signup/` | redirect | `django-allauth socialaccount compatibility route` | Redirect only | Redirects to `/accounts/3rdparty/signup/`. | N/A | No |
| `/accounts/social/connections/` | redirect | `django-allauth socialaccount compatibility route` | Redirect only | Redirects to `/accounts/3rdparty/`. | N/A | No |
| `/accounts/github/login/` | `github_login` | `django-allauth provider` | Provider redirect, no project HTML template | Starts GitHub OAuth flow. | N/A | No |
| `/accounts/github/login/callback/` | `github_callback` | `django-allauth provider` | Provider callback, no project HTML template | Handles GitHub OAuth callback. | N/A | No |
| `/accounts/google/login/` | `google_login` | `django-allauth provider` | Provider redirect, no project HTML template | Starts Google OAuth flow. | N/A | No |
| `/accounts/google/login/callback/` | `google_callback` | `django-allauth provider` | Provider callback, no project HTML template | Handles Google OAuth callback. | N/A | No |
| `/accounts/google/login/token/` | `google_login_by_token` | `django-allauth provider` | API/token endpoint, no project HTML template | Handles Google token login. | N/A | No |
