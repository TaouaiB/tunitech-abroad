# Phase 15L Acceptance Criteria

Phase 15L is accepted only if all criteria below are true.

## Brand

- [ ] Public UI shows `TuniAtlas` / `TuniAtlas Jobs`, not `TuniTech Abroad`.
- [ ] SEO/browser title uses `TuniAtlas — Tech Jobs Abroad for Tunisians` or a consistent page-specific variant.
- [ ] Logo/favicon assets are present or the missing asset is explicitly documented as a manual blocking item.
- [ ] Repo/internal Python/Django names are not renamed.

## Deployment preparation

- [ ] Domain plan is documented: `tuniatlas.com` primary, `tuniatlas.tn` later/defensive.
- [ ] Hosting/server decision is documented but no purchase/server action is performed.
- [ ] Email provider plan is documented.
- [ ] Backup destination and restore expectation are documented.
- [ ] Phase 15M exact deployment order is documented.

## Security and privacy

- [ ] `.env` was not read, printed, edited, created, or committed.
- [ ] `.env.example` and deployment templates contain placeholders only.
- [ ] Automatic LLM spending remains disabled by default in production docs/config examples.
- [ ] Private media/CV files are not publicly exposed by Caddy/Nginx/Whitenoise docs.
- [ ] No France Travail live API call is added to public search/views.
- [ ] No OpenRouter call is added to views/templates/models/admin display.

## Verification

- [ ] `python manage.py check --settings=config.settings.local` passes.
- [ ] `python manage.py makemigrations --check --dry-run --settings=config.settings.local` passes.
- [ ] Full Django test suite passes.
- [ ] `npm run css:build` passes.
- [ ] Local and production `collectstatic --dry-run` pass.
- [ ] `python manage.py check --deploy --settings=config.settings.production` passes.
- [ ] `pip-audit`, `bandit`, and `npm audit --omit=dev` pass or any non-blocking issue is explicitly justified.
- [ ] `git diff --check` passes.
- [ ] Secret grep finds no real secrets.

## Reports

- [ ] Gemini implementation report exists.
- [ ] Sonnet review report exists.
- [ ] Reports do not misidentify the model as Codex/GLM if not used.
