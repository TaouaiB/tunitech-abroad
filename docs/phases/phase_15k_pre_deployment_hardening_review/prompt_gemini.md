# Gemini Prompt for Phase 15K

Mission: Perform a final pre-deployment hardening review of the repository and deployment docs.

Review:
1. Production settings safety.
2. Static/private media.
3. LLM/token spending safety.
4. Public route safety.
5. Deployment runbook quality.
6. Security scans.

Allowed repairs: Small documentation/test/config corrections if safe.
Forbidden: Major refactors, real deployment, `.env` exposure.
Verdict options: PASS / REPAIRED_PASS / BLOCKED / FAIL.
