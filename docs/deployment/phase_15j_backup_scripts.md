# Backup Scripts

Create a cronjob for the `tunitech` user:

```bash
#!/bin/bash
# /home/tunitech/scripts/backup.sh
BACKUP_DIR="/home/tunitech/backups"
DATE=$(date +%F)

mkdir -p $BACKUP_DIR
pg_dump tunitech_db | gzip > $BACKUP_DIR/db_backup_$DATE.sql.gz
tar -czf $BACKUP_DIR/private_media_backup_$DATE.tar.gz -C /home/tunitech/tunitech-abroad private_media/

# Retain last 7 days
find $BACKUP_DIR -type f -mtime +7 -delete
```

```bash
chmod +x /home/tunitech/scripts/backup.sh
crontab -e
# Add: 0 2 * * * /home/tunitech/scripts/backup.sh
```
