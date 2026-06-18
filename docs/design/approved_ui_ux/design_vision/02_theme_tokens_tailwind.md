# 02 — Theme Tokens and Tailwind Strategy v3

## Theme decision

Use Tailwind `darkMode: "media"`.

This follows the system preference and avoids manual theme-state complexity.

```js
module.exports = {
  darkMode: "media",
  content: [
    "./templates/**/*.html",
    "./apps/**/*.py",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eff6ff",
          100: "#dbeafe",
          200: "#bfdbfe",
          300: "#93c5fd",
          400: "#60a5fa",
          500: "#3b82f6",
          600: "#2563eb",
          700: "#1d4ed8",
          800: "#1e40af",
          900: "#1e3a8a",
          950: "#172554",
        },
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "sans-serif"],
      },
    },
  },
  plugins: [],
}
```

No manual toggle in this design specification.

## Dependency rule

Do not add UI dependencies for this redesign.

Forbidden for Phase 14K unless separately approved:

- `django-widget-tweaks`
- `django-crispy-forms`
- `@tailwindcss/typography`
- new JavaScript UI libraries
- React/Vue/Next components

## Required app.css component layer

Use `static/src/css/app.css` and `@layer components` for repeated patterns.

### Base shell

```css
@layer components {
  .tta-page {
    @apply min-h-screen bg-slate-50 text-slate-950 antialiased dark:bg-slate-950 dark:text-slate-50;
  }

  .tta-container {
    @apply mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8;
  }

  .tta-container-narrow {
    @apply mx-auto w-full max-w-5xl px-4 sm:px-6 lg:px-8;
  }

  .tta-container-form {
    @apply mx-auto w-full max-w-3xl px-4 sm:px-6 lg:px-8;
  }
}
```

### Cards

```css
@layer components {
  .tta-card {
    @apply rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900;
  }

  .tta-card-muted {
    @apply rounded-2xl border border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-slate-800/60;
  }

  .tta-card-hover {
    @apply cursor-pointer transition-all duration-200 hover:-translate-y-1 hover:border-brand-300 hover:shadow-xl focus-within:border-brand-300 dark:hover:border-brand-700 dark:hover:shadow-none;
  }
}
```

### Buttons

```css
@layer components {
  .tta-btn-primary {
    @apply inline-flex min-h-11 items-center justify-center gap-2 rounded-xl bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-brand-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-brand-500 dark:hover:bg-brand-400 dark:focus-visible:ring-offset-slate-950;
  }

  .tta-btn-secondary {
    @apply inline-flex min-h-11 items-center justify-center gap-2 rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-800 shadow-sm transition hover:border-brand-300 hover:bg-brand-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:hover:border-brand-700 dark:hover:bg-slate-800 dark:focus-visible:ring-offset-slate-950;
  }

  .tta-btn-ghost {
    @apply inline-flex min-h-11 items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2 dark:text-slate-300 dark:hover:bg-slate-800 dark:focus-visible:ring-offset-slate-950;
  }

  .tta-btn-danger {
    @apply inline-flex min-h-11 items-center justify-center gap-2 rounded-xl bg-rose-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-rose-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-500 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60 dark:focus-visible:ring-offset-slate-950;
  }
}
```

### Forms

```css
@layer components {
  .tta-label {
    @apply mb-1.5 block text-sm font-medium text-slate-800 dark:text-slate-200;
  }

  .tta-input {
    @apply block min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-950 shadow-sm placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:placeholder:text-slate-500;
  }

  .tta-help {
    @apply mt-1.5 text-xs leading-relaxed text-slate-500 dark:text-slate-400;
  }

  .tta-error {
    @apply mt-1.5 text-xs font-medium text-rose-600 dark:text-rose-400;
  }
}
```

### Badges and chips

```css
@layer components {
  .tta-badge {
    @apply inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium;
  }

  .tta-badge-brand {
    @apply bg-brand-50 text-brand-700 ring-1 ring-brand-200 dark:bg-brand-950/40 dark:text-brand-300 dark:ring-brand-900;
  }

  .tta-badge-success {
    @apply bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200 dark:bg-emerald-950/30 dark:text-emerald-300 dark:ring-emerald-900;
  }

  .tta-badge-warning {
    @apply bg-amber-50 text-amber-800 ring-1 ring-amber-200 dark:bg-amber-950/30 dark:text-amber-300 dark:ring-amber-900;
  }

  .tta-badge-danger {
    @apply bg-rose-50 text-rose-700 ring-1 ring-rose-200 dark:bg-rose-950/30 dark:text-rose-300 dark:ring-rose-900;
  }

  .tta-chip {
    @apply inline-flex items-center gap-1 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300;
  }
}
```

### Homepage hero

```css
@layer components {
  .tta-hero {
    @apply flex min-h-[68vh] flex-col justify-center py-10 md:min-h-[72vh] md:py-14;
  }
}
```

Do not use `80vh`; it wastes vertical space for a job-search product.

### Legal content

```css
@layer components {
  .tta-legal {
    @apply mx-auto max-w-3xl px-4 py-8 md:py-12;
  }
  .tta-legal h1 {
    @apply border-b border-slate-200 pb-4 text-3xl font-bold tracking-tight text-slate-950 dark:border-slate-800 dark:text-white md:text-4xl;
  }
  .tta-legal h2 {
    @apply mt-8 mb-3 text-xl font-semibold text-slate-900 dark:text-slate-100 md:text-2xl;
  }
  .tta-legal p {
    @apply my-4 text-sm leading-relaxed text-slate-700 dark:text-slate-300 md:text-base;
  }
  .tta-legal ul {
    @apply my-4 list-disc space-y-1 pl-6 text-sm text-slate-700 dark:text-slate-300 md:text-base;
  }
  .tta-legal a {
    @apply text-brand-600 underline underline-offset-2 hover:text-brand-800 dark:text-brand-400 dark:hover:text-brand-300;
  }
}
```

### CV dropzone

```css
@layer components {
  .tta-dropzone {
    @apply rounded-2xl border-2 border-dashed border-slate-300 bg-slate-50 p-8 text-center transition-colors duration-200 dark:border-slate-700 dark:bg-slate-800/40;
  }
  .tta-dropzone:hover,
  .tta-dropzone.dragover {
    @apply border-brand-500 bg-brand-50/60 dark:bg-brand-950/30;
  }
}
```

### Sticky mobile save bar

```css
@layer components {
  .tta-mobile-savebar {
    @apply sticky bottom-0 z-30 -mx-4 border-t border-slate-200 bg-white/85 p-4 backdrop-blur-sm dark:border-slate-800 dark:bg-slate-950/85 md:static md:mx-0 md:border-0 md:bg-transparent md:p-0 md:backdrop-blur-0;
  }
}
```

## Component state matrix

Every component must support these states:

| State | Required behavior |
|---|---|
| default | clear baseline design |
| hover | visible but not childish |
| focus-visible | ring for keyboard users |
| active/current | selected nav/filter state visible |
| disabled | reduced opacity, no pointer |
| loading | spinner/skeleton or disabled CTA text |
| empty | illustrated empty state with action |
| error | nearby message and semantic color |
| success | confirmation state |
| dark mode | not an afterthought |
