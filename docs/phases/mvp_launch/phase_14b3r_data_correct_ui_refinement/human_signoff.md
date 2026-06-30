# Human Sign-off Checklist — Baha

This phase cannot PASS until Baha manually checks Chrome.

## Desktop Chrome

Open and inspect:

- [ ] `/`
- [ ] `/jobs/`
- [ ] one job detail page
- [ ] quick match form/result
- [ ] `/accounts/login/`
- [ ] `/accounts/signup/`
- [ ] `/accounts/password/reset/`
- [ ] `/dashboard/`
- [ ] `/dashboard/profile/`
- [ ] `/dashboard/cv/`
- [ ] `/dashboard/recommendations/`
- [ ] `/dashboard/matches/`
- [ ] one match detail
- [ ] `/dashboard/saved-jobs/`
- [ ] `/dashboard/account/`

## Mobile Chrome or responsive devtools

Check widths:

- [ ] 390px
- [ ] 768px
- [ ] desktop

## Product-flow checks

- [ ] Logged-in user does not see “Créer un compte”.
- [ ] Profile percentage is believable, not fake 100%.
- [ ] CV page shows extracted name/email/phone/location/links/skills when available.
- [ ] No `https://Next.js` appears as website URL.
- [ ] CV-detected but not applied values are visible or explained.
- [ ] Profile page labels are French.
- [ ] Recommendations page shows exact blocked reason if profile incomplete.
- [ ] Recommendations page shows offer cards if profile complete and active jobs exist.
- [ ] Match detail looks product-grade.
- [ ] Quick match form/result is not raw/native-looking.
- [ ] No raw CV text shown.
- [ ] No CV file URL shown.

## Verdict

Baha manual verdict:

```text
PASS / FAIL
```

Notes:

```text

```
