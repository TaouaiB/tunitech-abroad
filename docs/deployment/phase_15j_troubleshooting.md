# Troubleshooting

## Check Logs

```bash
# Gunicorn
sudo journalctl -u gunicorn -f

# Celery Worker
sudo journalctl -u celery -f
# Or check log files
tail -f /home/tunitech/tunitech-abroad/celery-1.log

# Caddy
sudo journalctl -u caddy -f

# PostgreSQL
sudo systemctl status postgresql
sudo journalctl -u postgresql -f
sudo -u postgres psql -c "\l tunitech_db"          # confirm DB exists
sudo -u postgres psql -d tunitech_db -c "\dt"       # list tables

# Redis
sudo systemctl status redis
sudo journalctl -u redis -f
redis-cli ping                                       # expect PONG
redis-cli -h 127.0.0.1 -p 6379 ping
```

## Common Issues
- **502 Bad Gateway**: Check if Gunicorn socket exists and has correct permissions, or if Gunicorn service crashed.
- **Missing Static Files**: Did you run `collectstatic`?
