# 04 — Component Specification v3

This document defines reusable UI components for Django templates.

## 1. App shell

```html
<body class="tta-page">
  {% include "partials/navbar.html" %}
  <main>
    {% block content %}{% endblock %}
  </main>
  {% include "partials/footer.html" %}
</body>
```

Rules:

- Main content should not hide behind navbar.
- Prefer normal top navbar unless sticky behavior is already stable.
- Footer must stay compact.

## 2. Containers

| Use | Class |
|---|---|
| jobs/dashboard wide | `tta-container` |
| profile/CV/recommendations | `tta-container-narrow` |
| auth/legal/narrow forms | `tta-container-form` or `tta-legal` |

## 3. Buttons

### Primary

Use for one main action per section.

Examples:

- `Explorer les offres`
- `Analyser mon CV`
- `Postuler sur France Travail`
- `Lancer l’analyse`
- `Enregistrer`

Class: `tta-btn-primary`

### Secondary

Use for alternative actions.

Class: `tta-btn-secondary`

### Ghost

Use for low-emphasis actions.

Class: `tta-btn-ghost`

### Danger

Use only for destructive actions.

Class: `tta-btn-danger`

## 4. Cards

### Standard card

Use for normal content panels.

```html
<section class="tta-card p-5 md:p-6">
```

### Interactive card

Use for clickable cards.

```html
<a class="tta-card tta-card-hover block p-5 md:p-6" href="...">
```

### Nested card

Use inside larger cards.

```html
<div class="tta-card-muted p-4">
```

## 5. Job card variants

### Public job card

Content order:

1. title
2. company + location
3. contract/job/remote badges
4. skills
5. short description
6. freshness/status
7. actions

### Recommendation card

Must add:

- score badge
- why recommended
- missing skills
- risk flags

### Saved job card

Must add:

- saved state
- stale/expired label if applicable
- remove action

### Dashboard compact card

Must be smaller and show only:

- title
- score/status
- one CTA

## 6. Badges

| Use | Class |
|---|---|
| active/success | `tta-badge tta-badge-success` |
| warning/stale/partial | `tta-badge tta-badge-warning` |
| danger/failed/weak | `tta-badge tta-badge-danger` |
| brand/info | `tta-badge tta-badge-brand` |

Badge text must not be color-only. Always include readable label.

## 7. Score ring

Responsive size:

```html
<svg class="h-24 w-24 md:h-32 md:w-32" viewBox="0 0 120 120" aria-label="Score de compatibilité 72%">
```

Desktop: 128px. Mobile: 96px.

Color semantics:

| Score | Ring color |
|---:|---|
| 80–100 | emerald |
| 65–79 | brand/blue |
| 50–64 | amber |
| <50 | rose |

Never use score color without text label.

## 8. Mobile filter drawer

Use Alpine only for drawer open/close. Do not use `<details>` for the primary mobile filter UX.

Pattern:

```html
<div x-data="{ filtersOpen: false }">
  <button type="button" @click="filtersOpen = true" class="tta-btn-secondary w-full md:hidden">
    Filtres
  </button>

  <div x-show="filtersOpen" x-cloak @click="filtersOpen = false" class="fixed inset-0 z-50 bg-slate-950/50"></div>

  <aside
    x-show="filtersOpen"
    x-cloak
    x-transition:enter="transition ease-out duration-200"
    x-transition:enter-start="translate-x-full"
    x-transition:enter-end="translate-x-0"
    x-transition:leave="transition ease-in duration-150"
    x-transition:leave-start="translate-x-0"
    x-transition:leave-end="translate-x-full"
    class="fixed right-0 top-0 z-50 h-full w-80 max-w-[90vw] overflow-y-auto bg-white p-5 shadow-2xl dark:bg-slate-900 md:static md:block md:h-auto md:w-auto md:max-w-none md:translate-x-0 md:shadow-none"
  >
    <!-- filter fields -->
  </aside>
</div>
```

Preserve existing form method/action/fields.

## 9. CV dropzone

Structure:

```html
<div class="tta-dropzone" x-data="{ drag: false }" :class="{ 'dragover': drag }" @dragenter.prevent="drag = true" @dragover.prevent="drag = true" @dragleave.prevent="drag = false" @drop="drag = false">
  <p class="font-semibold">Parcourir ou glisser-déposer</p>
  <p class="tta-help">PDF uniquement, jusqu'à 5 Mo</p>
  {{ form.file }}
</div>
```

File input must remain functional and backend-compatible.

## 10. Empty state

All important empty states use:

- icon
- title
- short explanation
- one action

Pattern:

```html
<div class="tta-card p-8 text-center">
  <svg class="mx-auto h-14 w-14 text-slate-400 dark:text-slate-600" aria-hidden="true">...</svg>
  <h3 class="mt-4 text-lg font-semibold text-slate-950 dark:text-white">Aucune offre trouvée</h3>
  <p class="mt-2 text-sm text-slate-600 dark:text-slate-400">Essayez d'élargir vos filtres.</p>
  <div class="mt-6"><a class="tta-btn-secondary" href="/jobs/">Réinitialiser</a></div>
</div>
```

## 11. Alerts

| Type | Use |
|---|---|
| Success | parsed CV, profile ready, saved job |
| Warning | stale recommendation, incomplete profile, uncertain data |
| Danger | delete account, parse failed, invalid CV |
| Info | processing, explanation pending |

Alerts must include icon + label + body text.

## 12. Loading states

Use one of:

- disabled button with `Analyse en cours…`
- inline spinner
- skeleton card
- HTMX indicator

Never let the user click repeatedly without feedback.


## 15. Pagination

Use a reusable pagination component wherever lists span multiple pages: jobs, recommendations if paginated, saved jobs if paginated, match history.

