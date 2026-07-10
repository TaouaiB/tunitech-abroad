# TuniAtlas Gate E Fix Prompt Pack

## Agent

Use **Codex in Warp, GPT-5.5 medium**.

Do not use Gemini, Minimax 2.7, or Kimi 2.6 for this correction unless Codex is unavailable.

## Workflow

1. Run `01_gate_e_fix_blockers_prompt.md`.
2. Do not commit or push.
3. Run `02_gate_e_re_review_prompt.md`.
4. The review prompt creates a new zip.
5. Upload the new Gate E review zip to ChatGPT.

## Current verdict

Gate E is **not safe to commit or apply yet**.

The uploaded submission contains only a dry-run report. It does not prove targeted apply, idempotency, full apply, or a verified backup. The report also contains misleading hard-coded regression PASS lines and inconsistent quality reporting.
