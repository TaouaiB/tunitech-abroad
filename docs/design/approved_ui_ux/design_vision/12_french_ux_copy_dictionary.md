# 12 — French UX Copy Dictionary v3

Use this to keep the UI consistent.

## Navigation

| Concept | French label |
|---|---|
| Jobs | Offres |
| Job search | Recherche d'offres |
| Dashboard | Tableau de bord |
| Recommendations | Recommandations |
| Saved jobs | Favoris |
| CV | Mon CV |
| Profile | Profil |
| Match history | Compatibilités |
| Settings | Sécurité & compte |
| Email preferences | Préférences emails |
| Login | Connexion |
| Signup | Créer un compte |
| Logout | Déconnexion |

## Buttons

| Action | Label |
|---|---|
| View jobs | Explorer les offres |
| Search | Rechercher |
| View job | Voir l'offre |
| Apply | Postuler |
| Apply on source | Postuler sur la source |
| Apply on France Travail | Postuler sur France Travail |
| Save job | Sauvegarder |
| Saved | Sauvegardée |
| Remove saved | Retirer |
| Analyze CV | Analyser mon CV |
| Upload CV | Ajouter mon CV |
| Replace CV | Remplacer le CV |
| Delete CV | Supprimer le CV |
| Complete profile | Compléter mon profil |
| Save | Enregistrer |
| Save profile | Enregistrer le profil |
| Reset filters | Réinitialiser |
| Apply filters | Appliquer les filtres |
| Login | Se connecter |
| Signup | S'inscrire |
| Continue with Google | Continuer avec Google |
| Continue with GitHub | Continuer avec GitHub |
| Generate explanation | Générer une explication |
| View compatibility | Voir la compatibilité |
| Start full compatibility | Vérifier ma compatibilité |
| Quick match | Test rapide |
| Back to dashboard | Retour au tableau de bord |
| Back to jobs | Retour aux offres |

## Auth labels

| English/mixed | French |
|---|---|
| Email address | Adresse email |
| Password | Mot de passe |
| Password again | Confirmer le mot de passe |
| Remember Me | Se souvenir de moi |
| Forgot password? | Mot de passe oublié ? |
| New here? | Nouveau sur TuniTech ? |
| Already have an account? | Vous avez déjà un compte ? |

## Job labels

| Internal | French |
|---|---|
| active | Active |
| stale | À vérifier |
| expired | Expirée |
| removed | Retirée |
| archived | Archivée |
| remote | Télétravail |
| hybrid | Hybride |
| on_site | Présentiel |
| unknown | Non précisé |
| internship | Stage |
| apprenticeship | Alternance |
| full_time_job | Emploi temps plein |
| contract | Mission / Contrat |
| junior | Junior |
| mid_level | Confirmé |
| senior | Senior |

## Match score labels

| Score range | French label |
|---|---|
| 80–100 | Très bon match |
| 65–79 | Bon potentiel |
| 50–64 | Match partiel |
| below 50 | Match faible |

## Match sections

| Concept | French label |
|---|---|
| Strong skills | Points forts |
| Missing required skills | Compétences requises manquantes |
| Missing optional skills | Compétences optionnelles à renforcer |
| Risk flags | Points de vigilance |
| Recommended actions | Actions recommandées |
| Technical score | Technique |
| Experience score | Expérience |
| Role title score | Rôle/titre |
| Language score | Langues |
| Location score | Localisation |

## CV labels

| Concept | French label |
|---|---|
| Active CV | CV actif |
| CV processing | Analyse du CV en cours |
| Parsed | Analyse terminée |
| Parsed with warnings | Analyse terminée avec avertissements |
| Failed | Analyse échouée |
| Upload date | Ajouté le |
| Parsed date | Analysé le |
| Extracted data | Données extraites |
| Private file | Fichier privé |

## Empty states

| Page | Title | Body |
|---|---|---|
| Jobs | Aucune offre trouvée | Essayez d'élargir vos filtres ou de chercher une autre technologie. |
| Recommendations | Aucune recommandation disponible | Ajoutez un CV ou complétez votre profil pour recevoir des offres adaptées. |
| Saved jobs | Aucune offre sauvegardée | Sauvegardez les offres intéressantes pour les comparer plus tard. |
| CV | Aucun CV actif | Ajoutez votre CV PDF pour lancer l'analyse de compatibilité. |
| Matches | Aucune analyse pour le moment | Lancez une analyse depuis une offre pour voir votre score détaillé. |

## Avoid

Avoid mixed labels:

- `Password`
- `Password again`
- `Remember Me`
- `Missing Skills`
- `Nice to have`
- `Quick Match`
- `Match`

Preferred replacements:

- `Mot de passe`
- `Confirmer le mot de passe`
- `Se souvenir de moi`
- `Compétences manquantes` used alone
- `Un plus` when the concept is required missing skills
- `Analyse rapide` for quick match
- `Analyse` when it is unclear whether it means CV parsing or job compatibility


## Canonical concept rules

Use these labels consistently across all pages:

| Concept | Canonical label | Forbidden drift |
|---|---|---|
| Missing required skills | Compétences requises manquantes | Compétences manquantes / À renforcer |
| Missing optional skills | Compétences optionnelles à renforcer | Nice to have / Un plus as a section title |
| Risk flags | Points de vigilance | Attention |
| Job compatibility detail | Compatibilité détaillée | Analyse when ambiguous |
| Match history | Compatibilités | Analyses |
| Anonymous quick match | Test rapide | Quick Match / Analyse rapide |
| CV parsing | Analyse du CV | Compatibilité CV |

Source-apply copy:

- Default generic label: `Postuler sur la source`.
- France Travail-specific label may be used only when `source_name` is France Travail: `Postuler sur France Travail`.
- Do not hardcode France Travail copy inside reusable components that may later render another source.
