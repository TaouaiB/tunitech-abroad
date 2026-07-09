# Manual Readiness Checklist — Phase 15I

Before Phase 15J deployment begins, manually confirm:

## Repo

- [ ] Phase 15H committed and pushed.
- [ ] Phase 15I changes reviewed and committed.
- [ ] `git status --short --branch` is clean except intentional local runtime files.

## Secrets

- [ ] `.env` was not committed.
- [ ] `.env.example` has placeholders only.
- [ ] No real OpenRouter, France Travail, email, Google, GitHub, DB, Redis secrets in diff.

## LLM spend control

- [ ] Production example disables automatic job enrichment.
- [ ] CV LLM extraction disabled by default.
- [ ] Public browsing/search/matching does not call OpenRouter.
- [ ] Public search does not call France Travail.

## CV/privacy

- [ ] CV files private.
- [ ] `private_media` not served by Caddy/Nginx/Whitenoise.
- [ ] CV ownership checks documented.
- [ ] Delete CV/account flows documented.

## Deployment prerequisites

- [ ] Domain chosen.
- [ ] Email provider chosen.
- [ ] OAuth callback URLs planned.
- [ ] Backup target chosen.
- [ ] Monitoring plan chosen.
- [ ] Rollback plan exists.
