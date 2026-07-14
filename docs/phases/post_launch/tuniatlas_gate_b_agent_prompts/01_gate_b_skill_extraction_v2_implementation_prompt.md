# Gate B — Skill Extraction v2 Implementation Prompt

You are working in the TuniAtlas Django repository.

## Agent choice

Recommended agent: **Codex GPT-5.5 medium in Warp**.

Reason: this is a repo-wide Django service/test hardening task. Keep changes deterministic, small, and reviewable.

## Current branch and safety

Start with:

```bash
cd ~/Projects/tunitech-abroad
git status --short --branch
git log --oneline --decorate -8
git diff --stat
git diff --check
```

Stop if:
- branch is not `dev`
- there are unexpected uncommitted changes
- `.env` is modified
- migrations are created unexpectedly
- Gate A.2 commit is not clean

Do **not** commit.
Do **not** push.

## Product context

TuniAtlas is not a generic job board. It is a job intelligence platform for Tunisian IT candidates targeting international tech opportunities.

Stack constraints:
- Django, Django ORM, PostgreSQL, Redis, Celery, Django templates, HTMX/Tailwind.
- No React, Next.js, FastAPI, MongoDB, SQLAlchemy, SPA.
- Views stay thin.
- Business logic belongs in services.
- Celery tasks call services only.
- No LLM call from Django views.
- No France Travail live API calls during normal user search.
- Public URLs use UUID public_id.
- Matching remains deterministic.
- LLM may extract/suggest but must never decide final fit score.

## Gate B scope

Implement **Skill Extraction v2** only.

Goal:
Reduce noisy job skill extraction and make extracted skills useful for matching and recommendations.

Use the Gate A baseline report as source:
`docs/phases/post_launch/gate_a_baseline_current_damage/gate_a_baseline_report_2026_07_10.md`

Confirmed damage:
- Teamwork, Communication, Agile, Scrum, API, Monitoring, Technical Documentation, Technical Watch, Software Development, Software Testing are being extracted as required/detected skills.
- Generic France Travail phrases are polluting unmatched candidates:
  - Concevoir une application web
  - Application web
  - Rédiger un cahier des charges...
  - Déterminer des mesures correctives
  - Configurer le poste de travail...
  - Collaborer avec une équipe projet
- Generic-only jobs exist:
  - job with only Teamwork
  - job with only Communication
  - job with only Technical Watch
- Some zero-skill jobs have `status=success` and `quality=partial`, causing inconsistent signal classification.
- SQL family must stay distinct:
  - SQL is not SQL Server
  - PostgreSQL, MySQL, SQLite, SQL Server are separate skills
- Chef must only be accepted in DevOps/config-management context, never chef de projet/cook/hospitality.

## Required implementation

### 1. Add a skill extraction policy/service layer

Add or update a service under `apps/skills/services/` or `apps/jobs/services/` that classifies extracted candidates before they become `NormalizedJobSkill`.

The policy must support at least:

- hard technical skill
- broad technical concept
- methodology/process
- soft skill
- source metadata / France Travail phrase
- rejected/noise

Required behavior:
- hard technical skills can be materialized as required/optional/detected.
- broad/process/soft skills must not become required missing skills.
- source metadata / France Travail phrases must not become materialized job skills.
- rejected/noise terms should be ignored or tracked as unmatched with ignored/rejected status depending existing model conventions.

### 2. Multiword-first and exact-boundary matching

Ensure alias matching prefers longer/more specific aliases before shorter aliases.

Examples:
- SQL Server must match SQL Server, not SQL.
- REST API should not reduce to plain API.
- GitLab CI/CD should not reduce to GitLab or CI/CD if the specific skill exists.
- PostgreSQL/MySQL/SQLite must remain separate from SQL.

Use punctuation-safe boundaries.

### 3. Context guard rules

Add or strengthen context guards for:

- `Chef`
  - accept: Chef cookbooks, Chef recipes, infrastructure automation, configuration management, DevOps.
  - reject: chef de projet, chef projet, chef d’équipe, kitchen, restaurant, cuisine, hospitality, cuisinier.
- `API`
  - plain API alone is broad. Do not make it a required skill.
  - allow REST API, OpenAPI, GraphQL, API testing/automation if those canonical skills exist or as lower confidence.
- `Monitoring`
  - plain monitoring is broad/process. Do not make it a required skill.
  - allow specific tools: Prometheus, Grafana, Datadog, Zabbix, Nagios, Sentry, ELK, etc.
- `Agile`, `Scrum`, `Communication`, `Teamwork`, `Leadership`
  - do not use as technical missing skills.
  - at most classify as non-scoring/context signal if existing design supports it.
- `Technical Documentation`, `Requirements Analysis`, `Technical Watch`, `Corrective Maintenance`, `Software Development`, `Software Architecture`, `Software Testing`
  - do not materialize as required technical skills unless a specific testing/tool skill is present.
  - specific skills such as Selenium, Playwright, Cypress, pytest, JUnit, Unit Testing may remain real.

### 4. Confidence and evidence

Preserve or add evidence/confidence fields already available.

Rules:
- high confidence: exact hard skill alias in technical context.
- medium/low confidence: broad but technical-ish concept.
- rejected: source metadata/generic phrase/soft-skill/process phrase.

Do not add migrations unless absolutely necessary. Prefer using existing fields.

### 5. Job quality classification

Fix inconsistent states:
- zero materialized skills should not be marked as strong/partial success in a misleading way.
- generic-only jobs should not be considered useful skill-signal jobs.
- if only rejected/broad/soft/process signals exist, classify as weak/insufficient according to existing model constants.

### 6. Seed/taxonomy adjustments allowed

Allowed:
- deactivate aliases that cause noise.
- adjust existing seed data/test fixtures.
- add explicit ignored terms.
- add context rejection rules.

Not allowed:
- creating unknown canonical skills automatically.
- broad taxonomy redesign.
- custom ML model.
- CV parser v2 changes.

### 7. Tests required

Add/adjust tests for:

- `chef de projet` does not produce Chef.
- Chef DevOps context still produces Chef.
- SQL Server does not produce SQL as duplicate.
- PostgreSQL/MySQL/SQLite remain distinct from SQL.
- REST API/OpenAPI/GraphQL handled better than plain API.
- plain API not required hard skill.
- Agile/Scrum/Communication/Teamwork/Leadership not scoring/missing technical skills.
- Technical Documentation/Technical Watch/Corrective Maintenance not required technical skills.
- zero-skill and generic-only jobs get weak/insufficient quality state.
- recommendation/matching tests still pass.

### 8. Commands to run

Run:

```bash
python manage.py check --settings=config.settings.local
python manage.py test apps.skills apps.jobs apps.matching apps.recommendations --settings=config.settings.local
python manage.py test apps.accounts apps.core apps.cvs apps.jobs apps.matching apps.recommendations --settings=config.settings.local
```

Run `npm run css:build` only if you touched CSS. You should not need CSS.

## Expected final report

Report:
- files changed
- extraction behavior changed
- tests added
- tests run and result
- any deferred cases for Gate D admin anomaly review
- confirm no migrations
- confirm no CV parser v2 work
- confirm no commit/push
