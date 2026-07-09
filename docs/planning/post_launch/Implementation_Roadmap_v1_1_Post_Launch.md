# Implementation Roadmap v1.1 — Post-Launch Hardening

Status: Post-launch roadmap  
Product: TuniAtlas Jobs  
Purpose: Define ordered phases after initial deployment

## 1. Purpose

This roadmap defines what to do after the website has been deployed and used for several days.

It does not replace the original v1 roadmap. It continues after deployment and corrects production-discovered issues.

## 2. Execution rules

```text
One phase at a time.
Agent may complete all tickets inside the current phase.
Agent must not start next phase without explicit approval.
No stack changes.
No SPA rewrite.
No live external API calls during user search.
No LLM scoring authority.
No public CV exposure.
No real secrets in prompts/reports/logs.
No real CV test corpus committed.
```

## 3. Updated phase order

```text
16A — Production Stabilization
16B — Job Ingestion, Freshness, Search, and Country-Neutral UI Hardening
16C — CV Parser Quality Framework
16D — Skill Taxonomy and Alias Accuracy
16E — Job Skill Extraction and Data Quality
16F — Matching and Recommendation Accuracy
16G — Admin Monitoring and Alerts
16H — UI/UX Decision System
16I — Email Professionalization
16J — Future ML/LLM Platform
```

## 4. Phase 16A — Production Stabilization

### Goal

Fix production trust issues before product expansion.

### Scope

```text
HTTPS awareness behind Caddy
Google OAuth duplicate verified-email linking
robots.txt
sitemap.xml
unsafe job description rendering
PDF magic-byte validation
match formula correction
LLM disabled result cleanup
homepage real latest jobs
```

### Tickets

#### TTA-16A-001 — Production HTTPS awareness

Add to production settings through Git:

```python
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https"
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

Acceptance:

```text
Django recognizes HTTPS behind Caddy.
OAuth builds HTTPS callback URLs.
Secure cookies enabled.
No manual server drift.
```

#### TTA-16A-002 — Google OAuth verified-email linking

Acceptance:

```text
Existing verified email/password account can safely connect Google login.
No duplicate user is created.
Unverified collision does not silently link.
User sees clear message if linking unsafe.
Tests cover verified and unverified email collision.
```

#### TTA-16A-003 — robots.txt and sitemap.xml

Acceptance:

```text
/robots.txt returns 200.
/sitemap.xml returns 200.
No private/dashboard/admin URLs exposed in sitemap.
```

#### TTA-16A-004 — Remove unsafe job description rendering

Replace unsafe `|safe` rendering for external job descriptions.

Acceptance:

```text
External job descriptions do not render arbitrary HTML.
Line breaks are preserved safely.
XSS test passes.
```

#### TTA-16A-005 — PDF magic-byte validation

Acceptance:

```text
Fake .pdf with wrong header rejected.
Wrong content type rejected.
Oversized files rejected.
Valid PDF accepted.
File pointer reset after validation.
```

#### TTA-16A-006 — Match formula correction

Formula:

```text
technical 45%
experience 20%
role/title 15%
language 10%
location 10%
```

Acceptance:

```text
Location score affects final fit score.
Tests assert formula exactly.
```

#### TTA-16A-007 — LLM disabled result cleanup

Acceptance:

```text
LLM disabled mode returns disabled result.
No fake success.
No fake extraction contaminates production data.
```

#### TTA-16A-008 — Homepage real latest jobs

Acceptance:

```text
Homepage shows real latest public jobs or honest empty state.
No stale static "coming soon" job block.
```

### Commands

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test --settings=config.settings.local
```

Production smoke:

```bash
curl -I https://www.tuniatlas.com/accounts/login/
curl -I https://tuniatlas.com/accounts/login/
curl -I https://tuniatlas.com/robots.txt
curl -I https://tuniatlas.com/sitemap.xml
```

## 5. Phase 16B — Job Ingestion, Freshness, Search, and Country-Neutral UI Hardening

### Goal

Fix job supply visibility, make ingestion configurable, harden freshness and search, and remove France-only public copy.

### Scope

```text
diagnose why automatic ingestion shows around 100–200 jobs instead of manual 1k
configurable target_daily_fetch_count from admin
query-level ingestion audit
freshness/expiry hardening
company filter
published exact/from/to filters
empty/space search behavior
skill alias search behavior
country-neutral public copy
```

### Tickets

#### TTA-16B-001 — Diagnose job count discrepancy

Add command:

```bash
python manage.py diagnose_job_ingestion --settings=config.settings.production
```

Acceptance:

