# Phase 15G — Matching Explanation and Recommendation UX Hardening

## Purpose

Phase 15G fixes the quality of the match explanation page and recommendation actions after the ingestion, skill materialization, eligibility, and LLM E2E pipelines were hardened.

This is not a redesign phase and not a new matching engine phase. It is a focused hardening pass for score composition, noisy-skill presentation, missing-skill recommendations, and recommendation refresh UX.

## Background

A real frontend match showed:

- Final score: 82%.
- Location contributed 55% even though the product targets Tunisian/foreign candidates applying to France.
- `JSON` appeared as an optional skill to strengthen even though the candidate already had JavaScript, TypeScript, REST API, and Node.js.
- The page showed both `Compétences requises manquantes` and a redundant `À renforcer / Compétences obligatoires non détectées` block.
- `Actions recommandées` used English copy and neutral styling even when required skills were missing.
- The recommendations page needs a safe refresh/recalculate button.

## Phase boundary

Allowed:

- Remove location from final score calculation.
- Keep location/mobility as an informational warning only.
- Suppress noisy foundational skills from missing/optional display and recommendation actions.
- Remove redundant `À renforcer` card from the match detail page.
- Make `Actions recommandées` red/priority-styled when required skills are missing.
- Add a POST-only refresh/recalculate recommendations button.
- Keep logic in services/presentation helpers.
- Add/repair tests.

Not allowed:

- No React, Next.js, SPA, FastAPI, MongoDB, SQLAlchemy.
- No LLM calls from views/templates.
- No France Travail calls from public search, match, or recommendation views.
- No broad UI redesign.
- No new product features outside this scope.
- No fake-adding skills to user profiles.
- No deleting JSON/XML/YAML/etc. from the taxonomy globally.
- No changing public URL policy.
- No CV privacy changes unless fixing a directly discovered leak.

## Required final proof

The agent must prove:

- `JSON` is not displayed as missing/optional to strengthen when implied by stronger skills.
- `Angular` still appears as required missing when not in candidate profile.
- Location no longer reduces final score.
- A mobility/location note still appears as non-scored context.
- Redundant `À renforcer / Compétences obligatoires non détectées` block is gone.
- `Actions recommandées` is French and priority/red when required skills are missing.
- Refresh recommendations button is POST-only and calls service logic.
- Full tests pass.
