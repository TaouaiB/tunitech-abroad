# Confidence Mapping Rules

This file is mandatory. The implementer and verifier must use this exact mapping.

Phase 14C uses three related concepts:

1. **IT classification confidence**: how sure we are the job belongs to an IT family.
2. **Skill signal quality**: how useful the extracted technical skills are for matching.
3. **Match confidence**: what the user sees on match/recommendation pages.

Do not infer a different mapping in code or tests.

## Canonical states

### IT classification confidence

```text
high
medium
low
excluded
```

Use `excluded` when the job is non-IT or should not be matched as an IT opportunity.

### Skill signal quality

```text
unknown
strong
partial
generic_only
missing
excluded_non_it
```

`unknown` is allowed only as a pre-computation/default storage value. It must be converted to one of the other states before recommendation/match display.

Meaning:

- `strong`: specific required technical stack exists, such as Java, C#, Python, React, Salesforce, SQL Server, Kubernetes.
- `partial`: specific technical stack exists, but mostly optional/detected or not clearly required.
- `generic_only`: only generic France Travail labels exist, such as “Application web” or “Concevoir une application web”.
- `missing`: job appears IT-like, but no useful technical stack was extracted.
- `excluded_non_it`: non-IT job, sales/commercial/photography/insurance/etc.

### Match confidence

```text
reliable
low_confidence
unavailable
```

## Required mapping table

| IT classification | Skill signal quality | Match confidence | User-facing behavior |
| --- | --- | --- | --- |
| excluded | any | unavailable | Hide normal score. Show “Offre non IT ou non comparable”. Exclude from recommendations. |
| any | excluded_non_it | unavailable | Hide normal score. Exclude from recommendations. |
| high/medium | strong | reliable | Show normal score and component bars. |
| high/medium | partial with required technical skills | reliable | Show normal score, but mention detected/optional context where useful. |
| high/medium | partial without required technical skills | low_confidence | Show score as “estimation faible confiance”; show detected skills; required skills = “non précisées”. |
| high/medium | generic_only | low_confidence | Show low-confidence label; do not present generic FT labels as stack requirements. |
| high/medium | missing | low_confidence only if description/ROME strongly proves IT context; otherwise unavailable | Show missing extraction warning. Do not say candidate has all required skills. |
| low | strong/partial | low_confidence | Show low-confidence label. Rank after reliable matches. |
| low | generic_only/missing | unavailable | Hide normal score. Do not recommend. |
| unknown | any | unavailable until computed | Do not display as a normal match. |

## Required examples

| Case | Classification | Skill signal quality | Match confidence |
| --- | --- | --- | --- |
| Data Scientist with Python/Machine Learning/Pandas but no required skills | data_ai_bi, high/medium | partial | low_confidence |
| Web Developer with no extracted skills and generic description only | low_confidence_it or unknown, low | missing | unavailable |
| Photography seller / `développeur-vendeur` | non_it, excluded | excluded_non_it | unavailable |
| Real Java/Spring/Angular job with specific skills | software/web_mobile, high | strong | reliable |
| Generic FT “Application web” only | web_mobile, medium/low | generic_only | low_confidence or unavailable depending description strength; never reliable |

## Ranking rule

Recommendations must rank:

```text
reliable first
low_confidence after reliable
unavailable excluded
```

## UI rule

Do not show raw states directly without labels. Use French display labels:

- `reliable` => “Match fiable”
- `low_confidence` => “Estimation faible confiance”
- `unavailable` => “Données insuffisantes”
- `strong` => “Signal technique fort”
- `partial` => “Signal technique partiel”
- `generic_only` => “Signal France Travail générique”
- `missing` => “Compétences techniques non détectées”
- `excluded_non_it` => “Offre non IT”
