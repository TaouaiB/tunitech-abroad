# Codex Verification Prompt — Phase 14F

Read and verify Phase 14F implementation exactly.

You may fix Phase 14F issues only.
Do not commit.
Do not deploy.
Do not start Phase 14G.
Do not rewrite unrelated phases.
Do not remove unrelated dirty worktree changes.

Verify:

1. New broad IT command exists: `sync_france_travail_it_jobs`.
2. Default `limit_per_keyword=50`.
3. Default `max_total_per_run=1000`.
4. Nightly default max total `2000`.
5. No hidden cap of 10 in the new broad command.
6. Broad IT preset covers developer, data, DevOps/cloud, cyber, QA, support, systems, DBA, ERP/CRM, project/product, internship/apprenticeship.
7. Pagination and deduplication are implemented.
8. Raw records are saved/updated.
9. Normalization runs when enabled.
10. Enrichment is queued for every fetched active eligible IT job by default.
11. Enrichment respects existing Phase 14D feature flags/hash/skipping.
12. Stale/expired jobs are marked inactive and excluded from public search/recommendations.
13. Admin config and run logs exist.
14. No France Travail live API calls happen in user views/search/recommendations.
15. No LLM calls happen in views.
16. Tests prove the key cases.

Run:

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test apps.jobs apps.llm apps.matching apps.recommendations --settings=config.settings.local
python manage.py test --settings=config.settings.local
git diff --check
```

Run boundary greps from `regression_security_checks.md`.

If code/tests pass, final verdict is:

```text
BLOCKED_HUMAN_VISUAL_SIGNOFF
```

If not, final verdict is:

```text
FAIL
```

Never write PASS.
