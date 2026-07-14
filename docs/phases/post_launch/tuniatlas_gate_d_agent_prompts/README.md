# TuniAtlas Gate D Agent Prompt Pack

## Which agent to use

Use **Codex in Warp, GPT-5.5 medium** for implementation.

Do **not** use Gemini unless Codex is unavailable. Do **not** use Minimax 2.7 or Kimi 2.6 for the main implementation. Gate D touches admin visibility, diagnostics, model/admin/query safety, and regression tests. Codex is the safest choice for service/admin/test work.

For the review prompt, use **Codex GPT-5.5 medium** again. Use GPT-5.5 high only if budget allows.

## Files

1. `01_gate_d_admin_anomaly_review_implementation_prompt.md`
2. `02_gate_d_admin_anomaly_review_review_prompt.md`

## Required workflow

1. Keep Gate A.2, Gate B, Gate C local and unpushed.
2. Run the implementation prompt.
3. Do not commit or push.
4. Run the review prompt.
5. Use the review prompt zip command.
6. Upload the Gate D review zip back to ChatGPT before commit.

## Strict boundary

Gate D is **admin anomaly review only**.

Do not implement:
- rematerialization / Gate E
- production deployment
- broad UI/i18n cleanup
- new extraction model
- new CV parser work except direct read-only display of parser warnings
- React/Next/FastAPI/Mongo/SQLAlchemy
