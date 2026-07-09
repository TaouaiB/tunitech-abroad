# Phase 14K-0 Acceptance Criteria

## Required file locations

The repository must contain:

```text
docs/design/approved_ui_ux/README_APPROVED.md
docs/design/approved_ui_ux/design_vision/README.md
docs/design/approved_ui_ux/design_vision/00_product_ux_principles.md
docs/design/approved_ui_ux/design_vision/01_brand_and_visual_identity.md
docs/design/approved_ui_ux/design_vision/02_theme_tokens_tailwind.md
docs/design/approved_ui_ux/design_vision/03_information_architecture_and_navigation.md
docs/design/approved_ui_ux/design_vision/04_components_specification.md
docs/design/approved_ui_ux/design_vision/05_page_specs_public.md
docs/design/approved_ui_ux/design_vision/06_page_specs_private_dashboard.md
docs/design/approved_ui_ux/design_vision/07_jobs_matching_recommendations_deep_spec.md
docs/design/approved_ui_ux/design_vision/08_forms_auth_cv_profile_spec.md
docs/design/approved_ui_ux/design_vision/09_accessibility_responsive_empty_states.md
docs/design/approved_ui_ux/design_vision/10_backend_safety_and_template_guardrails.md
docs/design/approved_ui_ux/design_vision/11_page_by_page_final_blueprint.md
docs/design/approved_ui_ux/design_vision/12_french_ux_copy_dictionary.md
docs/design/approved_ui_ux/design_vision/13_future_phase_split_recommendation_no_prompts.md
docs/design/approved_ui_ux/design_vision/99_input_audit_summary.md
docs/design/approved_ui_ux/static_ui_prototype/prototype-map.html
docs/design/approved_ui_ux/static_ui_prototype/component-states.html
docs/design/approved_ui_ux/static_ui_prototype/404.html
docs/design/approved_ui_ux/static_ui_prototype/500.html
docs/design/approved_ui_ux/static_ui_prototype/assets/prototype.css
docs/design/approved_ui_ux/static_ui_prototype/assets/prototype.js
```

The repository must also contain:

```text
docs/phases/phase_14k_0_design_docs_import/tasks.md
docs/phases/phase_14k_0_design_docs_import/prompt_gemini.md
docs/phases/phase_14k_0_design_docs_import/prompt_codex.md
docs/phases/phase_14k_0_design_docs_import/acceptance.md
docs/phases/phase_14k_0_design_docs_import/agent_report_template.md
docs/phases/phase_14k_0_design_docs_import/codex_report_template.md
```

## Must not change

No changes in:

```text
templates/**
static/**
apps/**
config/**
tailwind.config.js
package.json
package-lock.json
requirements*.txt
pyproject.toml
manage.py
.env
.env.*
```

## Required commands

```bash
git status --short
git diff --stat
git diff --name-only
find docs/design/approved_ui_ux -maxdepth 2 -type f | sort | head -120
find docs/phases/phase_14k_0_design_docs_import -maxdepth 1 -type f | sort
git diff --check
```

## Acceptance decision

PASS only if:

- the approved design source is present
- the static HTML prototype is present
- the phase files are present
- the change is docs-only
- `git diff --check` passes
- no secrets are present
- Phase 14K-1 has not started
