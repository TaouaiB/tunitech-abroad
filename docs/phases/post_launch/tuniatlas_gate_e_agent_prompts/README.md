# TuniAtlas Gate E Agent Prompt Pack

## Which agent to use

Use **Codex in Warp, GPT-5.5 medium** for implementation.

Do **not** use Gemini unless Codex is unavailable. Do **not** use Minimax 2.7 or Kimi 2.6 for the main implementation. Gate E touches local database rematerialization, search vectors, matches/recommendations, reporting, and rollback safety. Codex is the safest choice for this repo-wide Django service/management-command work.

For the review prompt, use **Codex GPT-5.5 medium** again. Use GPT-5.5 high only if budget allows.

## Files

1. `01_gate_e_rematerialize_compare_implementation_prompt.md`
2. `02_gate_e_rematerialize_compare_review_prompt.md`

## Required workflow

1. Keep Gate A.2, Gate B, Gate C, and Gate D local and unpushed.
2. Run the implementation prompt.
3. Do not commit or push.
4. Run the review prompt.
5. The review prompt includes the zip/export command.
6. Upload the Gate E review zip back to ChatGPT before commit.

## Strict boundary

Gate E is **local rematerialization and before/after comparison**.

Do not:
- deploy to production
- push branches
- call France Travail live APIs
- enable uncontrolled LLM enrichment
- create canonical skills automatically
- perform broad UI/i18n cleanup
- introduce React/Next/FastAPI/Mongo/SQLAlchemy
- mutate production data
