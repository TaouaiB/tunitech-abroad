# Phase 09 — LLM Support — README

This folder contains the autonomous agent instructions for Phase 09 only.

## Correct folder name

```text
docs/phases/phase_09_llm_support/
```

## Files in this phase folder

```text
README.md
prompt.md
tasks.md
acceptance.md
agent_report_template.md
codex_verify_prompt.md
```

## How to use

1. Confirm Phase 08 is committed and pushed on `dev`.
2. Give Gemini/Antigravity the contents of `prompt.md` as the implementation instruction.
3. Gemini may work automatically through all tickets in this phase only.
4. Gemini must run the acceptance commands and repair failures up to the configured loop limit.
5. After Gemini reports success, run `codex_verify_prompt.md` with Codex for strict review.
6. Do not commit until senior review approves.

## Phase boundary

Phase 09 is for controlled LLM support only. It must not implement email, privacy deletion, admin observability, deployment, or polish work.
