# Caddy Configuration

File: `/etc/caddy/Caddyfile`

```caddyfile
tunitech-abroad.com, www.tunitech-abroad.com {
    # Forward all traffic to Gunicorn
    reverse_proxy unix//home/tunitech/tunitech-abroad/gunicorn.sock
    
    # Do NOT define a route for /media/ here.
    # Private media MUST be served through Django authenticated views only.
    # Static files are handled by Whitenoise in Django directly.
}
```

```bash
sudo systemctl reload caddy
```
