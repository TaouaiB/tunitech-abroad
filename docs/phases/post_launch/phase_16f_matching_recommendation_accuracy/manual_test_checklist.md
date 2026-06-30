# Manual Test Checklist — Phase 16F

Manual checks:

```text
Pick a job with required skills and a profile with matching skill_id values.
Generate match and verify score breakdown.
Remove one required skill and verify missing required risk appears.
Use low-confidence detected job skill and verify it does not inflate score.
Verify LLM disabled/enabled does not change final score.
Open recommendations and verify reason snapshots explain why each job appears.
```
