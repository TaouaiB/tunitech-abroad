# Phase 15E Diagnostic Summary

## Observed issue

The admin query showed:

```text
ACTIVE EXCLUDED_NON_IT JOBS: 10
```

But several rows are clearly technical:

```text
Data Engineer GCP
Data Engineer / Expert Data Intégration
Tech Lead / DevOps
Développeur .NET / C# Fullstack
Développeur fullstack Java/Angular confirmé
Consultant Cybersécurité Sénior
Ingénieur en Optimisation R&D
```

These rows had `classification_json.is_it = False`, `family = non_it`, and negative reason `Contains explicit non-IT negative signals`, even though many have materialized `job_skills`.

## Interpretation

The classifier is over-triggering on negative/business words such as:
- client
- commercial
- secteur
- transformation digitale
- business
- conseil
- développement commercial

Those words can appear inside real IT consulting/software/data jobs. Negative signals must not override strong technical evidence.

## Real non-IT examples

These should be hidden from public IT jobs:

```text
CHARGÉ D'AFFAIRES / DEVELOPPEUR COMMERCIAL AGENCEMENT BOIS
SDR/BDR - Business Developer - Cybersécurité
Animateur/trice réseau / développeur/euse réseau de franchise
Médiateur/Médiatrice scientifique - spécialité cybersécurité
Stage Consultant transformation digitale - Transport, Infrastructure, Manufacturing & Energy
```

## Important semantic traps

### `réseau`

IT:
- réseau informatique
- LAN/WAN
- VPN
- systèmes et réseaux
- infrastructure réseau

Non-IT:
- réseau de franchise
- réseau de magasins
- développer un réseau commercial
- animer le réseau
- franchisés
- points de vente

### `cybersécurité`

IT:
- security engineer
- SOC
- pentest
- GRC / ISO / EBIOS / NIS2 / DORA
- cyber risk/audit/security implementation

Non-IT:
- SDR/BDR cyber
- business developer cyber
- mediator/science outreach cyber
- promoting cybersecurity to students/general public

## Product behavior target

A job should be one of:

```text
PUBLIC_MATCHABLE
PUBLIC_LIMITED_PENDING_ANALYSIS
ADMIN_REVIEW_ONLY
EXCLUDED
```

`excluded_non_it` is not enough alone; eligibility must combine classification, title/description evidence, skill rows, and known false-positive patterns.
