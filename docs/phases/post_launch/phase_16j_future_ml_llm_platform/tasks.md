# Phase 16J — Future ML/LLM Platform — tasks.md

## Goal

Prepare optional ML/LLM platform infrastructure without making AI the scoring authority.

## In-scope apps/areas

```text
llm prompt/version/cache/logging
label export commands
offline model experiment structure
feature flags
```

## Tickets

### TTA-16J-001 — Prompt/version/log/cache cleanup

Priority: P0  
Type: llm/service/model/test

Acceptance:

```text
PromptVersion, LLMCacheEntry, LLMUsageLog or existing equivalents are consistent.
PromptRunnerService centralizes LLM calls.
No LLM calls from views.
No fake success in disabled mode.
Feature flags control usage.
```

### TTA-16J-002 — Label export commands

Priority: P0  
Type: command/privacy/test

Acceptance:

```text
Exports CVFieldCorrection, SkillExtractionFeedback, JobQualityFeedback where available.
Supports anonymization/redaction.
No raw CV files exported.
No secrets exported.
Output suitable for future offline evaluation/training.
```

### TTA-16J-003 — Offline experiment folder policy

Priority: P1  
Type: docs/tooling

Acceptance:

```text
Offline experiments are separate from production app path.
No model artifact loaded by production without explicit future phase.
No real private data committed.
Documented local-only workflow.
```

### TTA-16J-004 — Optional LLM extraction gates

Priority: P1  
Type: llm/service/test

Acceptance:

```text
LLM can assist extraction/explanation only behind feature flags.
LLM output is validated against schema.
LLM output maps to canonical taxonomy before scoring.
LLM cannot change final score.
LLM cannot bulk-rank jobs.
```

### TTA-16J-005 — Future ML readiness review

Priority: P1  
Type: docs/audit

Acceptance:

```text
Review confirms taxonomy is stable label space.
Review confirms correction/feedback tables exist or are explicitly deferred.
Review confirms evaluation metrics exist before any model is considered.
No production ML is shipped in this phase.
```

## Out of scope

```text
No production ML/DL model.
No model training pipeline in production.
No AI scoring authority.
No auto-apply/chatbot.
```
