# Phase 15G Scoring Policy

## Final score composition

Location must not affect final score for TuniTech Abroad.

Reason:

- The product is built for Tunisian/foreign candidates targeting France.
- Penalizing a Tunisian profile because the job is in France hurts the core product audience.
- Mobility, visa, alternance/PFE, and remote status are important context, but not fit-score components.

## Required scoring behavior

Final score should be calculated from:

```text
technical score
experience score
language score
role/title score
```

Location/mobility should be displayed separately as contextual guidance.

## Do not fake location

Do not set location to `100%` to avoid penalty. That hides useful context and creates fake precision.

Better:

```text
Location/mobility is informational only and excluded from score.
```

## Tests

At minimum:

- Same candidate/job with location score 0, 55, and 100 should produce the same final score if all other dimensions are equal.
- Match detail should not show a scored `Localisation` bar if location is no longer part of final score.
- A mobility/contract note should still be visible.
