# Rollback Plan — Phase 16B — Job Ingestion, Freshness, Search, and Country-Neutral UI Hardening

## Before deployment

```text
Review migrations.
Backup production database if schema/data migrations are involved.
Confirm no secrets in git diff.
Confirm feature flags/defaults are safe.
```

## If deployment fails

```bash
sudo systemctl status tuniatlas.service --no-pager
sudo journalctl -u tuniatlas.service --since "30 minutes ago" --no-pager | tail -200
```

Rollback through Git deployment process. Do not edit production Python manually except emergency containment.

## Data rollback

If a migration is irreversible or destructive, stop and require manual senior review before deployment.

## 16B-specific freshness/search rollback guard

Before deployment, capture:

```bash
python manage.py diagnose_job_ingestion --settings=config.settings.production > /tmp/diagnose_before_16b.txt
python manage.py shell --settings=config.settings.production <<'PY'
from collections import Counter
from apps.jobs.models import NormalizedJob
print('total', NormalizedJob.objects.count())
print(Counter(NormalizedJob.objects.values_list('status', flat=True)))
PY
```

After deployment and after the next ingestion/freshness run, capture the same output.

Rollback or stop if:

```text
active jobs drop unexpectedly by a large percentage
public visible jobs becomes zero or near-zero
removed/expired spikes without source explanation
scheduled ingestion starts failing completely
search with empty query no longer returns active jobs
```

Until Phase 16G alerting exists, this manual before/after check is mandatory for 16B.
