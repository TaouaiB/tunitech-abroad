# Gemini Prompt — Phase 15G Matching Explanation and Recommendation UX Hardening

You are working on TuniTech Abroad. Follow project architecture strictly.

## Context

The project is a Django + PostgreSQL + Redis + Celery + Django templates + HTMX + Tailwind platform. It is France-first job intelligence for Tunisian IT candidates.

Do not introduce React, Next.js, Angular, FastAPI, MongoDB, SQLAlchemy, or SPA architecture.

Do not call OpenRouter/LLM from views/templates/admin/models. Do not call France Travail from public search/match/recommendation views.

## Mission

Implement Phase 15G only:

```text
Matching Explanation and Recommendation UX Hardening
```

Fix these issues:

1. Location currently contributes to final match score. Remove it from final score.
2. Keep mobility/location as informational note only.
3. Suppress noisy foundational skills like `JSON` from missing/optional recommendations when implied by stronger skills.
4. Remove redundant `À renforcer / Compétences obligatoires non détectées` block.
5. Improve `Actions recommandées`: French copy and red/priority styling when required skills are missing.
6. Add a POST-only refresh recommendations button.
7. Add tests.

## Required policies

Read these files first:

- `docs/phases/phase_15g_matching_explanation_recommendation_ux_hardening/tasks.md`
- `docs/phases/phase_15g_matching_explanation_recommendation_ux_hardening/scoring_policy.md`
- `docs/phases/phase_15g_matching_explanation_recommendation_ux_hardening/noisy_skill_policy.md`
- `docs/phases/phase_15g_matching_explanation_recommendation_ux_hardening/refresh_recommendations_policy.md`

## Implementation rules

- Views stay thin.
- Business logic goes in services/presentation helpers.
- Templates render prepared data only.
- Do not fake-add JSON to user skills.
- Do not delete JSON from taxonomy.
- Do not change LLM scoring/eligibility pipelines except if directly needed for presentation filtering; avoid touching LLM phase code.
- Do not broaden scope into UI redesign.
- Do not change public URL ID policy.

## Expected behavior example

For this match:

```text
Strengths:
JavaScript, TypeScript, HTML5, CSS3, REST API, Node.js, Docker, Jest, Git
Required missing:
Angular
Optional gaps:
JSON, Kubernetes, Jenkins, Nexus Repository, Ionic, Cypress, GitLab, Jira, Confluence
```

Display:

```text
Required missing:
Angular
Optional gaps:
Kubernetes, Jenkins, Nexus Repository, Ionic, Cypress, GitLab, Jira, Confluence
```

`JSON` must not appear.

Remove:

```text
À renforcer
Compétences obligatoires non détectées
```

Actions recommended should be French and priority/red:

```text
Actions recommandées
Priorité : ajoutez Angular à votre plan d'apprentissage.
Mettez à jour votre CV si vous avez déjà utilisé Angular.
```

## Required checks

Run:

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test --settings=config.settings.local --parallel 1
npm run css:build
python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
git diff --check
```

Run the security greps from `tasks.md`.

## Report

Create:

```text
docs/phases/phase_15g_matching_explanation_recommendation_ux_hardening/agent_report.md
```

Use the template.
