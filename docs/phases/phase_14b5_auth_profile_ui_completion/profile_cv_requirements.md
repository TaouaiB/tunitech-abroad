# Profile, CV, and Recommendation Truth Requirements

## Remove target country from UI

This MVP is France-only. Do not show `target_country` in profile UI, CV extracted summary, onboarding, or recommendation blocker copy.

Allowed:

- Internally default France for matching/search if existing code requires it.
- Keep the DB field for now.

Forbidden:

- Asking the user to select target country.
- Showing `Pays cible: France` as a profile completion field.
- Inferring target country from CV text and displaying it as user preference.

## Career level wording

Replace unclear `Current level` with:

```text
Niveau de carrière
```

Helper text:

```text
Exemples : étudiant, stagiaire/PFE, junior, confirmé, senior.
```

If inferred from CV:

- `Junior Full Stack Developer` -> `junior`
- `Intern`, `Stage`, `PFE` -> `internship`/valid project choice
- If ambiguous, leave blank and ask the user.

## Years experience

Replace `Years experience` with:

```text
Années d’expérience
```

Rules:

- Extract only when reliable enough.
- If not reliable, leave blank and show `À compléter manuellement`.
- Do not hallucinate exact years.
- Do not make recommendations impossible only because this field is blank if the career level is present and skills/roles exist, unless existing product decision requires it. If it blocks, the blocked reason must be exact and honest.

## Phone/location issue

The page must never say phone or location is missing if the database profile has non-empty values.

Use one source of truth:

```text
ProfileCompletenessService.get_missing_fields(profile)
```

or equivalent. The same service must power:

- profile missing banner
- recommendation blocked reason
- dashboard profile completeness card
- tests

## CV parse reapply/sync

After CV parse:

- extracted phone fills profile phone if empty
- extracted location fills profile location if empty
- extracted LinkedIn/GitHub/portfolio fills profile links if empty
- invalid stale CV-derived website URL like `https://Next.js` is cleaned/replaced
- profile completion recalculates after save
- UI shows applied values and detected-but-not-applied values

## Recommendation states

Recommendation page must distinguish:

1. profile incomplete
2. no active jobs
3. generation failed
4. recommendations stale
5. recommendations ready
6. no compatible jobs after scoring

Do not use `Aucune offre ne correspond` when the real reason is incomplete profile.

## Tests required

- Profile DB has phone/location -> missing fields must not include phone/location.
- Profile DB lacks only years -> missing fields contains only years, if years is required.
- Same missing fields appear on profile page and recommendations page.
- CV parse fills empty phone/location/link fields.
- Target country is not rendered in profile/CV/recommendation templates.
