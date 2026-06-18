# 10 — Backend Safety and Template Guardrails v3

This design must not break the working Django application.

## Non-negotiable preservation list

During UI implementation, preserve:

- `{% csrf_token %}`
- all form `method`
- all form `action`
- all file upload `enctype="multipart/form-data"`
- all `hx-*` attributes
- all `public_id` URL variables
- all Django `{% url %}` names unless route is intentionally verified
- all allauth provider tags
- all permission/owner checks in views
- all hidden form fields
- all pagination query params
- all current POST redirect behavior
- all HTMX partial targets/swaps
- all CV privacy flows

## Public IDs

Never change:

```html
{% url 'jobs:detail' job.public_id %}
```

into:

```html
{% url 'jobs:detail' job.id %}
```

Never expose internal integer IDs in public routes.

## HTMX preservation

If a template has:

```html
hx-post
hx-get
hx-target
hx-swap
hx-trigger
hx-indicator
```

it must be copied into the redesigned element or preserved in a wrapper.

Danger areas:

- save/unsave job
- quick match form/result
- CV parse status polling
- recommendation refresh status
- match explanation generation
- email preference toggles

## Forms

Do not break:

- Django form fields
- file inputs
- allauth provider buttons
- form errors
- hidden fields
- CSRF
- POST redirect flow

If styling forms, keep the original field rendering connected to backend validation.

## CV privacy

UI must not expose:

- CV file URL publicly
- raw CV text
- hidden personal data in public templates
- deleted CVs

CV privacy line should be visible on CV page:

```text
Fichier chiffré et privé. Non partagé avec les employeurs.
```

## No backend product changes in UI phase

Do not implement:

- new models
- new services
- new LLM features
- new France Travail calls
- employer/recruiter features
- payments
- new matching algorithm
- auto-apply
- chatbot

## No dependency creep

Do not install:

- React/Next/Vue/Angular
- shadcn or SPA component libraries
- `django-crispy-forms`
- `django-widget-tweaks`
- typography plugin
- chart libraries

Score rings can be SVG/CSS. Empty icons can be inline SVG/Heroicons.

## Template migration rule

When redesigning a template:

1. Copy current template.
2. Identify backend-critical tags.
3. Redesign wrapper/layout/classes.
4. Preserve all backend-critical tags.
5. Run page-level tests.
6. Run full test suite.

## Visual cleanup cannot hide backend errors

If a form has validation errors, show them.
If a job has missing data, show fallback text.
If recommendations are stale, show stale state.
If CV parse fails, show failed state.


## Locked route guardrail

The account/security page is `/dashboard/account/` in the current app. UI polish must preserve this route and its existing Django URL name. Do not rename it to `/dashboard/settings/` during this redesign.

## Existing form guardrail

Do not introduce `django-widget-tweaks`, `django-crispy-forms`, custom select libraries, or frontend component libraries in this UI polish. Style current forms through existing templates, existing JS injection where already used, or controlled CSS utilities.
