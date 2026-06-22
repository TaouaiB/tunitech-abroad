# Gunicorn Systemd Service

Create `/etc/systemd/system/gunicorn.service`:

```ini
[Unit]
Description=gunicorn daemon
Requires=gunicorn.socket
After=network.target

[Service]
User=tunitech
Group=tunitech
WorkingDirectory=/home/tunitech/tunitech-abroad
ExecStart=/home/tunitech/tunitech-abroad/.venv/bin/gunicorn \
          --access-logfile - \
          --workers 3 \
          --bind unix:/home/tunitech/tunitech-abroad/gunicorn.sock \
          config.wsgi:application
EnvironmentFile=/home/tunitech/tunitech-abroad/.env

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/gunicorn.socket`:

```ini
[Unit]
Description=gunicorn socket

[Socket]
ListenStream=/home/tunitech/tunitech-abroad/gunicorn.sock

[Install]
WantedBy=sockets.target
```

```bash
sudo systemctl start gunicorn.socket
sudo systemctl enable gunicorn.socket
```
