# Gate C — CV Parser v2 Implementation Prompt

You are working in the TuniAtlas Django repository.

## Agent choice

Recommended agent: **Codex GPT-5.5 medium in Warp**.

Reason: this is a Django service/test hardening task touching privacy-sensitive CV parsing and profile mutation. Keep changes deterministic, narrow, and reviewable.

## Current state

Expected local branch:
- `dev`
- local `dev` is ahead of `origin/dev` by 2 commits:
  - Gate A.2 production trust stabilization
  - Gate B skill extraction policy
- These commits are local only. Do not push.

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
- unexpected uncommitted changes exist
- `.env` is modified
- migrations are created unexpectedly
- Gate A.2 and Gate B commits are not present

Do **not** commit.
Do **not** push.

## Product context

TuniAtlas is a job intelligence platform for Tunisian IT candidates targeting international tech opportunities.

Stack constraints:
- Django, Django ORM, PostgreSQL, Redis, Celery, Django templates, HTMX/Tailwind.
- No React, Next.js, FastAPI, MongoDB, SQLAlchemy, SPA.
- Views stay thin.
- Business logic belongs in services.
- Celery tasks call services only.
- No LLM call from Django views.
- Public URLs use UUID public_id.
- CV files are private.
- CVUpload.objects must exclude soft-deleted CVs.
- CVUpload.all_objects is only for admin/privacy/deletion/internal tasks.
- Matching remains deterministic.
- LLM may extract/explain/suggest but must never decide final fit score.

## Gate C scope

Implement **CV Parser v2** only.

Goal:
Stop CV parsing from polluting candidate profiles with wrong personal fields and random phrase skills. The parser should extract useful structured signals only:
- skills
- languages
- experience level / years where reliable
- target roles only if reliable
- parsing warnings/confidence

It must not overwrite confirmed user profile data with low-confidence parsed values.

Use the Gate A baseline report as source:
`docs/phases/post_launch/gate_a_baseline_current_damage/gate_a_baseline_report_2026_07_10.md`

Confirmed damage examples:
- raw_skills polluted by phrases:
  - API smoke tests
  - authentication flows
  - based access control
  - bug reports
  - CI basics
  - freelance web developer
  - implemented input validation
  - inventory manager api
  - language extraction
  - location extraction
  - manual QA
  - recommended learning topics
  - responsive UI
  - SEO metadata
  - server
  - stock alerts
  - stock movements
  - suppliers
  - validation
  - web development
- parser warns about CV name mismatch and may treat personal identity fields as useful profile updates.
- skills are extracted from arbitrary comma-separated lines, not only skill/stack sections.
- broad/general CV phrases can become ProfileSkill pollution.

## Required implementation

### 1. Section-aware CV skill extraction

Update deterministic CV parsing so skills are extracted from reliable sections first.

Allowed skill sections include headers like:
- Skills
- Technical Skills
- Compétences
- Compétences techniques
- Stack
- Technologies
- Tools
- Frameworks
- Databases
- Cloud
- DevOps
- Testing
- Languages / Programming Languages

Stop skill sections at headers like:
- Experience
- Professional Experience
- Projects
- Education
- Certifications
- Contact
- Profile
- Summary
- Languages if it means human languages
- Interests

Rules:
- Prefer known canonical SkillAlias matching.
- Do not create canonical Skill rows.
- Unknown skill candidates may be tracked only when they come from explicit skill/technical sections.
- Do not extract arbitrary 2-3 word phrases from general bullets.
- Do not treat every comma-separated line as a skill list unless inside a skill/technical section.
- Keep skill extraction deterministic.

### 2. Use Gate B policy for CV skills where practical

If a skill policy/service exists from Gate B, reuse it so broad/noise/process/soft phrases are not added as confirmed ProfileSkill rows.

CV parser must reject or ignore:
- language extraction
- location extraction
- validation
- server
- tools as a standalone skill
- testing as a standalone skill unless mapped to a specific canonical testing skill
- web development
- freelance web developer
- stock alerts / stock movements / suppliers
- recommended learning topics
- bug reports
- implemented input validation
- authentication flows
- manual QA unless there is a canonical skill and policy allows it
- API smoke tests unless treated as non-required broad signal, not confirmed hard skill

### 3. Protect confirmed profile data

Do not overwrite user-confirmed profile fields with low-confidence CV parser output.

Required behavior:
- Existing confirmed profile skills remain.
- CV-detected skills may be added with source `cv_upload` and confidence.
- Low-confidence personal fields should not overwrite profile name, location, target roles, current level, or languages if user already set them.
- If parsed data conflicts with existing profile data, create/keep a warning or skip update; do not blindly overwrite.
- CV personal identity parsing can be removed, ignored, or reduced to warnings.

### 4. Parsing warnings and confidence

Use existing status/warnings fields if present. Do not add migrations unless unavoidable.

Add warnings for:
- no reliable skill section found
- only broad/noisy skill candidates found
- possible name/location/profile mismatch
- low-confidence parsing
- unsupported/empty CV text

### 5. Tests required

Add or update tests for:

- explicit skill section extracts known aliases.
- arbitrary project bullet phrases are not extracted as skills.
- comma-separated non-skill line outside skill section is ignored.
- unknown candidates from non-skill sections are not tracked.
- unknown candidates from explicit technical skill section may be tracked according to existing conventions.
- profile confirmed fields are not overwritten by CV parser output.
- existing confirmed skills are preserved.
- CV-detected skills are added only for accepted canonical aliases.
- noisy examples from Gate A are rejected or not confirmed:
  - language extraction
  - location extraction
  - recommended learning topics
  - stock alerts
  - stock movements
  - suppliers
  - validation
  - server
  - freelance web developer
  - web development
- CVUpload privacy/soft-delete tests still pass.

### 6. Commands to run

Run:

```bash
python manage.py check --settings=config.settings.local
python manage.py test apps.cvs apps.profiles apps.skills --settings=config.settings.local
python manage.py test apps.accounts apps.core apps.cvs apps.jobs apps.matching apps.recommendations --settings=config.settings.local
```

Run `npm run css:build` only if you touched CSS. You should not need CSS.

## Expected final report

Report:
- files changed
- parser behavior changed
- tests added
- tests run and result
- any deferred cases for Gate D admin anomaly review
- confirm no migrations unless explicitly justified
- confirm no job skill extraction work beyond direct reuse of Gate B policy
- confirm no commit/push
