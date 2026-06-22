# Restore Test Procedure

To verify backups:

```bash
# 1. Drop existing dev DB
dropdb tunitech_db_dev

# 2. Create blank DB
createdb tunitech_db_dev

# 3. Unzip and restore SQL dump
gunzip < db_backup_YYYY-MM-DD.sql.gz | psql tunitech_db_dev

# 4. Extract media
tar -xzf private_media_backup_YYYY-MM-DD.tar.gz -C /tmp/restore_test/
```