```text
Output explains fetched -> raw -> normalized -> active -> public visible -> matchable.
Latest run counts visible.
Per-query counts visible.
Eligibility/freshness reasons visible.
No guessing about 200 versus 1000.
```

#### TTA-16B-002 — Configurable ingestion limits

Admin can set:

```text
target_daily_fetch_count
max_jobs_per_run
max_pages_per_query
page_size
queries_json
stale_after_hours
removed_after_hours
expire_grace_hours
```

Acceptance:

```text
Default target_daily_fetch_count is 1000.
Admin can update config.
Config affects scheduled ingestion.
System reports when source returns fewer than target.
```

#### TTA-16B-003 — Query-level ingestion run tracking

Acceptance:

```text
Each configured query has fetched/created/updated/unchanged/error counts.
Admin can see which query underperforms.
```

#### TTA-16B-004 — Freshness/expiry hardening

Correct ordering:

```python
if expires_at and expires_at < now - expire_grace:
    status = "expired"
elif last_seen_at and last_seen_at < now - removed_after:
    status = "removed"
elif last_seen_at and last_seen_at < now - stale_after:
    status = "stale"
else:
    status = "active"
```

Acceptance:

```text
Failed ingestion run does not mass-stale jobs.
Failed ingestion run does not mass-remove jobs.
Removed check wins over stale check.
Date-only expiry uses end of day plus grace.
Tests cover edge cases.
```

#### TTA-16B-005 — Search hardening

Acceptance:

```text
/jobs/?q=%20%20%20 returns active jobs.
Empty q returns active jobs.
Invalid filters do not crash.
Anonymous best-match fallback works.
Pagination edge cases covered.
```

#### TTA-16B-006 — Company and published date filters

Add filters:

```text
company
published_exact
published_from
published_to
```

Acceptance:

```text
Company filter matches company_name.
Exact published date works.
Published date range works.
Invalid date safe.
Filters preserve pagination.
```

#### TTA-16B-007 — Search logs and audit

Add command:

```bash
python manage.py audit_job_search --settings=config.settings.production
```

Acceptance:

```text
Admin can see top searches, zero-result searches, whitespace searches, invalid filters.
Search logging failure does not break search.
```

#### TTA-16B-008 — Country-neutral public UI

Acceptance:

```text
Public marketing/product UI no longer says France-only or France-first.
Job location can still show France as data.
Admin/internal/source config can still say France Travail/France.
No public country dropdown yet.
```

Add command:

```bash
python manage.py audit_public_copy --settings=config.settings.local
```

