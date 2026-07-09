# Manual Test Checklist

Run these manually when the phase changes user/admin visible behavior.

```text
Check anonymous access.
Check authenticated access.
Check admin/staff restriction.
Check form validation.
Check no debug traceback.
Check no secret/raw CV text appears.
```

## Phase 16A checks

```text
Open login page over HTTPS.
Try Google login with canonical domain.
Open robots.txt.
Open sitemap.xml.
Upload fake PDF locally and confirm rejected.
Open job detail with external description and inspect rendering.
```
