# TuniAtlas V16 Acceptance Checklist

Use this checklist after every page/component.

A page is not done until the implemented Django page matches v16 visually and behaviorally.

## Global checks

- [ ] desktop light matches v16
- [ ] desktop dark matches v16
- [ ] mobile light matches v16
- [ ] mobile dark matches v16
- [ ] EN text matches v16
- [ ] FR text matches v16
- [ ] no extra helper wording added
- [ ] no missing actions
- [ ] no duplicate buttons
- [ ] no broken responsive layout
- [ ] no console errors
- [ ] no HTMX errors
- [ ] no dark mode regression
- [ ] no language toggle regression

## Technical checks

Run:

```bash
python manage.py check
python manage.py test
python manage.py collectstatic --dry-run --noinput
```

If available, also run project-specific frontend/build/test commands.

## Page-specific checks

### Header / base layout

- [ ] brand/logo correct
- [ ] desktop nav correct
- [ ] mobile drawer correct
- [ ] theme toggle works
- [ ] language toggle works
- [ ] auth/logged-in states correct

### Jobs index

- [ ] mobile Search / Stats / Filters row exists
- [ ] search collapses/opens on mobile
- [ ] stats collapses/opens on mobile
- [ ] filters open in mobile drawer
- [ ] job cards match v16
- [ ] save button state works
- [ ] desktop layout unchanged

### Job detail

- [ ] title/company/location/source match layout
- [ ] action buttons match v16
- [ ] mobile sticky action bar works
- [ ] secondary content collapses correctly on mobile
- [ ] desktop layout unchanged

### Match score

- [ ] score card matches v16
- [ ] sections match v16
- [ ] mobile collapsible sections work
- [ ] sticky mobile action bar works
- [ ] no scoring logic changed

### Auth

- [ ] no `or email` separator
- [ ] no unnecessary helper text
- [ ] OAuth buttons match v16
- [ ] email/password fields match v16
- [ ] validation messages remain useful

### Profile setup

- [ ] compact mobile stepper
- [ ] only one action row on mobile
- [ ] no duplicate buttons
- [ ] no `OAuth account.` text
- [ ] no `Optional.` text unless truly needed for validation
- [ ] no `Check extracted data.` text
- [ ] sticky bottom action bar works on mobile
- [ ] desktop stepper remains correct

### Settings

- [ ] mobile sections are accordions
- [ ] spacing between collapsed cards is correct
- [ ] only intended section is open
- [ ] desktop layout remains correct
- [ ] no extra explanation text

### Recommendations / saved jobs

- [ ] cards match v16
- [ ] badges/chips match v16
- [ ] empty states match v16
- [ ] mobile layout matches v16

### Loading / empty / failure states

- [ ] AI progress loaders match v16
- [ ] loading states match v16
- [ ] empty states match v16
- [ ] failure/retry states match v16
- [ ] no invented states

## Final acceptance rule

If the page screenshot differs from v16, it is not done.

If the code is clean but the visual output differs, reject the change.
