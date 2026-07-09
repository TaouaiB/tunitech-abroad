# Human Signoff Checklist

Baha must manually approve before this phase can be considered done.

## Auth pages

- [ ] `/accounts/login/` styled
- [ ] `/accounts/signup/` styled
- [ ] `/accounts/logout/` styled
- [ ] `/accounts/password/reset/` styled
- [ ] `/accounts/password/set/` styled
- [ ] `/accounts/password/change/` styled
- [ ] `/accounts/email/` styled
- [ ] `/accounts/confirm-email/` styled
- [ ] `/accounts/3rdparty/` styled

## Account connections

- [ ] Google connected/disconnected state visible
- [ ] GitHub connected/disconnected state visible
- [ ] Connect buttons visible
- [ ] Set password option visible for OAuth-created account
- [ ] Provider session/account switching explanation visible

## Email

- [ ] Email does not say example.test
- [ ] Confirmation email has confirmation link
- [ ] Duplicate account email is clear and not misleading

## Profile/CV/recommendations

- [ ] Target country not visible
- [ ] Phone/location missing status matches actual DB/profile UI
- [ ] Current level label is `Niveau de carrière`
- [ ] Years label is `Années d’expérience`
- [ ] CV parsed data shown clearly
- [ ] Recommendations blocked/ready state is truthful

## Visual quality

- [ ] Pages look professional, not default allauth/admin
- [ ] Mobile layout acceptable
- [ ] Buttons/cards/forms consistent

Until checked, verdict remains:

```text
BLOCKED_HUMAN_VISUAL_SIGNOFF
```
