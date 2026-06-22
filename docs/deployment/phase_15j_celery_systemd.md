# Celery Systemd Services

## Worker

Create `/etc/systemd/system/celery.service`:

```ini
[Unit]
Description=Celery Service
After=network.target redis-server.service

[Service]
Type=forking
User=tunitech
Group=tunitech
EnvironmentFile=/home/tunitech/tunitech-abroad/.env
WorkingDirectory=/home/tunitech/tunitech-abroad
ExecStart=/bin/sh -c '/home/tunitech/tunitech-abroad/.venv/bin/celery multi start worker1 -A config.celery_app --pidfile=/home/tunitech/tunitech-abroad/celery-%%n.pid --logfile=/home/tunitech/tunitech-abroad/celery-%%n.log'
ExecStop=/bin/sh -c '/home/tunitech/tunitech-abroad/.venv/bin/celery multi stopwait worker1 --pidfile=/home/tunitech/tunitech-abroad/celery-%%n.pid'
ExecReload=/bin/sh -c '/home/tunitech/tunitech-abroad/.venv/bin/celery multi restart worker1 -A config.celery_app --pidfile=/home/tunitech/tunitech-abroad/celery-%%n.pid --logfile=/home/tunitech/tunitech-abroad/celery-%%n.log'

[Install]
WantedBy=multi-user.target
```

## Beat

Create `/etc/systemd/system/celerybeat.service`:

```ini
[Unit]
Description=Celery Beat Service
After=network.target celery.service

[Service]
Type=simple
User=tunitech
Group=tunitech
EnvironmentFile=/home/tunitech/tunitech-abroad/.env
WorkingDirectory=/home/tunitech/tunitech-abroad
ExecStart=/home/tunitech/tunitech-abroad/.venv/bin/celery -A config.celery_app beat --pidfile=/home/tunitech/tunitech-abroad/celerybeat.pid --logfile=/home/tunitech/tunitech-abroad/celerybeat.log

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable celery celerybeat
sudo systemctl start celery celerybeat
```
