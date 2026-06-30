# Design Brief — TuniTech Abroad UI/UX

## Product identity

TuniTech Abroad is not a generic job board.

It is a France-first job intelligence platform for Tunisian IT profiles.

The UI must communicate:

- France IT opportunities
- CV/profile intelligence
- realistic matching
- missing skill detection
- recommendations
- candidate progression

## Visual direction

Use a modern SaaS/career-tech style.

Preferred feeling:

- clean
- energetic
- confident
- youthful
- practical
- professional

Avoid:

- plain admin tables
- default Django form look
- generic blue-only corporate pages
- excessive gradients
- childish colors
- overloaded dashboards
- huge walls of text
- random inconsistent card styles

## Suggested visual system

Colors:

- deep navy / ink for text and headers
- bright blue or indigo for primary action
- emerald/green for positive states
- amber for warning/incomplete states
- red for danger/delete states
- light neutral backgrounds
- soft borders/shadows

Typography:

- strong page headings
- short explanatory subtitles
- readable form labels
- clear badges and chips
- no tiny unreadable metadata

Layout:

- max-width containers
- responsive grids
- cards for grouped content
- sidebar or top nav only if clean and mobile-friendly
- generous spacing
- visible call-to-action hierarchy

## French-first copy

Default UI copy should be French.

Allowed English:

- technical skill names
- job titles from source data
- GitHub / LinkedIn
- API/provider names only in internal/admin contexts

Examples:

- `Explorer les offres`
- `Analyser mon CV`
- `Voir ma compatibilité`
- `Compétences manquantes`
- `Recommandations`
- `Compléter mon profil`
- `Offres sauvegardées`
- `Historique des matchs`
- `Profil incomplet`
- `CV analysé avec avertissements`

## Key UX principles

1. Every empty state must tell the user what to do next.
2. Every loading state must finish or show a clear fallback.
3. Every score must explain why.
4. Every form must be grouped and readable.
5. Every dashboard card must lead to a next action.
6. Job cards must be scannable.
7. CV page must not leak private files or raw text.
8. Recommendations must not look stuck.
9. Quick match must feel fast and clean.
10. Mobile must not break core pages.
