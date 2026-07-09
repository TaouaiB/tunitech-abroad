# Rollback Plan — Phase 16A — Production Stabilization

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
