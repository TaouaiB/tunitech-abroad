# Phase 15L — Deployment Execution Preparation + TuniAtlas Public Rebrand Lock

## Purpose

Prepare the project for real VPS deployment while locking the public brand as **TuniAtlas**.

This phase is **not actual deployment**. It must not provision a VPS, configure DNS, buy services, run commands on a server, or touch a real production `.env`.

## Brand lock

- Public brand: `TuniAtlas`
- Product line: `TuniAtlas Jobs`
- Tagline: `Tech careers abroad for Tunisian talent`
- SEO title: `TuniAtlas — Tech Jobs Abroad for Tunisians`
- Primary domain target: `tuniatlas.com`
- Secondary/later domain target: `tuniatlas.tn`
- Repository/internal project name: keep `tunitech-abroad` until after deployment

## Agent workflow

- Gemini: implementation
- Sonnet: review/repair
- Opus: reserved for final security audit before public launch
- GLM: do not use for this phase
- Codex: do not use unless explicitly requested later

## Hard boundaries

Do not add new product features.
Do not redesign the full UI/UX pack.
Do not change matching/scoring logic.
Do not rename Django apps, migrations, database tables, Python packages, repo, or deployment service names.
Do not read, create, print, or commit `.env`.
Do not deploy.
