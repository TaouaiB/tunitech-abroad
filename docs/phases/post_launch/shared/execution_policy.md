# Shared Execution Policy

## Gemini role

Gemini is the implementation agent. It may inspect the repo, plan inside the current phase, implement all tickets inside the current phase, run checks, fix in-scope failures, and report.

Gemini must not:

```text
start the next phase
change the stack
hide failing tests
commit secrets
invent product scope
build future UI redesign before 16H
build ML/DL before 16J and explicit approval
```

## Codex role

Codex is the verification and repair agent after Gemini. It must inspect Gemini's output, verify architecture, run tests, fix in-scope defects, and report residual risks.

Codex must be stricter than Gemini. It should check:

```text
service-layer boundaries
view thinness
Celery task thinness
models not calling external APIs
public_id usage
CV privacy
secret exposure
migrations
tests
phase boundary
overbuilding
production safety
```

## Browser/manual testing role

Browser tests are manual or Playwright-style only if the repo already supports them. Do not introduce a heavy browser framework unless explicitly approved. Use Django test client for most backend coverage.

## Gemini/Codex disagreement rule

Read `shared/gemini_codex_tiebreak_policy.md`.

Codex may fix in-scope defects automatically only when the fix preserves ticket intent. If Codex changes ticket intent, defers a ticket, replaces the requested behavior, or believes the ticket violates architecture/security/privacy, Codex must flag it explicitly in `Intent-changing fixes or disagreements` and stop for senior review.

## Diagnostics output rule

Read `shared/diagnostics_contract_policy.md`.

All diagnostics/audit services added in post-launch phases must return stable structured dicts with counts, status buckets, reason buckets, warnings, errors, and recommended actions where applicable. This is required so Phase 16G can build unified admin dashboards instead of re-implementing every diagnostic shape.
