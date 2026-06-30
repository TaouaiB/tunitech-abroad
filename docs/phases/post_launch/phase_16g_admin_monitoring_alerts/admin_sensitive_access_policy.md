# Admin Sensitive Access Policy

Baha is the only owner/admin now. Build superuser/owner tools, not enterprise RBAC.

CV download rules:

```text
superuser/explicit staff permission only
served through protected Django view/service
no public media URL
no filesystem path leak
AdminFileAccessLog row required
reason field recommended
```

Admin alerts must not include raw CV text, secrets, tokens, or private file paths.
