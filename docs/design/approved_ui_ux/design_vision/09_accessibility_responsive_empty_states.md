# 09 — Accessibility, Responsiveness, Empty States, and Micro-interactions v3

## Accessibility targets

Minimum:

- keyboard navigable
- visible focus states
- readable contrast
- labels on form fields
- large enough tap targets
- error messages near fields
- no color-only meaning
- dark mode contrast checked manually

## Focus states

All interactive elements must have:

```text
focus-visible:outline-none
focus-visible:ring-2
focus-visible:ring-brand-500
focus-visible:ring-offset-2
dark:focus-visible:ring-offset-slate-950
```

Apply to:

- links
- buttons
- inputs
- selects
- checkboxes
- dropdown menu items
- pagination links
- save buttons
- social auth buttons

## Tap targets

Minimum: 44px height or equivalent clickable area.

Especially:

- mobile nav button
- filter button
- save button
- checkboxes
- pagination
- job card actions

## Color contrast

Avoid low-contrast text such as:

```text
text-slate-400 on white for main copy
text-slate-500 on slate-900 for main copy
```

Use:

- body light: `text-slate-700`
- muted light: `text-slate-500/600`
- body dark: `text-slate-300`
- muted dark: `text-slate-400`

## Responsive breakpoints

| Area | Mobile | Desktop |
|---|---|---|
| Navbar | menu/dropdown | horizontal links |
| Jobs filters | drawer | sticky sidebar |
| Job cards | stacked | wider card layout |
| Job detail | stacked | main + sticky sidebar |
| Dashboard | one column | bento grid |
| Profile form | one column + sticky save | sectioned two-column |
| Auth | one column | split screen |
| Score ring | 96px | 128px |

## Empty states

Every empty state must include:

- icon
- title
- explanation
- action

### Jobs empty state

```text
Aucune offre trouvée
Essayez d'élargir vos filtres ou de chercher une autre technologie.
[Réinitialiser les filtres]
```

### Recommendations empty state

```text
Aucune recommandation disponible
Ajoutez un CV ou complétez votre profil pour recevoir des offres adaptées.
[Ajouter mon CV] [Compléter mon profil]
```

### Saved jobs empty state

```text
Aucune offre sauvegardée
Sauvegardez les offres intéressantes pour les comparer plus tard.
[Explorer les offres]
```

### CV empty state

```text
Aucun CV actif
Ajoutez votre CV PDF pour lancer l'analyse de compatibilité.
[Ajouter mon CV]
```

### Match history empty state

```text
Aucune analyse pour le moment
Lancez une analyse depuis une offre pour voir votre score détaillé.
[Explorer les offres]
```

## Micro-interactions

### Job cards

Use visible hover:

```text
hover:-translate-y-1
hover:shadow-xl
hover:border-brand-300
```

### Buttons

Use:

- hover color change
- disabled state
- loading state if submit can take time

### CV dropzone

Use visual drag-over state.

### HTMX actions

Use `hx-indicator` where possible.

Actions needing feedback:

- save/unsave
- quick match
- match explanation
- CV status polling
- recommendation refresh

## Motion rule

Motion must be minimal:

- duration 150–250ms
- no bouncing
- no excessive scroll animation
- respect content clarity

## Legal and privacy readability

Legal pages need:

- max width around `3xl`
- headings with spacing
- readable line height
- visible links
- dark mode support

Use `.tta-legal` from theme tokens.


## Component accessibility requirements added in v3

- Pagination uses `<nav aria-label="Pagination">` and `aria-current="page"` for the current page.
- Progress bars use `role="progressbar"`, `aria-valuemin`, `aria-valuemax`, and `aria-valuenow`, plus visible text such as `62% — Utilisable`.
- Avatar dropdown button uses `aria-haspopup="menu"` and `aria-expanded`.
- Mobile filter drawer must be keyboard closable with Escape and close on outside click.
- Skill filter remains a normal text input for MVP unless existing backend already supports multiple values.
