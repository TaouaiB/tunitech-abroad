# Manual Test Plan (TTA-1312)

Use this checklist to verify critical manual flows on the deployed application.

## 1. System Health
- [ ] Visit `/health/` and verify a `200 OK` response with `status: ok` for both database and redis.

## 2. Public Pages
- [ ] **Landing Page (`/`)**: Renders correctly, styling is responsive on mobile and desktop.
- [ ] **Privacy Policy (`/privacy/`)**: Renders correctly.
- [ ] **Terms of Service (`/terms/`)**: Renders correctly.

## 3. Authentication
- [ ] **Signup**: Can register a new account via email. Receives confirmation email (if enabled).
- [ ] **Login**: Can log in with email and password.
- [ ] **OAuth**: Google/GitHub login buttons are visible and functional (subject to proper credentials).
- [ ] **Logout**: Can log out and is redirected to the home page.

## 4. Job Search Flow
- [ ] **Job Search (`/jobs/`)**: Jobs list is displayed from PostgreSQL.
- [ ] **Pagination/Filters**: Can navigate between pages and filter jobs.
- [ ] **Job Detail (`/jobs/<public_id>/`)**: Can view job details using public UUID. Internal integer IDs are not visible in the URL.

## 5. Dashboard & CV
- [ ] **CV Upload (`/dashboard/cv/`)**: Can upload a PDF.
- [ ] **Privacy Check**: Uploaded CV cannot be accessed via a direct public media link.
- [ ] **Profile (`/dashboard/profile/`)**: Can view and update profile information.
- [ ] **Saved Jobs (`/dashboard/saved-jobs/`)**: Can save a job from the list/detail page and view it here. Can unsave it.

## 6. Matching & Recommendations
- [ ] **Quick Match (`/jobs/<public_id>/quick-match/`)**: Can run a quick match evaluation on a job.
- [ ] **Match History (`/dashboard/matches/`)**: Can view past match scores.
- [ ] **Recommendations (`/dashboard/recommendations/`)**: Relevant job recommendations appear based on profile.

## 7. Account Management
- [ ] **Email Preferences (`/dashboard/email-preferences/`)**: Can toggle preferences and save.
- [ ] **Delete Account (`/dashboard/settings/delete-account/`)**: Typing `DELETE` successfully queues the account for deletion.
- [ ] **Admin Login (`/admin/`)**: Non-staff users are redirected to login. Staff users can access the Django admin panel.
