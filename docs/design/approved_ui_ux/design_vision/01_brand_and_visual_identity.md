# 01 — Brand and Visual Identity v3

## Brand personality

TuniTech Abroad should feel:

- serious
- modern
- precise
- trustworthy
- youth-friendly
- France/Tunisia focused
- technical but not cold

It should not feel:

- childish
- generic Bootstrap
- corporate HR portal
- crypto/SaaS hype
- black-only AI landing page
- university admin system

## Visual metaphor

The product is a bridge:

```text
Tunisian IT profile → France IT opportunities → fit intelligence → action plan
```

Use subtle visual language:

- lines/paths
- score rings
- skill chips
- recommendation cards
- progress states
- France-focused badges
- CV security indicators
- abstract connection patterns

Avoid tourist flags, stock photos, Eiffel Tower clichés, and decorative overload.

## Logo treatment

Current logo:

```text
[briefcase icon] TuniTech Abroad
```

Keep the concept. Improve consistency:

- icon size: 28–32px desktop, 24px mobile
- text weight: `font-bold`
- `TuniTech` in brand blue
- `Abroad` in neutral text
- icon uses brand blue
- no complex new logo in this phase

## Color system

Primary brand: deep professional blue.

Use this palette as the Tailwind `brand` scale:

| Token | Hex | Use |
|---|---|---|
| `brand-50` | `#eff6ff` | light backgrounds, chips |
| `brand-100` | `#dbeafe` | active light surfaces |
| `brand-200` | `#bfdbfe` | light borders |
| `brand-300` | `#93c5fd` | hover border |
| `brand-400` | `#60a5fa` | dark-mode text accent |
| `brand-500` | `#3b82f6` | secondary action/accent |
| `brand-600` | `#2563eb` | primary buttons, links |
| `brand-700` | `#1d4ed8` | primary hover |
| `brand-800` | `#1e40af` | deep surfaces |
| `brand-900` | `#1e3a8a` | dark accents |
| `brand-950` | `#172554` | deepest dark accent |

Neutral system:

- use Tailwind `slate` for text/background/borders
- page light background: `slate-50`
- card light: `white`
- nested light: `slate-50`
- page dark: `slate-950`
- card dark: `slate-900`
- nested dark: `slate-800/60`

Semantic colors:

| Semantic | Tailwind | Use |
|---|---|---|
| Success | `emerald` | strong score, active, parsed, saved success |
| Warning | `amber` | stale, partial, attention |
| Danger | `rose` | delete, failed, weak risk |
| Info | `sky` or `brand` | neutral information |

## Typography

Decision: system font stack first.

CSS:

```css
font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
```

Do not require Google Fonts by default.

Options:

1. Use system stack now.
2. Self-host Inter later if exact typography is required.
3. Avoid Google Fonts unless explicitly approved for privacy/performance tradeoff.

## Typography scale

| Element | Classes |
|---|---|
| Hero H1 | `text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight` |
| Page H1 | `text-3xl md:text-4xl font-bold tracking-tight` |
| Section H2 | `text-2xl md:text-3xl font-bold tracking-tight` |
| Card title | `text-lg md:text-xl font-semibold` |
| Body | `text-sm md:text-base leading-relaxed` |
| Muted body | `text-sm text-slate-600 dark:text-slate-400` |
| Badge | `text-xs font-medium` |

## Shape system

| Component | Radius |
|---|---|
| Page sections | `rounded-3xl` where needed |
| Cards | `rounded-2xl` |
| Buttons | `rounded-xl` |
| Inputs/selects | `rounded-xl` |
| Badges/chips | `rounded-full` |
| Avatar | `rounded-full` |
| Dropzone | `rounded-2xl` |

## Shadow system

| Level | Classes | Use |
|---|---|---|
| Base | `shadow-sm` | normal cards |
| Interactive | `hover:shadow-xl` | clickable cards |
| Overlay | `shadow-2xl` | mobile drawer/dropdown |

Dark mode shadows should be restrained. Use border contrast more than heavy shadows.
