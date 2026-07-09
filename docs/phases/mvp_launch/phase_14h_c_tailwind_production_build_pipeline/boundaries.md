# Boundaries — Phase 14H-C

## Hard boundaries
- Do not introduce any frontend app framework.
- Do not use React, Next.js, Angular, Vue, Svelte, or SPA routing.
- Do not add Vite unless it is used only as a static build helper and does not create an app shell. Prefer simple Tailwind CLI.
- Do not edit business logic.
- Do not edit model fields or create migrations.
- Do not change URL behavior.
- Do not change auth, CV privacy, job ingestion, LLM, matching, or recommendations.
- Do not deploy.
- Do not commit.

## Low-risk preferred approach
Use Tailwind CLI with a minimal `package.json`:

```json
{
  "scripts": {
    "css:build": "tailwindcss -i ./static/src/css/app.css -o ./static/css/app.css --minify",
    "css:watch": "tailwindcss -i ./static/src/css/app.css -o ./static/css/app.css --watch"
  },
  "devDependencies": {
    "tailwindcss": "^3.4.17"
  }
}
```

This project currently uses CDN-style Tailwind utility classes. Tailwind v3 CLI is acceptable for this phase because it is stable and low-risk. Do not perform a Tailwind v4 migration unless the repo already has v4.

## Git hygiene
- Commit `package.json`, `package-lock.json`, Tailwind config, source CSS, generated CSS, templates/docs/tests.
- Do not commit `node_modules/`.
- Do not commit `staticfiles/`, collectstatic output, caches, `.env`, or secrets.
