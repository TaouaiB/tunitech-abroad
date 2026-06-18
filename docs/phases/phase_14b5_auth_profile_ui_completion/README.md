# Phase 14B.5 — Auth/Profile Truth + Full UI Coverage Repair

## Purpose
This phase fixes the remaining manually discovered blockers after Phase 14B.3R:

- allauth/socialaccount pages still missing the professional design
- `/accounts/3rdparty/` is unstyled
- `/accounts/password/set/` is unstyled
- account emails still show `example.test` or confusing copy
- Google/GitHub OAuth does not clearly support linking/switching providers
- social signup does not fill available profile data, including avatar/photo when available
- CV/Profile/recommendation truth is still inconsistent in the browser
- `target_country` appears in UI even though the MVP is France-only
- the agent keeps claiming PASS without full page coverage

This is not a new product feature phase. It is a repair phase to make the current MVP trustworthy and coherent.

## Final verdict rule
This phase can only end as:

- `BLOCKED_HUMAN_VISUAL_SIGNOFF`, after all automated tests pass but before Baha approves Chrome manually
- `FAIL`, if any required acceptance check fails

The agent must not claim final PASS. Baha decides PASS after manual browser review.
