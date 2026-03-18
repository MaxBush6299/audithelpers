# Project Context

- **Owner:** Max Bush
- **Project:** AI Calibration — Document intelligence pipeline for audit evidence validation
- **Stack:** Python, Azure Doc Intelligence, Multimodal LLM, Power Apps, Logic Apps
- **Description:** Takes PowerPoint evidence (photos of forms, handwriting, screenshots), extracts text via Doc Intelligence, validates with multimodal LLM against audit points. Expanding to Power Apps frontend + Logic Apps orchestration.
- **Created:** 2026-03-18

## Learnings

<!-- Append new learnings below. Each entry is something lasting about the project. -->

### 2026-03-18: Lab Structure Design

**Context:** Max requested a portal-forward lab series for Solution Engineers and auditors. Key constraints:
- Portal clicks over CLI/Python
- Recipe-style with embedded learning concepts
- Linear sequence
- Understand existing code, not rebuild it

**Key decisions:**
- 12 labs total (0-11 core + Lab 12 optional Power Apps)
- ~5-6 hours total duration
- Bond owns bulk of Logic App implementation (Labs 3-10)
- Each pipeline stage becomes its own lab
- Existing Python code referenced for context, not rewritten

**Existing assets discovered:**
- `docs/LAB_LOGIC_APP_PIPELINE.md` — 61KB existing lab draft (CLI-heavy, needs portal rewrite)
- `docs/solution-overview.md` — good conceptual content to reuse
- `docs/DATA_FLOW.md` — explains Streamlit flow, useful for context
- `iac/` folder has Bicep templates (not used in portal-forward approach)

**Team alignment:**
- Moneypenny: Setup and Doc Intelligence
- Bond: All Logic App stages
- Q: Power Apps (optional)
- Felix: Testing
- Vesper: UX review across all labs
