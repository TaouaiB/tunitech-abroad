# 08 — Forms, Auth, CV, and Profile UX Spec v3

## General form rules

### Labels

Labels must be visible. Do not rely only on placeholders.

Good:

```text
Email
[input placeholder="votre.email@example.com"]
```

Bad:

```text
[input placeholder="Email"]
```

### Field help

Use muted helper text under complex fields.

Example:

```text
Niveau de français
Utilisé pour détecter les risques sur les offres demandant le français.
```

### Errors

Show errors close to fields:

```text
Ce champ est obligatoire.
```

Global errors appear at top of form card.

### Required fields

Use subtle required mark:

```text
Nom complet *
```

Avoid loud red stars everywhere.

## Form layout

### Short forms

Login/signup:

```text
single column
max width 420–480px
comfortable vertical spacing
```

### Long forms

Profile:

```text
sectioned form
2-column fields on desktop
1-column on mobile
sticky mobile save bar
```

## Login page

### Desktop layout

```text
Left panel: value proposition
Right panel: login form
```

### Mobile layout

```text
Logo/header
Login card
```

### Required elements

- email
- password
- remember me
- forgot password
- submit
- Google login
- GitHub login
- signup link

### French labels

| Current/mixed | Correct |
|---|---|
| Password | Mot de passe |
| Remember Me | Se souvenir de moi |
| Forgot password? | Mot de passe oublié ? |
| Continue with Google | Continuer avec Google |
| Continue with GitHub | Continuer avec GitHub |

## Signup page

Required elements:

- email
- password
- password confirmation
- terms/privacy acknowledgement copy
- Google signup
- GitHub signup
- login link

Do not ask for CV upload inside signup. CV upload belongs after authentication in `/dashboard/cv/`.

## Auth left panel

Desktop only.

Visual direction:

- subtle gradient
- abstract SVG lines/dots
- no stock photo
- no flags

Copy:

```text
France IT,
profil tunisien.
Analysez votre compatibilité sans rendre public votre CV.
```

## CV upload form

### Required structure

```text
Upload card
  Dropzone
  File rules
  Consent checkbox
  Submit button
```

### Consent copy

```text
J'accepte que mon CV soit analysé pour extraire mes compétences et calculer mes scores de compatibilité avec les offres françaises. Mon CV ne sera jamais rendu public.
```

### Dropzone states

| State | Visual |
|---|---|
| default | dashed neutral border |
| hover | brand border |
| dragover | brand border + brand background tint |
| invalid | rose border + error message |
| uploading | disabled submit/loading text |

## Profile form

### Sections

1. Identité
2. Liens professionnels
3. Objectif France
4. Expérience
5. Langues
6. Préférences
7. Compétences

### Sticky save

Mobile:

```text
bottom sticky save bar
```

Desktop:

```text
save button at bottom and optionally in header
```

### Completeness display

Always show current score and status near top.

Status labels:

| Internal | French |
|---|---|
| incomplete | Incomplet |
| usable | Utilisable |
| strong | Fort |

## Form styling implementation rule

Do not install form styling dependencies for this redesign.

Allowed approaches:

- preserve existing JS class injection if already used
- improve wrapper HTML around Django fields
- add reusable CSS component classes
- update forms later in a separate cleanup phase if needed

Do not break `{{ field }}`, `{{ form }}`, CSRF, form actions, file upload enctype, allauth provider tags.
