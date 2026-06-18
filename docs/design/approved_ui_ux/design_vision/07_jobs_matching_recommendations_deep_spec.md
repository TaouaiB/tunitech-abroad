# 07 — Jobs, Matching, and Recommendations Deep UX Spec v3

## Public job search must feel fast

Perceived speed matters.

Required behavior:

- page loads with filters and job list
- active filters visible as chips
- user can clear all filters
- pagination is clear
- empty states are actionable
- form submission gives visible feedback

## Active filter chips

Example:

```text
Python ×
Paris ×
Remote ×
Junior ×
```

Clear action:

```text
Réinitialiser
```

## Job card hierarchy

Priority order:

1. Title
2. Company/location
3. Contract/job/remote badges
4. Skills
5. Description preview
6. Freshness/status
7. Actions

## Bad job data handling

Never render a giant blank card.

Fallbacks:

| Missing value | UI |
|---|---|
| title | Offre sans titre |
| company | Entreprise non précisée |
| location | Lieu non précisé |
| description | Description non disponible |
| skills | Compétences en cours d'analyse |
| source URL | Lien de candidature non disponible |

If title and company and description are all missing, the card should be visually compact and marked `Données incomplètes`.

## Job card visual spec

```text
white/dark card
rounded-2xl
border
hover lift
clear title
muted metadata
badges row
skill chips row
CTA footer
```

Interactive card class:

```html
class="tta-card tta-card-hover p-5"
```

## Match score UX

### Score labels

| Score | Label | Class |
|---:|---|---|
| 80–100 | Très bon match | success |
| 65–79 | Bon potentiel | brand |
| 50–64 | Match partiel | warning |
| < 50 | Match faible | danger |

### Display rule

Always show:

```text
[score]% — [label]
[one-sentence reason]
```

### Example outputs

Strong:

```text
82% — Très bon match
Votre profil correspond bien aux compétences principales demandées.
```

Partial:

```text
58% — Match partiel
L'offre est intéressante, mais certaines compétences requises manquent.
```

Weak:

```text
46% — Match faible
Le score est limité principalement par les compétences techniques détectées.
```

## Score breakdown display

Categories:

- Technique
- Expérience
- Rôle/titre
- Langues
- Localisation

Each category displays:

- label
- percentage
- semantic color
- optional short note

## Risk flags

Risk flags must be shown as warnings, not hidden in text.

Examples:

| Risk | French copy |
|---|---|
| `experience_too_low` | Expérience probablement insuffisante |
| `missing_required_skills` | Compétences requises manquantes |
| `french_level_missing` | Niveau de français non renseigné |
| `english_level_missing` | Niveau d'anglais non renseigné |
| `profile_incomplete` | Profil incomplet |
| `job_may_be_expired` | Offre possiblement expirée |
| `internship_type_unclear` | Type de stage à vérifier |

## Recommended actions

Every match detail should have an action plan section.

Examples:

```text
Ajoutez votre niveau de français.
Renforcez Django et PostgreSQL avant de postuler.
Ajoutez un lien GitHub si vous avez des projets publics.
Vérifiez la fraîcheur de l'offre avant candidature.
```

## Recommendation card required content

A recommendation card must include:

```text
Title
Company/location
Score + label
Why recommended
Matched skills
Missing required skills
Risk flags
Freshness
Actions
```

### Example recommendation card content

```text
Développeur Django Junior
Paris • CDI • Hybride
72% — Bon potentiel
Pourquoi : bon alignement Django/PostgreSQL et niveau junior cohérent.
Points forts : Django, PostgreSQL, Git
Compétences requises manquantes : Docker, tests automatisés
Points de vigilance : niveau de français non renseigné
[Voir la compatibilité] [Sauvegarder]
```

## Saved jobs UX

Saved jobs should not become a dead list.

Show stale/expired state:

```text
À vérifier
Expirée
Retirée
```

Allow:

- view job
- remove saved job
- apply if source available

## Quick match UX / Test rapide

Anonymous quick match must be frictionless.

Form fields:

- 3–5 skills
- experience level
- French level

Result:

- estimated score
- matched skills
- likely missing skills
- CTA to full analysis

No LLM. No CV stored. No fake precision.

Copy:

```text
Test rapide
Ce score est une estimation basée sur quelques informations. Créez un compte pour une compatibilité détaillée avec votre CV.
```
