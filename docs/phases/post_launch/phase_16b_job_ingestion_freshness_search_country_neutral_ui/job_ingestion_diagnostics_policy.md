# Job Ingestion Diagnostics Policy

The system must explain the complete funnel:

```text
external API returned
-> raw records stored
-> raw records changed/new/unchanged
-> normalized jobs
-> active/stale/expired/removed jobs
-> public visible jobs
-> public matchable jobs
```

`target_daily_fetch_count=1000` is a target/limit, not a fake guarantee. If the API/config only provides fewer relevant jobs, diagnostics must say so.

Freshness must never mass-stale or mass-remove jobs after failed ingestion.
