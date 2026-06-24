# 00 — Product UX Principles v3

## 1. Jobs are the public front door

Anonymous users should not be forced to read long marketing content before seeing jobs.

Primary anonymous flow:

```text
Home or /jobs
→ Search/filter jobs
→ Open job detail
→ Test rapide
→ Signup/login
→ Upload CV
→ Confirm profile
→ Full match/recommendations
```

Homepage exists, but it behaves as a **search gateway**, not as a brochure.

## 2. Authenticated users need next action, not decoration

Authenticated users should not wonder what to do.

Dashboard next-action priority:

```text
No CV
→ Add CV

CV parsing
→ Show parsing state

Profile incomplete
→ Complete profile

Profile usable + recommendations missing/stale
→ Generate or view recommendations

Recommendations available
→ Review recommended jobs
```

## 3. Recommendations are the private value page

Recommendations must not look like a simple list of jobs.

Each recommendation card must show:

- job title, company, location
- fit score and label
- why this job appears
- matched skills
- missing required skills
- risk flags
- freshness status
- save/apply/detail actions

A recommendation without a reason is generic. Generic is not the product.

## 4. Match score must be explainable and humane

Never show only a raw percentage.

Bad:

```text
46%
```

Good:

```text
46% — Match faible
Blocage principal : compétences techniques insuffisantes.
Priorité : renforcer les compétences requises avant de postuler.
```

Score labels:

| Score | Label | Tone |
|---:|---|---|
| 80–100 | Très bon match | confident |
| 65–79 | Bon potentiel | encouraging but realistic |
| 50–64 | Match partiel | cautious |
| < 50 | Match faible | direct, not humiliating |

## 5. Dark mode is adaptive, not a style gimmick

The site follows the user’s system theme.

- Light OS/browser → light UI.
- Dark OS/browser → dark UI.
- No forced black site.
- No manual toggle in this redesign.

## 6. Youth-friendly means fast and understandable

Youth-friendly does not mean cartoonish.

It means:

- fast scanning
- simple labels
- clear CTAs
- useful badges
- direct feedback
- mobile usability
- no corporate HR clutter

## 7. Every page must answer one question

| Page | User question answered |
|---|---|
| `/` | Can this help me find France IT jobs? |
| `/jobs/` | What jobs are available? |
| `/jobs/<public_id>/` | Is this job worth opening/applying? |
| quick match | Do I roughly fit this job? |
| `/dashboard/` | What should I do next? |
| `/dashboard/cv/` | Is my CV uploaded/parsed/private? |
| `/dashboard/profile/` | Is my profile ready? |
| `/dashboard/recommendations/` | Which jobs are realistic for me? |
| `/dashboard/matches/<public_id>/` | Why did I get this score and what should I fix? |

## 8. Do not hide data quality problems

If classification is uncertain, show `Non précisé` or `À vérifier`.

Do not make wrong data look confident. Example: a job cannot visually appear as both `CDI` and `Internship` without a warning or correction. UI must expose uncertainty clearly.
