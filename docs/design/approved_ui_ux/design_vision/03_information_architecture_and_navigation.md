# 03 — Information Architecture and Navigation v3

## Public routes

| Route | Page | Primary role |
|---|---|---|
| `/` | Search-first homepage | Drive to jobs and CV analysis |
| `/jobs/` | Public job search | Main anonymous product page |
| `/jobs/<uuid:public_id>/` | Job detail | Job evaluation + apply/save/match |
| `/cv-checker/` | CV checker landing | Explain CV upload/recommendations |
| `/accounts/login/` | Login | Access account |
| `/accounts/signup/` | Signup | Create account |
| `/privacy/` | Privacy policy | Trust and compliance |
| `/terms/` | Terms | Legal limits |

## Private routes

| Route | Page | Primary role |
|---|---|---|
| `/dashboard/` | Dashboard home | Action center |
| `/dashboard/profile/` | Profile | Complete candidate profile |
| `/dashboard/cv/` | CV management | Upload/parse/replace/delete CV |
| `/dashboard/recommendations/` | Recommendations | Main private value page |
| `/dashboard/matches/` | Match history | Previous job analyses |
| `/dashboard/matches/<uuid:public_id>/` | Match detail | Score breakdown and actions |
| `/dashboard/saved-jobs/` | Saved jobs | Stored jobs |
| `/dashboard/email-preferences/` | Email preferences | Digest settings |
| `/dashboard/account/` | Security/account | Auth, linked accounts, privacy links, delete account |

## Anonymous top navigation

Desktop:

```text
Logo | Offres | Analyse CV | Comment ça marche | Connexion | Créer un compte
```

Rules:

- `Offres` → `/jobs/`
- `Analyse CV` → `/cv-checker/`
- `Comment ça marche` → homepage section anchor `/#comment-ca-marche`
- `Connexion` → `/accounts/login/`
- `Créer un compte` → `/accounts/signup/`

Mobile:

```text
Logo | Menu button
```

Mobile menu items:

```text
Offres
Analyse CV
Comment ça marche
Connexion
Créer un compte
```

## Authenticated top navigation

Desktop:

```text
Logo | Offres | Recommandations | CV | Profil | Favoris | Avatar dropdown
```

Minimum accepted if space is limited:

```text
Logo | Offres | Recommandations | Tableau de bord | Avatar dropdown
```

Avatar dropdown must include:

```text
Tableau de bord
Mon CV
Profil
Recommandations
Favoris
Compatibilités
Préférences emails
Sécurité & compte
Déconnexion
```

## Active state

Current nav item:

```html
class="text-brand-600 dark:text-brand-400 font-semibold"
```

Inactive nav item:

```html
class="text-slate-600 hover:text-slate-950 dark:text-slate-300 dark:hover:text-white"
```

## Navigation anti-patterns

Do not add:

- Employers
- Companies
- Pricing
- Blog
- Recruiter dashboard
- Training center dashboard

These are out of MVP scope.

## Footer

Footer should be compact.

Public/authenticated common footer:

```text
Logo
© 2026 TuniTech Abroad
Offres
Analyse CV
Confidentialité
CGU
```

Optional sentence:

```text
Conçu pour les talents IT tunisiens ciblant le marché français.
```

Do not overload footer with future features.

## Mobile information architecture

On mobile, priority order:

1. Search/jobs
2. Recommendations/CV if authenticated
3. Profile
4. Saved jobs
5. Settings/legal

The job filter panel must not permanently occupy the first screen on mobile. Use a drawer.


## Locked route decisions for implementation

- Account/security route is locked to `/dashboard/account/` because this is the current implemented route. Do not rename it to `/dashboard/settings/` during UI polish.
- The user-facing label for `/dashboard/account/` is `Sécurité & compte`.
- `Comment ça marche` links to `/#comment-ca-marche`, not to `/cv-checker/`. `/cv-checker/` remains exposed through `Analyse CV`.
- Match history user-facing label is `Compatibilités`, not `Analyses`, to avoid confusing CV analysis with job compatibility analysis.
