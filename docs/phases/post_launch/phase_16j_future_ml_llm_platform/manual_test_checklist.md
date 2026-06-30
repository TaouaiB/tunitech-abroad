# Manual Test Checklist — Phase 16J

Manual checks:

```text
LLM disabled returns disabled result, not fake success.
PromptRunnerService is the only place calling OpenRouter.
Feature flags prevent accidental production LLM usage.
Label export command redacts/anonymizes private fields.
No production ML model is trained, loaded, or served.
Final match score remains deterministic.
```
