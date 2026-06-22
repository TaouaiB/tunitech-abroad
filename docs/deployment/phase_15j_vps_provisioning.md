# VPS Provisioning

1. Provision a Hetzner Cloud Linux VPS (e.g., Debian/Ubuntu or Fedora).
2. Add your public SSH key during provisioning.
3. Login as root to set up the `tunitech` user:

```bash
# SSH into root
ssh root@<SERVER_IP>

# Create user
useradd -m -s /bin/bash tunitech
usermod -aG sudo tunitech # Or wheel on Fedora

# Copy SSH keys
rsync --archive --chown=tunitech:tunitech ~/.ssh /home/tunitech
```
