# Server Packages Installation

SSH as `tunitech` user and install dependencies:

```bash
# Update system
sudo apt update && sudo apt upgrade -y  # Or dnf on Fedora

# Install dependencies
sudo apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib redis-server curl git build-essential libpq-dev

# Install Caddy
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install caddy
```