Container:

```html
<nav class="tta-pagination" aria-label="Pagination">
  <a class="tta-page-link" href="...">Précédent</a>
  <a class="tta-page-number" href="...">1</a>
  <span class="tta-page-number is-active" aria-current="page">2</span>
  <a class="tta-page-number" href="...">3</a>
  <a class="tta-page-link" href="...">Suivant</a>
</nav>
```

CSS contract:

```css
.tta-pagination {
  @apply mt-8 flex flex-wrap items-center justify-center gap-2;
}
.tta-page-link,
.tta-page-number {
  @apply inline-flex min-h-10 min-w-10 items-center justify-center rounded-xl border border-slate-200 bg-white px-3 text-sm font-medium text-slate-700 transition hover:border-brand-300 hover:bg-brand-50 hover:text-brand-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300 dark:hover:border-brand-700 dark:hover:bg-brand-950/40 dark:hover:text-brand-300;
}
.tta-page-number.is-active {
  @apply border-brand-600 bg-brand-600 text-white hover:bg-brand-600 hover:text-white dark:border-brand-500 dark:bg-brand-500;
}
.tta-page-link[aria-disabled="true"],
.tta-page-number[aria-disabled="true"] {
  @apply pointer-events-none opacity-50;
}
```

Preserve existing query parameters when generating page links.

## 16. Progress bar

Use one progress component for profile completeness, score breakdown, CV status progression if needed.

```html
<div class="tta-progress" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="62">
  <div class="tta-progress-bar" style="width: 62%"></div>
</div>
```

CSS contract:

```css
.tta-progress {
  @apply h-2.5 w-full overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800;
}
.tta-progress-bar {
  @apply h-full rounded-full bg-brand-600 transition-all duration-300 dark:bg-brand-400;
}
.tta-progress-bar-success { @apply bg-emerald-600 dark:bg-emerald-400; }
.tta-progress-bar-warning { @apply bg-amber-500 dark:bg-amber-400; }
.tta-progress-bar-danger { @apply bg-rose-600 dark:bg-rose-400; }
```

Do not use color only. Always pair the progress bar with text such as `62% — Utilisable`.

## 17. Selects and skill filters

Native select is acceptable for MVP if styled consistently. No custom select library.

Class for normal selects:

```css
.tta-select {
  @apply min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm transition focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:focus:border-brand-400;
}
```

Skill filter decision:

- For `/jobs/`, use a single text input named `skill` for MVP, not a complex multi-select.
- Placeholder: `Python, Django, React...`
- If multiple skills are supported by existing backend, use comma-separated text and preserve current form parsing.
- Do not introduce tag-input JS or a new dependency in this redesign.

## 18. Avatar dropdown

Use Alpine only for open/close behavior. Preserve existing logout URL/form behavior.

```html
<div class="relative" x-data="{ open: false }" @keydown.escape.window="open = false">
  <button type="button" @click="open = !open" class="tta-avatar-button" :aria-expanded="open.toString()" aria-haspopup="menu">
    <span class="tta-avatar">{{ user_initial }}</span>
  </button>

  <div x-show="open" x-cloak @click.outside="open = false" x-transition class="tta-dropdown-menu" role="menu">
    <a class="tta-dropdown-item" href="{% url 'dashboard:home' %}">Tableau de bord</a>
    <a class="tta-dropdown-item" href="{% url 'dashboard:cv' %}">Mon CV</a>
    <a class="tta-dropdown-item" href="{% url 'dashboard:profile' %}">Profil</a>
    <a class="tta-dropdown-item" href="{% url 'dashboard:recommendations' %}">Recommandations</a>
    <a class="tta-dropdown-item" href="{% url 'dashboard:saved_jobs' %}">Favoris</a>
    <a class="tta-dropdown-item" href="{% url 'dashboard:matches' %}">Compatibilités</a>
    <a class="tta-dropdown-item" href="{% url 'dashboard:email_preferences' %}">Préférences emails</a>
    <a class="tta-dropdown-item" href="{% url 'dashboard:account' %}">Sécurité & compte</a>
    <!-- preserve existing allauth logout implementation -->
  </div>
</div>
```

CSS contract:

```css
.tta-avatar-button {
  @apply inline-flex items-center rounded-full focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2 dark:focus-visible:ring-offset-slate-950;
}
.tta-avatar {
  @apply inline-flex h-9 w-9 items-center justify-center rounded-full bg-brand-100 text-sm font-bold text-brand-700 dark:bg-brand-950 dark:text-brand-300;
}
.tta-dropdown-menu {
  @apply absolute right-0 z-40 mt-3 w-64 overflow-hidden rounded-2xl border border-slate-200 bg-white p-2 shadow-xl dark:border-slate-800 dark:bg-slate-900;
}
.tta-dropdown-item {
  @apply block rounded-xl px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 hover:text-slate-950 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white;
}
```

## 19. Cookie/privacy notice UI slot

Do not add a cookie banner blindly. If the production app uses only essential cookies for session, CSRF, authentication, and security, a marketing-style banner is unnecessary and harmful.

If non-essential analytics/marketing cookies are introduced later, use this UI slot:

```html
<div class="tta-cookie-banner" role="region" aria-label="Préférences cookies">
  <p>Nous utilisons des cookies essentiels au fonctionnement du service. Les cookies optionnels ne sont activés qu'avec votre accord.</p>
  <div class="flex gap-2">
    <button class="tta-btn-secondary">Refuser les cookies optionnels</button>
    <button class="tta-btn-primary">Accepter</button>
  </div>
</div>
```

No fake consent UI. Only implement this if there is actual non-essential cookie behavior to control.
