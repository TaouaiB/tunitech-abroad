# Phase 16I-C: Auth Email UX & Ingestion Daily Cap Report

## Job Ingestion Updates
- **Ingestion schedule 6h/4 runs per day**: Yes.
- **Per-run cap persistent source-of-truth is 250**: Yes. Handled in `apps/jobs/models.py` defaults (`max_jobs_per_run=250`, `max_total_per_run=250`, `frequency_minutes=360`), and updated in `apps/jobs/management/commands/sync_france_travail_it_jobs.py` seeding config.
- **Production Database Update Command**: To update existing configurations in production manually without generating new migrations, run the following via `python manage.py shell`:
```python
from apps.jobs.models import JobIngestionConfig
JobIngestionConfig.objects.update(max_jobs_per_run=250, max_total_per_run=250, frequency_minutes=360)
```
- **Expected daily total**: 4 runs/day × 250 = 1000 fetched jobs.

## Email Template Updates
- **Account already exists email HTML template added**: Yes (`templates/account/email/account_already_exists_message.html` added based on the TuniAtlas branded template shell).
- **Old TuniTech Abroad email prefix removed**: Yes. Added `ACCOUNT_EMAIL_SUBJECT_PREFIX = "[TuniAtlas] "` in base settings and removed the hardcoded ` - TuniAtlas` suffix from `account_already_exists_subject.txt`.
- **/accounts/email/ page themed**: Yes. We rewrote `templates/account/email.html` to remove the default allauth styling and inject TuniAtlas CSS variables natively (card grids, button variants, labels translated to "Adresse email" and "Adresses email").

## Auth Verification Settings
- **ACCOUNT_EMAIL_VERIFICATION optional**: Yes (`ACCOUNT_EMAIL_VERIFICATION = "optional"` in `config/settings/base.py`).
- **Confirmation email still sent**: Yes (allauth's `optional` mode automatically continues sending verification emails).
- **Unverified users can access account**: Yes (users are no longer blocked after signup and can access the dashboard immediately).
- **Google/GitHub buttons use inline SVG icons**: Yes. We verified and patched `templates/socialaccount/snippets/provider_list.html` to use inline SVGs perfectly matching login/signup.

## Tests/Checks Output
- **Full tests actually passed**: Exactly 662 tests passed successfully (0 failures).
- **No test DB locked note**: DB state clean.

## Files Changed
- `config/settings/base.py` (updated schedule, email verification, email prefix)
- `templates/account/email/account_already_exists_subject.txt`
- `templates/account/email/account_already_exists_message.html`
- `templates/account/email.html` (themed to match TuniAtlas style)
- `templates/socialaccount/snippets/provider_list.html` (added inline SVGs for Google/GitHub)
- `apps/jobs/models.py` (persistent defaults for JobIngestionConfig)
- `apps/jobs/management/commands/sync_france_travail_it_jobs.py` (seed command defaults updated)

## Remaining Blockers
- None.
