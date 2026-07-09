# Observed Issues

## Manual QA examples

### `[DEMO] Data Scientist Junior (H/F)`

Database proof showed:

```text
OPTIONAL_JSON = ['Python', 'Machine Learning']
JOB_SKILLS = Python, Machine Learning, Pandas
TECH_SKILL_COUNT = 3
IT_RELEVANT = True
```

But the match page still communicated “no required technical skills extracted” in a way that looked like no technical data existed at all.

Correct UX:

```text
Compétences techniques détectées : Python, Machine Learning, Pandas
Compétences obligatoires : non précisées par l’offre
Match : estimation faible confiance / partielle
```

### `Web Developer — Proof Corp`

Database proof showed:

```text
REQUIRED_JSON = []
OPTIONAL_JSON = []
JOB_SKILLS = []
DESCRIPTION = General web project coordination without extracted requirements.
IT_RELEVANT = False
```

Correct UX:

```text
Données insuffisantes pour calculer un match fiable
```

No normal score bars.

### `Développeur-vendeur/Développeuse-vendeuse en photographie`

Raw France Travail payload shows photography/sales role, ROME not IT development, and skills such as sales, photo processing, transaction, product/service presentation.

Correct behavior:

```text
Matching indisponible
Offre probablement non IT
Not recommended
```

## Root cause categories

1. France Travail `competences[]` are often generic.
2. Real stack appears in `description`, not always in `competences[]`.
3. Job classification was developer-centric.
4. Match UI did not separate reliable match from weak job data.
5. Skill extraction needs broad IT taxonomy, not only web/dev keywords.
