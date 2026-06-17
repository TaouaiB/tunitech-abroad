# Acceptance Criteria

Phase 14H-D is acceptable when:

- All automated checks pass.
- Tailwind CSS build passes.
- collectstatic dry-run passes.
- Full test suite passes.
- No missing migrations.
- Browser smoke test is completed or clearly marked as human-blocked.
- CV upload/parse status works with Celery worker running.
- Public job search reads local PostgreSQL and does not call France Travail live.
- Matching and recommendations flows work for a test user.
- Save/unsave jobs works.
- Account/privacy flows are checked with a disposable user.
- No public CV file URLs or raw CV text appear in templates.
- No internal integer IDs are introduced in public URLs.
- No secrets are printed or committed.
- `docs/validation/local_mvp_e2e_report.md` is created/updated.

## Final verdict

Use:

```text
FINAL_VERDICT: BLOCKED_HUMAN_VISUAL_SIGNOFF
```

if checks pass but manual visual/real browser confirmation remains.

Use:

```text
FINAL_VERDICT: FAIL
```

if a blocker remains.
