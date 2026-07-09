# Static Build Playbook — Tailwind

## Local one-time setup

```bash
cd ~/Projects/tunitech-abroad
npm install
```

## Build CSS once

```bash
npm run css:build
```

## Watch CSS while editing templates

```bash
npm run css:watch
```

Run the Django server in another terminal:

```bash
source .venv/bin/activate
python manage.py runserver --settings=config.settings.local
```

## Deployment order
For deployment later, the safe order is:

```bash
npm ci
npm run css:build
python manage.py collectstatic --noinput --settings=config.settings.production
python manage.py migrate --settings=config.settings.production
```

Do not commit:
- `node_modules/`
- `staticfiles/`
- `.env`
- build caches

Commit:
- `package.json`
- `package-lock.json`
- `tailwind.config.js`
- `static/src/css/app.css`
- generated `static/css/app.css`
