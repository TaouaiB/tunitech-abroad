# TuniAtlas Gate C Agent Prompt Pack

## Which agent to use

Use **Codex in Warp, GPT-5.5 medium** for implementation.

Do **not** use Gemini for this gate unless Codex is unavailable. Do **not** use Minimax 2.7 or Kimi 2.6 for the main implementation. Gate C touches CV parsing services, profile update safety, tests, and privacy-sensitive behavior. Codex is the safest choice because it handles Django service/test changes and regression loops better.

For the review prompt, use **Codex GPT-5.5 medium** again. Use GPT-5.5 high only if budget allows.

## Files

1. `01_gate_c_cv_parser_v2_implementation_prompt.md`
2. `02_gate_c_cv_parser_v2_review_prompt.md`

## Required workflow

1. Do not push Gate A.2 or Gate B yet.
2. Run the implementation prompt.
3. Do not commit or push.
4. Run the review prompt.
5. The review prompt includes the zip/export command for changed files.
6. Upload that zip back to ChatGPT for final review before commit.

## Strict boundary

Gate C is **CV parser v2 only**.

Do not implement:
- more job skill extraction v2 work unless fixing a direct Gate C test interaction
- admin anomaly UI
- rematerialization
- production deployment
- broad EN/FR cleanup
- React/Next/FastAPI/Mongo/SQLAlchemy
