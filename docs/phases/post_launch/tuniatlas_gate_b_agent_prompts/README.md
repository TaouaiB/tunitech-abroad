# TuniAtlas Gate B Agent Prompt Pack

## Which agent to use

Use **Codex in Warp, GPT-5.5 medium** for implementation.

Do **not** use Gemini for this gate unless Codex is unavailable. Do **not** use Minimax 2.7 or Kimi 2.6 for the main implementation. Gate B touches Django services, tests, taxonomy behavior, extraction rules, and score safety. Codex is the safest choice here because it handles repo-wide service/test changes and regression loops better.

For the review prompt, use **Codex GPT-5.5 medium** again. Use GPT-5.5 high only if you have enough budget and want a stricter second pass.

## Files

1. `01_gate_b_skill_extraction_v2_implementation_prompt.md`
2. `02_gate_b_skill_extraction_v2_review_prompt.md`

## Required workflow

1. First clean/amend the Gate A.2 commit if needed.
2. Run the implementation prompt.
3. Do not commit or push.
4. Run the review prompt.
5. The review prompt includes the command to create a zip with changed files.
6. Upload that zip back to ChatGPT for final human review before commit.

## Strict boundary

Gate B is **skill extraction v2 only**.

Do not implement:
- CV parser v2
- admin anomaly UI
- rematerialization
- production deployment
- broad EN/FR cleanup
- React/Next/FastAPI/Mongo/SQLAlchemy
