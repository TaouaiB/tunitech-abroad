# UX Copy Rules for Job and Match Pages

## Product principle

Users should feel the platform understands jobs. They should not see parser/debug problems.

## Public job cards and job detail

Show:

- title
- company
- location
- contract
- remote/hybrid/on-site
- experience if available
- detected/enriched stack if available

If stack is missing, hide the stack section. Do not show:

```text
Aucune compétence spécifique n'est extraite.
```

Better alternatives:

```text
Voir les détails de l’offre
```

or no stack block at all.

## Logged-in recommendations

Use labels:

- Bon potentiel
- Potentiel moyen
- À vérifier
- Faible alignement
- Analyse limitée

Avoid making percentage the only headline. Percentage may be secondary when reliable.

## Match detail sections

Use:

```text
Pourquoi cette offre peut vous intéresser
Compétences déjà présentes
Compétences à renforcer
Points à vérifier
Conseil de candidature
```

Do not use:

```text
Points de vigilance
Signaux positifs
low confidence
non-IT
parser
```

## Limited analysis copy

For vague jobs:

```text
Analyse limitée
Cette offre ne donne pas assez de détails techniques pour comparer précisément votre profil. Consultez l’offre complète avant de postuler.
```

For enriched but unclear required/optional separation:

```text
À vérifier
L’offre mentionne des compétences techniques, mais ne distingue pas clairement les compétences obligatoires des compétences souhaitées.
```

For strong enrichment:

```text
Bon potentiel
Votre profil correspond à plusieurs compétences importantes de cette offre.
```

For poor alignment:

```text
Faible alignement
Cette offre demande plusieurs compétences absentes de votre profil actuel.
```
