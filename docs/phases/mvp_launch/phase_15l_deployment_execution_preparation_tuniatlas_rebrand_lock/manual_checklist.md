# Phase 15L Manual Checklist

Run locally after implementation.

## Browser checks

- [ ] Home page shows TuniAtlas branding.
- [ ] Navbar/logo does not show TuniTech Abroad.
- [ ] Footer does not show TuniTech Abroad.
- [ ] Login/signup pages show TuniAtlas.
- [ ] Dashboard shows TuniAtlas or TuniAtlas Jobs where public/product branding appears.
- [ ] Admin branding is acceptable and no public-facing old name remains.
- [ ] Browser title shows TuniAtlas.
- [ ] Favicon/logo loads without 404.
- [ ] Job list works.
- [ ] Job detail works.
- [ ] Saved jobs works.
- [ ] Recommendations works.
- [ ] CV upload/private media behavior is unchanged.

## Old-name grep review

Run:

```bash
grep -R "TuniTech Abroad\|tunitech abroad\|Tunitech Abroad" templates static apps config docs/deployment .env.example -n || true
```

Allowed occurrences:

- historical phase docs
- internal project/repo references
- migration-independent technical notes

Blocked occurrences:

- public templates
- public emails
- browser titles/meta
- homepage/footer/navbar
- production deployment public brand docs
