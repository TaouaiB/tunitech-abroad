# Tailwind CSS Setup & Playbook

TuniTech Abroad uses Tailwind CLI to build and minify CSS for production and local development. This approach replaces the CDN for faster load times and production readiness.

## Local Development

### 1. Install dependencies
When setting up the project locally for the first time, run:
```bash
npm install
```

### 2. Build CSS once
To manually trigger a one-time build of the CSS:
```bash
npm run css:build
```

### 3. Watch CSS during development
When making changes to UI/templates locally, run the Tailwind watcher in a separate terminal to automatically rebuild CSS on save:
```bash
npm run css:watch
```

## Deployment

During deployment, ensure that the Tailwind CSS build step runs **before** Django's `collectstatic`:
1. `npm install`
2. `npm run css:build`
3. `python manage.py collectstatic --noinput`

## Version Control Rules
- **`node_modules/` must NOT be committed** (it is excluded in `.gitignore`).
- The `package.json` and `package-lock.json` must be committed.
- Both the source CSS (`static/src/css/app.css`) and generated CSS (`static/css/app.css`) are currently committed.