### Commands

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test --settings=config.settings.local
python manage.py audit_public_copy --settings=config.settings.local
```

Production diagnostics:

```bash
python manage.py diagnose_job_ingestion --settings=config.settings.production
python manage.py audit_job_search --settings=config.settings.production
```

## 6. Phase 16C — CV Parser Quality Framework

### Goal

Make CV parser quality measurable and prevent embarrassing wrong extraction.

### Scope

```text
CVNameExtractionService
name candidate scoring/rejection
confidence outputs
private 100+ CV corpus structure
expected JSON format
audit_cv_parser command
parser metrics
regression tests
correction capture foundation
```

### Tickets

#### TTA-16C-001 — Name extractor rewrite

Acceptance:

```text
"je me suis" is rejected.
Sentence-like text rejected.
Section headers rejected.
Job titles rejected.
Low-confidence returns None.
Unit tests cover French/English bad cases.
```

#### TTA-16C-002 — Parser confidence and warnings

Acceptance:

```text
CVParsedData includes confidence_json and warnings_json.
Low-confidence fields do not overwrite confirmed profile data.
```

#### TTA-16C-003 — Private CV audit corpus

Acceptance:

```text
private_test_corpus/ structure documented.
.gitignore protects it.
Example expected JSON included without real personal data.
```

#### TTA-16C-004 — audit_cv_parser command

Acceptance:

```text
Command parses local corpus.
Compares expected versus actual.
Outputs CSV/JSON report.
Exits non-zero below threshold.
```

#### TTA-16C-005 — Parser metrics

Acceptance:

```text
name/email/phone/link/skill precision-recall metrics generated.
False skill rate tracked.
```

#### TTA-16C-006 — Regression loop tests

Acceptance:

```text
Each parser bug fix adds unit/regression test.
Full corpus score does not regress.
```

## 7. Phase 16D — Skill Taxonomy and Alias Accuracy

### Goal

Make skill matching canonical and alias-aware.

### Scope

```text
ProfileSkill canonical Skill FK if not already correct
alias expansion
.NET / ASP.NET Core / C# / Node.js / PostgreSQL handling
audit_skill_aliases command
unmatched skill review improvements
matching by skill_id
```

### Tickets

#### TTA-16D-001 — Canonical ProfileSkill

Acceptance:

```text
ProfileSkill has skill FK.
Existing profile skills backfilled.
Matching uses skill IDs.
No duplicate profile skills.
```

#### TTA-16D-002 — Alias expansion

Acceptance examples:

```text
.NET Core maps intentionally.
dotnet maps intentionally.
Node.js/node js maps to Node.js.
Postgres maps to PostgreSQL.
ReactJS maps to React.
csharp/C sharp maps to C#.
C++ remains C++.
CI/CD remains CI/CD.
```

#### TTA-16D-003 — audit_skill_aliases command

Acceptance:

```text
Duplicate aliases reported.
Ambiguous aliases reported.
Top unmatched candidates shown.
```

#### TTA-16D-004 — Skill feedback labels

Acceptance:

```text
Admin/user corrections can be recorded.
Feedback usable for future ML labels.
```

## 8. Phase 16E — Job Skill Extraction and Data Quality

### Goal

Improve job skill extraction, required/optional classification, search vector quality, and job visibility diagnostics.

### Scope

```text
required/optional/detected classifier
zero-skill job detection
generic-skill-only detection
rematerialize_job_skills
rebuild_job_search_vectors
inspect_public_job_eligibility
ingestion count diagnostics integration
```

### Required commands

```bash
python manage.py rematerialize_job_skills --settings=config.settings.production
python manage.py rebuild_job_search_vectors --settings=config.settings.production
python manage.py inspect_public_job_eligibility --settings=config.settings.production
```

Acceptance:

```text
Search vector includes canonical required/optional skill names.
Admin can see zero-skill jobs.
Admin can see public eligibility buckets.
Commands are idempotent.
```

## 9. Phase 16F — Matching and Recommendation Accuracy

### Goal

Make matching and recommendations explainable and useful without LLM.

### Scope

```text
exact skill scoring
related skill scoring if needed
low-confidence job skill behavior
recommendation reason storage
missing skill roadmap
match result explanation cleanup
feedback hooks
```

Acceptance:

```text
Score breakdown matches formula.
Missing required skills visible.
Low-confidence job skill warning visible.
Recommendation card explains why.
LLM cannot alter score.
```

## 10. Phase 16G — Admin Monitoring and Alerts

### Goal

Give solo owner/operator enough visibility to run the product.

### Scope

```text
owner-only admin operations dashboard
data quality dashboard
search quality dashboard
CV parser dashboard
ingestion diagnostics dashboard
protected admin CV download
AdminFileAccessLog
AdminAlertService
AdminOpsDigestService
```

Acceptance:

```text
Admin can see operational health.
Admin can download CV through protected logged action.
No public CV URL.
Admin alerts sent to env-configured ADMIN_ALERT_EMAIL.
No fake enterprise roles.
```

## 11. Phase 16H — UI/UX Decision System

### Goal

Redesign UI around decision clarity, not decoration.

### Scope order

```text
homepage
job search
job detail
quick match
dashboard
recommendations
match result
CV upload/profile confirmation
```

Acceptance:

```text
User understands value in under 10 seconds.
Job cards show useful signals.
Match result explains next action.
Country-neutral public copy preserved.
No SPA rewrite.
```

## 12. Phase 16I — Email Professionalization

### Goal

Make user/admin emails professional and aligned with product quality.

### Scope

```text
verification email
password reset email
admin alert emails
optional CV parsed email
weekly digest only after recommendation quality is acceptable
plain text fallback
unsubscribe/preferences footer
```

Acceptance:

```text
No hardcoded secrets/emails.
Templates use TuniAtlas branding.
Digest respects opt-in and verified email.
Admin alerts do not include sensitive personal data.
```

## 13. Phase 16J — Future ML/LLM Platform

### Goal

Prepare optional ML/LLM layer without changing deterministic scoring authority.

### Scope

```text
PromptVersion
LLMCacheEntry
LLMUsageLog
label export commands
training dataset export
optional model experiment folder
LLM extraction behind feature flags
LLM disabled result cleanup if not done earlier
```

Acceptance:

```text
LLM cannot change score.
Future ML predicts canonical Skill IDs + confidence.
Correction/feedback labels exportable.
No production ML shipped without evaluated dataset.
```

## 14. Files to create per implementation phase

For each phase, create:

```text
docs/phases/phase_16x_<name>/tasks.md
docs/phases/phase_16x_<name>/prompt.md
docs/phases/phase_16x_<name>/acceptance.md
docs/phases/phase_16x_<name>/agent_report_template.md
```

Do not make the implementation agent read all v1.1 documents blindly every time. Give it the specific phase files and relevant planning docs.
