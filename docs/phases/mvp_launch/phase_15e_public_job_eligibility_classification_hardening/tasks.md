# Phase 15E Tasks — Public Job Eligibility + Classification Hardening

## Task 0 — Inspect current implementation

Inspect:
- job classification/signals service
- ingestion normalization path
- public job list/detail views
- recommendation querysets
- saved jobs / match views
- job presentation service and badge helpers
- tests for public jobs/search/matching

Find:
- where `skill_signal_quality` is set
- where `classification_json` is set
- where public `/jobs/` queryset is built
- where job detail fetches by `public_id`
- where quick/detailed match allows running

## Task 1 — Add central eligibility service

Create a service such as:

```python
apps/jobs/services/eligibility.py

class JobEligibilityService:
    classify_public_state(job) -> PublicJobState
    is_publicly_visible(job) -> bool
    is_matchable(job) -> bool
    reason(job) -> str
```

Allowed states:
- `public_matchable`
- `public_limited_pending_analysis`
- `admin_review_only`
- `excluded`

Do not add DB migration unless necessary. A service-level computed state is enough for this phase.

## Task 2 — Harden classification rules

Repair the classifier/signals logic so strong IT positives override generic negative terms.

Must protect:
- Data Engineer GCP
- Data Engineer / Expert Data Intégration
- Tech Lead / DevOps
- Développeur .NET / C# Fullstack
- Développeur fullstack Java/Angular
- Consultant Cybersécurité Sénior with audit/risk/security delivery
- Ingénieur en Optimisation R&D when software/algorithm/R&D tooling evidence exists

Must exclude:
- Chargé d'affaires / commercial agencement bois
- SDR/BDR Business Developer Cybersécurité
- Animateur réseau / développeur réseau de franchise
- Médiateur scientifique cybersécurité
- generic Wavestone transformation digitale business/industry consulting without hands-on technical role

## Task 3 — Reclassify existing active jobs command

Add command:

```bash
python manage.py reclassify_jobs --active-only --dry-run --limit 500 --settings=config.settings.local
python manage.py reclassify_jobs --active-only --apply --limit 500 --settings=config.settings.local
```

It should:
- recompute classification/signal for existing jobs
- show before/after counts
- list examples changed from excluded -> IT
- list examples changed from visible -> excluded/admin_review
- not call external APIs
- be idempotent

## Task 4 — Apply public eligibility to public surfaces

Use `JobEligibilityService` in:
- public jobs list
- public job detail
- recommendations
- quick match / detailed match entrypoints
- saved jobs display if a saved job later becomes excluded

Rules:
- excluded/admin_review_only should not appear in public list
- direct public detail for excluded/admin_review_only should 404 for non-admin users
- match actions should be blocked for non-matchable jobs
- user job search still reads local PostgreSQL only

## Task 5 — Fix wording and CTAs

Use `Compétences en cours d'analyse` only for truly pending analysis.

Hide/disable detailed analysis CTA when:
- job has zero materialized skills
- job is excluded/admin_review_only
- job is public_limited_pending_analysis
- job is not matchable

Do not show fake technical confidence for non-matchable jobs.

## Task 6 — Deduplicate badges

Centralize badge deduplication after placeholder filtering.

Example:
`CDD`, `Internship`, `Internship`
must render as:
`CDD`, `Internship`

Keep valid distinct badges.

## Task 7 — Admin visibility

Admin must still be able to see:
- excluded jobs
- admin_review_only jobs
- classification reasons
- public eligibility state/reason if easy

Do not delete rows.

## Task 8 — Tests

Required tests:
- Data Engineer GCP is not excluded and is publicly visible/matchable when skills exist
- Tech Lead / DevOps is not excluded and is publicly visible/matchable when skills exist
- Fullstack Java/Angular is not excluded and is publicly visible/matchable when skills exist
- Business Developer Cybersécurité is excluded/not public/not matchable
- franchise `réseau` job is excluded/not public/not matchable
- Médiateur scientifique cyber is excluded/not public/not matchable
- Wavestone generic transformation business role is excluded/not public/not matchable
- `réseau informatique` remains IT, `réseau de franchise` is non-IT
- `cybersécurité` engineer/consultant remains IT, SDR/mediator cyber is non-IT
- public job list excludes excluded/admin_review_only
- direct detail for excluded job returns 404 for normal users
- match action blocked for non-matchable job
- duplicate badges are removed
- `Compétences en cours d'analyse` appears only for true pending analysis

## Task 9 — Verification commands

Run:

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test --settings=config.settings.local --parallel 1
npm run css:build
python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
git diff --check
```

Run data checks:

```bash
python manage.py reclassify_jobs --active-only --dry-run --limit 500 --settings=config.settings.local
python manage.py reclassify_jobs --active-only --apply --limit 500 --settings=config.settings.local
python manage.py reclassify_jobs --active-only --apply --limit 500 --settings=config.settings.local
```

Report:
- active excluded_non_it count before/after
- public visible count before/after
- public matchable count
- admin_review_only count
- zero-skill public visible count
- examples hidden
- examples corrected from excluded to IT

## Task 10 — Safety greps

Run:

```bash
grep -R "OpenRouterClient\|OPENROUTER\|client.chat\|_make_request" apps/*/views.py apps/*/admin.py templates -n 2>/dev/null || true
grep -R "FranceTravailClient\|search_offers\|api.francetravail" apps/*/views.py templates -n 2>/dev/null || true
grep -R "file.url\|cv.file.url\|upload.file.url\|raw_text\|raw_request_json\|raw_response_text\|raw_response_json" templates apps -n 2>/dev/null || true
grep -R "<int:" apps templates config -n 2>/dev/null || true
git diff -- . ':!.env' ':!.env.*' | grep -iE "sk-or-|Bearer [A-Za-z0-9_.-]{20,}|OPENROUTER_API_KEY=.*[^=]|FRANCE_TRAVAIL_CLIENT_SECRET=.*[^=]|EMAIL_HOST_PASSWORD=.*[^=]" || echo "OK: no obvious secrets in diff"
```

## Deliverables

Create:
- code/tests/commands
- `docs/phases/phase_15e_public_job_eligibility_classification_hardening/agent_report.md`

Do not commit.
