# Preflight — Phase 14H-C

Run before edits:

```bash
cd ~/Projects/tunitech-abroad
source .venv/bin/activate

git status --short
python --version
node --version || true
npm --version || true
python manage.py check --settings=config.settings.local
```

If Node/npm are missing on Fedora:

```bash
sudo dnf install -y nodejs npm
node --version
npm --version
```

Do not proceed if the working tree has unrelated dirty files. Ask the user first.
