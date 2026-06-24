# 06 — Private Dashboard Page Specifications v3

## 1. Dashboard `/dashboard/`

### Goal

Show next best action and summarize core product value.

### Current issue

The current dashboard is clean but too static. It works as a menu, not a strong action center.

### Required layout

```text
Page header
  Bonjour, [name/email]
  Short subtitle
  Contextual CTA

Next action card
  Conditional state

Bento grid
  Profile completeness
  CV status
  Recommendations preview
  Missing skills
  Saved jobs
  Recent analyses

Account/settings strip
  Email preferences
  Security & account
```

### Conditional next action card

No CV:

```text
Ajoutez votre CV
Votre CV permet d'extraire vos compétences et d'améliorer vos scores de compatibilité.
[Ajouter mon CV]
```

CV processing:

```text
Analyse du CV en cours
Nous préparons vos données de profil.
[Voir le statut]
```

Profile incomplete:

```text
Complétez votre profil
Certaines informations manquent pour obtenir des recommandations fiables.
[Compléter mon profil]
```

Recommendations ready:

```text
Vos recommandations sont prêtes
Consultez les offres les plus cohérentes avec votre profil.
[Voir mes recommandations]
```

### Bento card rules

- Cards must be clickable if they lead to a page.
- Use icons sparingly.
- Each card needs title, short text, and status/metric.
- Avoid decorative empty cards.

## 2. Profile `/dashboard/profile/`

### Goal

Help the user make profile usable/strong for matching.

### Required structure

```text
Back link
Page header
Completeness card
Readiness alert
Profile form card
  Identity/contact
  Links
  Objective France
  Experience
  Languages
  Preferences
  Skills
Sticky mobile save bar
```

### Completeness card

Show:

- score percentage
- status label: `Incomplet`, `Utilisable`, `Fort`
- progress bar
- missing fields list if available

### Form section rules

Each section has:

- section title
- short help text if complex
- grouped fields

No endless wall of fields.

### Mobile save

Use sticky mobile save bar:

```text
[Enregistrer le profil]
```

Desktop save can stay at bottom or top-right of form card.

## 3. CV `/dashboard/cv/`

### Goal

Make CV status, privacy, upload, parsing, and deletion clear.

### Required layout

```text
Back link
Page header
Active CV card
  filename
  uploaded date
  parsed date
  parse status
  extracted summary
  privacy line
Upload/replace card
  dropzone
  consent checkbox
  submit button
Danger/delete action
```

### Active CV status labels

| Status | Label | Semantic |
|---|---|---|
| pending | En attente | info |
| processing | Analyse en cours | info/loading |
| parsed | Analyse terminée | success |
| parsed_with_warnings | Analyse terminée avec avertissements | warning |
| failed | Analyse échouée | danger |
| deleted | Supprimé | muted/danger |

### Privacy line

Always visible:

```text
Fichier chiffré et privé. Non partagé avec les employeurs.
```

### Upload rules

- PDF only.
- max 5 MB unless system setting says otherwise.
- consent required.
- dropzone has drag-over feedback.
- submit button disabled/clear during upload if possible.

## 4. Recommendations `/dashboard/recommendations/`

### Goal

Show ranked jobs with intelligence, not just job cards.

### Required layout

```text
Back link
Page header
Status/filter bar
Recommendation cards
Empty/pending/stale states
```

### Recommendation card content

- title
- company/location
- score + score label
- reason
- matched skills
- missing skills
- risk flags
- freshness
- actions: `Voir la compatibilité`, `Sauvegarder`, `Postuler`

### Empty state

No recommendations:

```text
Aucune recommandation disponible
Ajoutez un CV ou complétez votre profil pour recevoir des offres adaptées.
[Ajouter mon CV] [Compléter mon profil]
```

Stale recommendations:

```text
Vos recommandations peuvent être anciennes
Nous les mettons à jour en arrière-plan. Les résultats actuels restent visibles.
```

## 5. Match detail `/dashboard/matches/<public_id>/`

### Goal

Explain score and teach user what to fix next.

### Required layout

```text
Back link
Hero score card
  job title/company
  global score ring
  score label
  analyzed date
Score breakdown grid
Analysis sections
  Points forts
  Compétences requises manquantes
  Points de vigilance
  Actions recommandées
Apply side card
Optional explanation panel
```

### Score explanation rule

Always pair number with interpretation.

Example:

```text
46% — Match faible
Le score est limité principalement par les compétences techniques détectées.
```

## 6. Saved jobs `/dashboard/saved-jobs/`

### Goal

Allow user to return to interesting jobs and notice stale/expired states.

### Card content

- title
- company/location
- saved state
- job status/freshness
- actions: view, unsave, apply if available

Empty state:

```text
Aucune offre sauvegardée
Sauvegardez les offres intéressantes pour les comparer plus tard.
[Explorer les offres]
```

## 7. Email preferences `/dashboard/email-preferences/`

### Goal

Simple consent-based email control.

Content:

- weekly digest toggle
- product updates toggle if exists
- explanation of frequency
- unsubscribe/privacy link

No complex notification center.

## 8. Account/security `/dashboard/account/`

### Goal

Security, linked accounts, privacy links, deletion.

Sections:

- profile identity summary
- password management
- linked Google/GitHub accounts
- privacy links
- danger zone

Danger zone must be visually separated using rose semantic styling. Do not add fake data-export or cookie controls unless matching backend routes and consent behavior already exist; show privacy links and deletion controls that are implemented.
