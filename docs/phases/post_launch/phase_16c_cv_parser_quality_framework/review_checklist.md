# Review Checklist — Phase 16C — CV Parser Quality Framework

Senior review must inspect:

```text
Phase scope compliance
Service-layer compliance
Migration safety
Tests and commands
Security/privacy risks
CV privacy
Secret handling
Admin access protection
Public_id usage
No overbuilding
No future phase drift
```

Reject if:

```text
Business logic moved into views/templates/tasks.
Private CV files are exposed publicly.
External API is called during user search.
LLM changes fit score.
Secrets are printed or committed.
React/Next/FastAPI/Mongo/SQLAlchemy introduced.
```
