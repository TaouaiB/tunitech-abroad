# Low-Token Agent Workflow for V16 Implementation

## Goal

Use agents efficiently without burning tokens or letting them redesign.

## Agent roles

### Gemini Pro

Best for mechanical implementation:

- HTML-to-Django conversion
- repeated component extraction
- CSS placement
- responsive markup conversion
- page-by-page template work

Do not use Gemini as product designer for this phase.

### GPT-5.5

Best for control/review:

- planning the next smallest task
- reviewing diffs
- checking missed v16 behavior
- detecting extra wording
- detecting scope creep
- writing QA checklist

GPT-5.5 should act as reviewer/mentor, not as a second competing implementer.

## Token-saving method

Do not paste full HTML into chat.

Agents should read local files:

```text
/docs/ui/v16-final/<page>.html
```

Each task should name:

- prototype source file
- target Django template file
- allowed files to edit
- exact acceptance checklist

## One task format

Each agent task should be small:

```text
Task: implement v16 job card component.
Read:
- docs/ui/v16-final/index.html
- current templates/jobs/index.html
- current job model fields

Allowed edits:
- templates/components/job_card.html
- templates/jobs/index.html only if needed
- static/css/tuniatlas_v16.css only if needed

Do not:
- redesign
- add wording
- change backend logic
- change models

Return:
- files changed
- exact v16 elements implemented
- missing/unmapped elements, if any
- checks run
```

## Work loop

Use this loop for every page/component:

```text
1. Inspect current template and v16 page.
2. Implement exact visual structure.
3. Replace static text/data with Django variables.
4. Wire HTMX only where needed.
5. Run checks.
6. Screenshot compare.
7. Fix differences only.
8. Commit.
```

## Output discipline

Agent output should be short:

```text
Files changed:
- ...

Implemented:
- ...

Not changed:
- ...

Checks:
- ...

Next recommended task:
- ...
```

No long reasoning. No philosophy. No UX recommendations.

## Parallel work rule

Do not let Gemini and GPT-5.5 edit the same files at the same time.

Safe split:

- Gemini implements one page/component
- GPT-5.5 reviews the diff
- Gemini fixes only reviewed issues
- commit
- move to next page

## Stop conditions

Stop and ask before changing:

- models
- migrations
- auth logic
- matching/scoring logic
- recommendation logic
- payment/billing logic
- production settings
- security-sensitive behavior
