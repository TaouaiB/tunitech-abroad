# Backup & Restore Policy

Data preservation is critical. The following policy outlines the backup and restore procedures for the production database and user uploads.

## Backup Policy

1. **Daily PostgreSQL Dump**: A full logical backup (`pg_dump`) of the PostgreSQL database will run daily via cron.
2. **Daily Private Media Archive**: A compressed archive (`tar.gz`) of the `PRIVATE_MEDIA_ROOT` will run daily.
3. **Encrypted Storage**: Backups must be encrypted (e.g., using `gpg` or a secure transfer protocol to an isolated bucket/server).
4. **Retention Window**:
   - Keep 7 daily backups.
   - Keep 4 weekly backups.
5. **Logs**: Backup scripts must log success/failure to a monitored file (e.g., `/var/log/tunitech_backup.log`).

## Restore Policy & Testing

Before public launch, a full restore test must be conducted on a staging or local environment to verify backup integrity.

### Restore Steps (Outline)
1. Stop Gunicorn and Celery workers to prevent data mutation.
2. Drop and recreate the target database.
3. Restore from the `.sql` dump.
4. Extract the private media archive into the proper directory.
5. Apply any pending migrations if restoring to a newer codebase.
6. Restart services and verify functionality.

## Rollback Notes
If a deployment corrupts data, restore from the immediate prior backup following the steps above. Document the rollback event and notify affected users if data loss occurred within the rollback window.
