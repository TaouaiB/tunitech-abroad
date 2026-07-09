# TuniAtlas V16 Page Mapping

This file maps final v16 prototype pages to likely Django templates/components.

Adjust paths only if the real project structure differs.

## Public / jobs

| V16 prototype file | Django target |
|---|---|
| `index.html` | `templates/jobs/index.html` or public jobs listing template |
| `job-detail.html` | `templates/jobs/detail.html` |
| `about.html` | `templates/public/about.html` |

## Auth

| V16 prototype file | Django target |
|---|---|
| `auth.html` | `templates/account/login.html`, `templates/account/signup.html`, or split into existing auth templates |

Important:

- OAuth signup/profile flow must keep create-password step first.
- Do not show extra text like `or email`.
- Do not show helper text like `OAuth account.`.

## Dashboard

| V16 prototype file | Django target |
|---|---|
| `recommendations.html` | `templates/dashboard/recommendations.html` |
| `saved-jobs.html` | `templates/dashboard/saved_jobs.html` |
| `notifications.html` | `templates/dashboard/notifications.html` |
| `settings.html` | `templates/dashboard/settings.html`, account/security/email preferences templates, or existing equivalents |

## Profile / CV

| V16 prototype file | Django target |
|---|---|
| `profile-setup.html` | `templates/dashboard/profile.html`, `templates/dashboard/cv.html`, or onboarding/profile-step templates |

Important mobile behavior:

- compact stepper
- only one action row on mobile
- sticky bottom action bar
- no duplicate buttons
- no extra helper text

## Match / scoring

| V16 prototype file | Django target |
|---|---|
| `match-score.html` | `templates/matches/detail.html` or dashboard match detail template |

Important:

- preserve score layout
- preserve collapsible mobile sections
- preserve sticky mobile action bar
- do not change scoring logic

## State pages/components

| V16 prototype file | Django target |
|---|---|
| `empty-states.html` | shared components or state-specific templates |
| `loading-states.html` | shared loading/HTMX components |
| `failure-states.html` | shared error/retry components |
| `404.html` | `templates/404.html` |
| `500.html` | `templates/500.html` |

## Shared components

Suggested components:

```text
templates/components/header.html
templates/components/footer.html
templates/components/mobile_nav.html
templates/components/job_card.html
templates/components/skill_chip.html
templates/components/toast.html
templates/components/mobile_filter_drawer.html
templates/components/ai_progress.html
templates/components/empty_state.html
templates/components/loading_state.html
templates/components/failure_state.html
```
