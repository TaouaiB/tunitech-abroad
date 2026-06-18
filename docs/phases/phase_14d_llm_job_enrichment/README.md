# Phase 14D — LLM-Assisted Job Enrichment Pipeline

## Purpose

Phase 14C proved that deterministic regex/classification alone is not enough for messy France Travail job data. Real IT offers often hide their useful stack in free-text descriptions, while `competences[]` can be generic. This phase adds an offline, controlled LLM enrichment pipeline to turn raw job text into validated structured job intelligence.

## Core product rule

The public website must feel like a serious job platform. Do not expose internal parser/debug wording to users.

User-facing pages must avoid labels like:

- IT / non-IT
- low IT signal
- `skill_signal_quality`
- `match_confidence`
- `generic_only`
- `no_required_skills_extracted`
- raw risk flags

Use friendly product wording instead:

- Bon potentiel
- Potentiel moyen
- À vérifier
- Faible alignement
- Analyse limitée
- Analyse CV non disponible

## Architecture rule

LLM enrichment is an offline data-quality layer only.

Allowed:

- Celery task calls LLM job enrichment service.
- Management command enqueues enrichment tasks.
- Enriched result is cached in PostgreSQL.
- Matching uses enriched data deterministically.

Forbidden:

- No LLM calls from Django views.
- No LLM calls from templates.
- No LLM calls during normal user search/request.
- No France Travail live API calls during normal user search.
- No LLM final fit scoring.

## Final verdict rule

Agent must end with either:

```text
FAIL
BLOCKED_HUMAN_VISUAL_SIGNOFF
```

Never write PASS before Baha manually checks the website in Chrome.
