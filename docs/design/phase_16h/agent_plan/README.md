# TuniAtlas v16 Final Prototype — Agent Implementation Plan Pack

This pack is for a new ChatGPT/project conversation that will plan and control implementation of the **TuniAtlas v16 final UI prototype** into the existing Django + HTMX frontend.

## Source of truth

- **v16 is final.**
- The prototype is not inspiration. It is the UI contract.
- The goal is exact implementation, not redesign.
- Agents must not add wording, sections, features, animations, colors, or layout ideas that are not in v16.

## Files in this pack

1. `V16_EXACT_IMPLEMENTATION_PLAN.md` — the main plan and workflow.
2. `V16_UI_LOCK.md` — hard rules to prevent redesign/scope creep.
3. `V16_COPY_LOCK.md` — wording rules and banned extra helper text.
4. `V16_PAGE_MAPPING.md` — suggested prototype-to-Django template mapping.
5. `V16_AGENT_WORKFLOW.md` — low-token agent workflow using Gemini Pro and GPT-5.5.
6. `V16_ACCEPTANCE_CHECKLIST.md` — visual and behavior acceptance checklist.

## Recommended files to upload with this pack

Upload these together in the implementation conversation:

- `tuniatlas_full_prototype_v16.zip`
- `tuniatlas_v16_implementation_handoff_pack.zip`
- this pack: `tuniatlas_v16_agent_implementation_plan_pack.zip`

## Main principle

Use agents as porting tools, not designers.

> You are not designing. You are porting v16 exactly into Django/HTMX.
