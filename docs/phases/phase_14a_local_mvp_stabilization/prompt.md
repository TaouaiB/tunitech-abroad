# Autonomous Agent Prompt — Phase 14A Local MVP Stabilization

You are the implementation agent for TuniTech Abroad.

Read this file fully, then read every file in:

```text
docs/phases/phase_14a_local_mvp_stabilization/
```

Also read:

```text
AGENTS.md
docs/planning/
```

If planning docs exist as PDFs or Markdown, use them as source of truth. If both exist and conflict, prefer the current code's existing migration reality for safe repair, and report the planning/code divergence.

## Mission

Repair and stabilize the existing MVP locally so it can pass backend/template acceptance without browser testing.

The product flow to validate is:

```text
Tunisian IT profile
→ France IT jobs/internships
→ PDF CV/profile parsing
→ deterministic job matching
→ missing skill detection
→ stored recommendations
→ controlled LLM support
```

## Mandatory first step

Run the preflight in:

```text
docs/phases/phase_14a_local_mvp_stabilization/preflight.md
```

Do not edit code before understanding current state.

## Work rules

- Work only inside this stabilization scope.
- Do not start unrelated product features.
- Do not redesign the architecture.
- Do not use browser automation.
- Do not commit, merge, or push.
- Preserve user changes.
- Use the current Django models/migrations as reality; do not perform destructive schema rewrites.
- Add migrations only when necessary and safe.
- Do not print secrets.
- Do not include real user passwords in code/tests/docs/reports.

## Required repairs

Implement or repair all tasks from:

```text
docs/phases/phase_14a_local_mvp_stabilization/tasks.md
```

Key outcomes:

1. CV parsing extracts name, email, phone, location, LinkedIn, GitHub, portfolio/website, useful skills, and stores warnings/conflicts.
2. Profile prefill happens only where fields are empty; non-empty or user-confirmed profile data is not silently overwritten.
3. Profile completeness recalculates after CV parse/profile update.
4. Recommendations generate stored `JobRecommendation` rows for usable profile + active jobs.
5. Recommendation page no longer shows endless refreshing when blocked, failed, or zero-result.
6. Anonymous quick match recalculates when skills change and does not show stale result.
7. Quick match processing state resets safely for HTMX and browser back/forward cache, verified by template tests/static assertions only.
8. `/recommendations/` wrong links are removed, redirected, or safe-404 handled.
9. With `DEBUG=False`, 404/500 do not expose URLconf, traceback, settings, env values, or secrets.
10. Controlled OpenRouter LLM validation exists and can run at most 2 real calls.
11. Small France Travail ingestion validation exists and can ingest at most 10 real offers when credentials are present.
12. Public job search remains local PostgreSQL only.

## Repair loop

Use this loop, maximum 8 full loops:

```text
1. Run relevant failing test/check.
2. Inspect stack trace and current code.
3. Identify root cause.
4. Make the smallest correct architecture-compliant fix.
5. Add or update regression test.
6. Re-run the specific test.
7. Re-run related app tests.
8. Continue until clean or exact blocker.
```

Do not claim success after only editing code.

## Testing requirements

Follow:

```text
docs/phases/phase_14a_local_mvp_stabilization/test_plan.md
docs/phases/phase_14a_local_mvp_stabilization/acceptance.md
```

Full test suite must run.

`Found 0 test(s)` is failure.

## Real external validation

Follow:

```text
docs/phases/phase_14a_local_mvp_stabilization/real_validation.md
```

### OpenRouter

- Must be service-level only.
- Max 2 real calls.
- No secrets printed.
- If credentials missing/unavailable, report `BLOCKED_REAL_LLM`.

### France Travail

- Must be ingestion service/command only.
- Max 10 offers.
- No live call from user search.
- No secrets printed.
- If credentials missing/unavailable, report `BLOCKED_REAL_FRANCE_TRAVAIL`.

## Architecture guardrails

Reject and repair any of these if found:

- LLM call in Django view.
- France Travail call in `/jobs/` search path.
- Matching score decided by LLM.
- Business logic in templates.
- Celery task containing business logic instead of calling a service.
- Public URL using integer internal ID.
- CV file publicly exposed.
- `CVUpload.objects` returning soft-deleted CVs.
- `.env` committed or secret printed.
- React/Next/FastAPI/MongoDB/SQLAlchemy added.

## Specific implementation guidance

### CV extraction

Improve deterministic extraction before relying on LLM.

Handle examples:

```text
Tunis, Tunisia | +216 55 123 456 | aymen.bensalah.test@example.com | LinkedIn: linkedin.com/in/aymen-bensalah-test | GitHub: github.com/aymen-bensalah-test | Portfolio: aymen-dev.example.com
```

Normalize URLs:

```text
linkedin.com/in/x -> https://linkedin.com/in/x
github.com/x -> https://github.com/x
aymen-dev.example.com -> https://aymen-dev.example.com
```

Do not mark random phrases like `and role`, `PROJECTS`, `March 2025`, or `Added filters by location` as confirmed skills.

### Profile prefill

Allowed:

- Fill empty fields from parsed CV.
- Add ProfileSkill rows from normalized extracted skills.
- Store warnings for conflicts.

Forbidden:

- Silently overwrite an existing profile name with a CV name.
- Silently overwrite user-confirmed fields.

### Recommendations

For a synthetic user/profile/jobs smoke:

- Ensure profile completeness is usable/strong.
- Ensure active jobs exist.
- Run recommendation refresh service/task.
- Assert `JobRecommendation.objects.filter(user=user).count() > 0`.
- Assert dashboard query returns stored recommendations.

### Quick match

Must be re-runnable with changed skills.

If template JavaScript is needed, keep it tiny and local. Do not add a frontend framework.

### Safe 404

Add `templates/404.html` and `templates/500.html` if missing.

Test with `override_settings(DEBUG=False)`.

## Final report

Write final report using:

```text
docs/phases/phase_14a_local_mvp_stabilization/agent_report_template.md
```

Save it as:

```text
docs/phases/phase_14a_local_mvp_stabilization/agent_report.md
```

The report must include:

- Exact commands run.
- Test output summary.
- External validation result.
- Files changed.
- Remaining blockers.
- Whether final classification is PASS/FAIL/BLOCKED.

Do not mark `PASS` unless local acceptance, real LLM validation, and real France Travail validation all pass.
