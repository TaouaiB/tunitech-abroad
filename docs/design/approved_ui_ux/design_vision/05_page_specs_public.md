# 05 — Public Page Specifications v3

## 1. Homepage `/`

### Goal

Make the user search jobs or start CV analysis immediately.

### Current issue

The current homepage is clean but too brochure-like. It does not put actual job search above the fold.

### Required layout

```text
Navbar
Hero/Search Gateway
Latest Jobs Preview
How It Works
Candidate Types
Intelligence Preview
Final CTA
Footer
```

### Hero details

Use `.tta-hero`.

Required above the fold:

- pill: `Objectif France`
- H1
- subtitle
- job search form or search gateway
- fast chips
- primary CTA
- secondary CTA
- trust/privacy micro-copy

H1:

```text
Trouvez des offres IT en France adaptées à votre profil
```

Subtitle:

```text
TuniTech Abroad aide les talents IT tunisiens à trouver des offres françaises, comprendre leur compatibilité et identifier les compétences à renforcer.
```

Search fields:

- keyword/role input
- location input or select
- submit button: `Rechercher`

Fast chips:

```text
Stage PFE
Alternance
Junior
Django
Data
Remote
```

CTA row:

```text
Explorer les offres
Analyser mon CV
```

Trust line:

```text
CV privé • Analyse de compatibilité • Offres France
```

### Latest jobs preview

Show 3–6 cards.

If no jobs:

```text
Les offres seront bientôt disponibles.
```

Do not render blank cards.

## 2. Public jobs `/jobs/`

### Goal

Fast public job browsing from local PostgreSQL.

### Layout desktop

```text
Header
Active filter chips
Two-column layout
  Left: filter sidebar sticky
  Right: results count + sort + job cards + pagination
```

### Layout mobile

```text
Header
Search input
Filter drawer button
Active filter chips
Job cards
Pagination
```

### Filter sidebar fields

- Mots-clés
- Lieu
- Type de contrat
- Type d'emploi
- Télétravail
- Niveau d'expérience
- Compétence
- Trier par

Actions:

- `Appliquer les filtres`
- `Réinitialiser`

### Result header

Example:

```text
1096 offres trouvées
Tri : Plus récentes
```

### Job cards

Use the public job card variant.

Fallbacks required:

| Missing value | UI text |
|---|---|
| title | Offre sans titre |
| company | Entreprise non précisée |
| location | Lieu non précisé |
| description | Description non disponible |
| skills | Compétences en cours d'analyse |
| source URL | Lien de candidature non disponible |

### Empty state

```text
Aucune offre trouvée
Essayez d'élargir vos filtres ou de chercher une autre technologie.
[Réinitialiser les filtres]
```

## 3. Job detail `/jobs/<public_id>/`

### Goal

Help the user decide whether the job is worth applying to or analyzing.

### Layout desktop

```text
Back link
Two-column layout
  Main card
    title/company/status
    badges
    key facts grid
    technical stack
    description
  Sticky side card
    apply/source CTA
    save button
    match/test rapide CTA
```

### Layout mobile

```text
Back link
Title card
Action card
Technical stack
Description
```

Side card becomes normal stacked card.

### Required content

- title
- company
- location
- contract type
- job type
- remote type
- experience level
- status/freshness
- source apply link
- save action if authenticated
- test rapide for anonymous
- full match for authenticated
- skills
- language requirements if available
- description

### Test rapide panel

Anonymous state:

```text
Testez rapidement votre compatibilité
Ajoutez 3 à 5 compétences, votre niveau d'expérience et votre niveau de français.
```

Result state:

- estimated score
- matched skills
- likely missing skills
- CTA: `Créer un compte pour l'analyse complète`

### Data uncertainty

If classification is suspicious or unknown, use:

```text
Type à vérifier
Télétravail non précisé
Expérience non précisée
```

Do not visually overclaim.

## 4. CV checker `/cv-checker/`

### Goal

Explain why CV upload matters without allowing anonymous CV processing.

### Layout

```text
Hero
3-step explanation
Privacy/trust block
Example insight cards
CTA
FAQ-lite
Footer
```

CTA behavior:

- anonymous → login/signup
- authenticated → `/dashboard/cv/`

### Copy

H1:

```text
Analysez votre CV pour cibler les bonnes offres en France
```

Trust block:

```text
Votre CV reste privé. Il sert uniquement à extraire vos compétences et améliorer vos scores de compatibilité.
```

## 5. Auth pages public shell

Login/signup pages use split-screen desktop layout and single-column mobile layout.

Desktop:

```text
Left: visual/value panel
Right: form card
```

Mobile:

```text
Logo/header
Form card only
```

Left panel content:

```text
France IT,
profil tunisien.
Analysez votre compatibilité sans rendre public votre CV.
```

Use abstract SVG/connection pattern. No flags, no stock images.

## 6. Legal pages `/privacy/` and `/terms/`

Use `.tta-legal`.

Must include readable headings, lists, spacing, and dark-mode support.

Legal pages must look intentionally designed, not like raw markdown dumped into HTML.
