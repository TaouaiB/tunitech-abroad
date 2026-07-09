# TuniAtlas V16 UI Lock

## Status

**V16 is final.**

Do not improve it. Do not redesign it. Do not reinterpret it.

The implementation goal is exact visual and behavior parity with v16.

## Hard rules

Agents must not:

- add new pages
- add new sections
- add new cards
- add new helper text
- add marketing copy
- add philosophical explanations
- change colors
- change typography
- change layout direction
- change responsive behavior
- change desktop while fixing mobile
- change mobile while fixing desktop
- change brand wording
- invent states not present in v16
- redesign the dashboard
- introduce React/Vue/SPA behavior
- rewrite backend business logic
- modify scoring/matching/recommendation logic
- modify auth logic unless required by template wiring
- modify models/migrations without explicit approval

## Allowed work

Agents may:

- convert static v16 HTML into Django templates
- extract repeated markup into template components
- move CSS into controlled static CSS files
- move JS into controlled static JS files
- replace static sample data with Django variables
- wire existing backend actions with HTMX
- preserve existing security and auth behavior
- fix visual differences from v16

## Visual parity beats code elegance

If a refactor makes the code cleaner but changes visuals, reject the refactor.

## Source of truth

The prototype files under:

```text
/docs/ui/v16-final/
```

are the UI contract.

The implementation is done only when the real Django pages match v16 screenshots.
