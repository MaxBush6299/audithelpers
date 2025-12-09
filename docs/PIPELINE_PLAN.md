# PI Calibration Evidence Evaluation Pipeline
## Planning Document

**Version:** 1.1  
**Date:** December 8, 2025  
**Status:** In Progress

---

## 1. Executive Summary

This document outlines the plan to consolidate existing components into a unified end-to-end pipeline that:
1. Accepts an Excel file containing PI calibration elements
2. Accepts one or more PowerPoint files containing evidence slides
3. Processes through extraction, matching, and LLM evaluation
4. Produces a final evaluation report (Word/DOCX)
5. Provides a Streamlit web UI for easy operation

---

## 2. Current State: Existing Components

### 2.1 Excel Elements Extraction (`extractors/xlsx_extract.py`)
- **Function:** `extract_pi_rows_xlsx(source, sheets)`
- **Input:** Excel file (path, bytes, or BytesIO)
- **Output:** List of dictionaries with `PI-Element`, `Ask/Look For`, `Calibrator notes`
- **Status:** ✅ Complete and working
- **Notes:** Parses columns L and M, extracts element numbers via regex

### 2.2 PowerPoint Text Extraction (`extractors/helpers/multimodal_extract.py`)
- **Functions:** `multimodal_extract()`, `quick_extract()`
- **Input:** PPTX file path
- **Output:** JSON with slides array containing `index` and `text` for each slide
- **Status:** ✅ Complete and working
- **Pipeline:**
  1. Render slides to images (PowerPoint COM on Windows, LibreOffice otherwise)
  2. Extract native text from PPTX shapes
  3. OCR embedded images via Azure Document Intelligence (optional)
  4. Send image + extracted text to GPT-4.1/5.1 for accurate transcription
- **Dependencies:** PowerPoint/LibreOffice, Azure OpenAI, Azure Document Intelligence

### 2.3 Evidence-to-Element Matching (`match_evidence_to_elements.py`)
- **Input:** 
  - `elements.json` (from xlsx extraction)
  - `evidence.json` (from multimodal extraction)
- **Output:** `matched_evidence.json` with structure:
  ```json
  {
    "metadata": {...},
    "statistics": {...},
    "matched_elements": [
      {
        "PI-Element": "2.1",
        "Calibrator instructions": {"Ask/Look For": "...", "Calibrator notes": "..."},
        "Evidence": [{slide_index, text_preview, full_text, ...}],
        "evidence_count": N
      }
    ],
    "unmatched_slides": [...]
  }
  ```
- **Status:** ✅ Complete and working
- **Logic:** Uses regex patterns in `helper/element_extract.py` to match slide references to elements

### 2.4 LLM Evidence Evaluation (`agents/evidence_evaluator.py`, `evaluate_evidence.py`)
- **Input:** `matched_evidence.json`
- **Output:** 
  - `evaluation_results.json` - Final results
  - `evaluation_progress.json` - Incremental updates for real-time monitoring
- **Status:** ✅ Complete and working
- **Logic:** 
  - Elements with no evidence → "Needs More Evidence" (no LLM call)
  - Others → LLM evaluates against calibrator instructions
  - 3 retries with exponential backoff
  - Outputs: Pass / Fail / Needs More Evidence / Error

### 2.5 Element Pattern Extraction (`helper/element_extract.py`)
- **Functions:** `extract_element_references()`, `get_primary_element()`, `normalize_element_id()`
- **Status:** ✅ Complete and working
- **Patterns Supported:**
  - `X.Y >` (arrow format)
  - `NEXT X.Y >` (new elements)
  - `PI-X` (headers)
  - `(X.Y)` (parentheses)
  - `Element X.Y` (explicit)

---

## 3. Target Pipeline Architecture

### 3.1 Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           UNIFIED PIPELINE                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐     ┌──────────────┐                                      │
│  │  Excel File  │     │  PPTX Files  │                                      │
│  │  (Elements)  │     │  (Evidence)  │                                      │
│  └──────┬───────┘     └──────┬───────┘                                      │
│         │                    │                                               │
│         ▼                    ▼                                               │
│  ┌──────────────┐     ┌──────────────┐                                      │
│  │    Stage 1   │     │    Stage 2   │                                      │
│  │   xlsx_ext   │     │  multimodal  │                                      │
│  │              │     │   extract    │                                      │
│  └──────┬───────┘     └──────┬───────┘                                      │
│         │                    │                                               │
│         │  elements.json     │  evidence.json                               │
│         │                    │  (merged if multiple PPTX)                   │
│         ▼                    ▼                                               │
│  ┌─────────────────────────────────────┐                                    │
│  │             Stage 3                 │                                    │
│  │     Evidence-Element Matching       │                                    │
│  │                                     │                                    │
│  └──────────────┬──────────────────────┘                                    │
│                 │                                                            │
│                 │  matched_evidence.json                                    │
│                 ▼                                                            │
│  ┌─────────────────────────────────────┐                                    │
│  │             Stage 4                 │                                    │
│  │       LLM Evaluation Agent          │                                    │
│  │    (with progress file output)      │                                    │
│  └──────────────┬──────────────────────┘                                    │
│                 │                                                            │
│                 │  evaluation_results.json                                  │
│                 │  evaluation_progress.json (real-time)                     │
│                 ▼                                                            │
│  ┌─────────────────────────────────────┐                                    │
│  │             Stage 5                 │                                    │
│  │        Report Generation            │                                    │
│  │   (Excel/PDF/HTML - Future)         │                                    │
│  └─────────────────────────────────────┘                                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Data Flow Summary

| Stage | Input | Output | Component |
|-------|-------|--------|-----------|
| 1 | Excel file | `elements.json` | `xlsx_extract.py` |
| 2 | PPTX file(s) | `evidence.json` | `multimodal_extract.py` |
| 3 | elements.json + evidence.json | `matched_evidence.json` | `match_evidence_to_elements.py` |
| 4 | matched_evidence.json | `evaluation_results.json` + `evaluation_progress.json` | `evaluate_evidence.py` |
| 5 | evaluation_results.json | Final Report | **NEW - To be built** |

---

## 4. Required Development Work

### 4.1 Stage 1: Excel Extraction (Minor Changes)

**Current State:** Extracts to Python list, caller saves to JSON  
**Required Changes:**
- [x] Add CLI wrapper with argparse for standalone use
- [x] Add validation for expected columns (L, M)
- [x] Add error handling for malformed rows
- [x] Add progress output for large files

**Estimated Effort:** 2-4 hours

### 4.2 Stage 2: PowerPoint Extraction (Minor Changes)

**Current State:** `quick_extract()` function processes single PPTX  
**Required Changes:**
- [x] Add support for multiple PPTX files (merge output)
- [x] Handle slide numbering across multiple files (offset indices)
- [x] Track source file for each slide in output
- [x] Add validation for rendering prerequisites

**Estimated Effort:** 4-6 hours

**Multi-PPTX Output Structure:**
```json
{
  "source_files": ["evidence1-6.pptx", "evidence7-10.pptx"],
  "total_slides": 120,
  "slides": [
    {"index": 1, "source_file": "evidence1-6.pptx", "source_index": 1, "text": "..."},
    {"index": 70, "source_file": "evidence7-10.pptx", "source_index": 1, "text": "..."}
  ]
}
```

### 4.3 Stage 3: Evidence-Element Matching (Minor Changes)

**Current State:** CLI tool with argparse, works well  
**Required Changes:**
- [x] Accept direct Python objects (not just file paths) for programmatic use
- [x] Handle multi-source evidence (track which PPTX each slide came from)
- [x] Add `source_file` to matched evidence output

**Estimated Effort:** 2-3 hours

### 4.4 Stage 4: LLM Evaluation (No Changes)

**Current State:** Complete with progress file output  
**Required Changes:** None - ready for integration

**Estimated Effort:** 0 hours

### 4.5 Stage 5: Report Generation (NEW)

**Current State:** Does not exist  
**Required Development:**
- [ ] Design report format(s) - Excel, PDF, HTML options
- [ ] Create report generator that reads `evaluation_results.json`
- [ ] Include:
  - Summary statistics (Pass/Fail/Needs More Evidence counts)
  - Per-element details with reasoning
  - Evidence slide references
  - Timestamp and metadata
- [ ] Consider formatting for calibrator consumption

**Estimated Effort:** 8-16 hours depending on format complexity

**Proposed Report Sections:**
1. **Executive Summary**
   - Overall compliance percentage
   - Elements by status (Pass/Fail/Needs More Evidence)
   - Timestamp and model used

2. **Detailed Results Table**
   | PI Element | Status | Evidence Slides | LLM Reasoning |
   |------------|--------|-----------------|---------------|
   | 1.1 | Pass | 2, 3 | "Evidence shows..." |
   | 1.2 | Needs More Evidence | - | "No evidence provided" |

3. **Elements Requiring Attention**
   - Failed elements with detailed reasoning
   - Elements needing more evidence

4. **Appendix**
   - Full evidence text for each element (optional)

### 4.6 Unified Pipeline Orchestrator (NEW)

**Current State:** Each stage runs independently via CLI  
**Required Development:**
- [ ] Create `run_pipeline.py` - single entry point
- [ ] Accept inputs:
  - `--elements-xlsx` - Path to Excel file
  - `--evidence-pptx` - One or more PPTX paths
  - `--output-dir` - Directory for all outputs
  - `--report-format` - excel/pdf/html
- [ ] Orchestrate all stages sequentially
- [ ] Handle errors at each stage gracefully
- [ ] Provide overall progress tracking
- [ ] Clean up intermediate files (optional)

**Estimated Effort:** 8-12 hours

---

## 5. Configuration & Environment

### 5.1 Required Environment Variables

```bash
# Azure Document Intelligence (for embedded image OCR)
AZURE_DI_ENDPOINT=https://<resource>.cognitiveservices.azure.com
AZURE_DI_KEY=<key>

# Azure OpenAI - GPT-4.1 (for extraction and evaluation)
AZURE_AI_ENDPOINT=https://<resource>.services.ai.azure.com
AZURE_AI_API_KEY=<key>
GPT_4_1_DEPLOYMENT=<deployment-name>

# Optional: GPT-5.1 (if using newer model)
AZURE_AI_GPT5_ENDPOINT=...
AZURE_AI_GPT5_API_KEY=...
GPT_5_1_DEPLOYMENT=...
```

### 5.2 System Requirements

- **Windows:** PowerPoint (preferred for slide rendering) or LibreOffice
- **macOS/Linux:** LibreOffice required for slide rendering
- **Python:** 3.9+
- **Dependencies:** See `requirements.txt`

---

## 6. Azure Deployment & Streamlit Frontend

### 6.1 Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         AZURE DEPLOYMENT ARCHITECTURE                            │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌──────────────┐         ┌─────────────────────────────────────────────────┐   │
│  │    Users     │         │           Azure Container Apps                   │   │
│  │  (Browser)   │────────▶│  ┌─────────────────────────────────────────┐    │   │
│  └──────────────┘         │  │         Streamlit App Container         │    │   │
│         │                 │  │                                         │    │   │
│         │ Entra ID Auth   │  │  • File upload UI                       │    │   │
│         ▼                 │  │  • Progress visualization               │    │   │
│  ┌──────────────┐         │  │  • Results dashboard                    │    │   │
│  │  Microsoft   │         │  │  • Report download                      │    │   │
│  │  Entra ID    │◀───────▶│  └─────────────────────────────────────────┘    │   │
│  │  (Auth)      │         │                    │                             │   │
│  └──────────────┘         │                    │ Pipeline calls              │   │
│                           │                    ▼                             │   │
│                           │  ┌─────────────────────────────────────────┐    │   │
│                           │  │     Pipeline Processing (in-container)  │    │   │
│                           │  │                                         │    │   │
│                           │  │  • Excel extraction                     │    │   │
│                           │  │  • PPTX multimodal extraction           │    │   │
│                           │  │  • Evidence-element matching            │    │   │
│                           │  │  • LLM evaluation                       │    │   │
│                           │  │  • Report generation                    │    │   │
│                           │  └─────────────────────────────────────────┘    │   │
│                           └──────────────┬──────────────────────────────────┘   │
│                                          │                                       │
│                                          │ Managed Identity                      │
│                                          ▼                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                        Azure AI Services                                 │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                   │    │
│  │  │  Azure       │  │   Azure      │  │   Azure      │                   │    │
│  │  │  OpenAI      │  │   Document   │  │   Blob       │                   │    │
│  │  │  (GPT-4.1)   │  │   Intel.     │  │   Storage    │                   │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘                   │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Authentication Strategy: Open Access (POC)

**Approach:** No authentication for POC deployment. Single-user access assumed.

**Rationale:**
- POC/demo environment only
- Single user expected at a time
- Simplifies deployment and testing
- No Entra ID app registration required

**Future Consideration:** If multi-user or security is needed later, Easy Auth with Microsoft Entra ID can be added.

### 6.3 Azure Container Apps Configuration (Simplified)

**Container App Settings:**
```yaml
# container-app.yaml
properties:
  configuration:
    ingress:
      external: true
      targetPort: 8501  # Streamlit default port
      transport: http
    secrets:
      - name: azure-openai-endpoint
        value: <from-key-vault>
    registries:
      - server: <acr-name>.azurecr.io
        identity: system
  template:
    containers:
      - name: calibration-app
        image: <acr-name>.azurecr.io/calibration-app:latest
        resources:
          cpu: 2.0
          memory: 4Gi
        env:
          - name: AZURE_AI_ENDPOINT
            secretRef: azure-openai-endpoint
    scale:
      minReplicas: 0
      maxReplicas: 3
      rules:
        - name: http-scaling
          http:
            metadata:
              concurrentRequests: "10"
```

**Resource Recommendations:**
- **CPU:** 2 cores (PPTX processing is CPU-intensive)
- **Memory:** 4 GB (LibreOffice rendering needs memory)
- **Scale:** 0-3 replicas with HTTP-based autoscaling
- **Timeout:** Extend request timeout for long-running evaluations

### 6.4 Container Image Requirements

**Dockerfile Considerations:**
```dockerfile
FROM python:3.11-slim

# Install LibreOffice for slide rendering (no PowerPoint in container)
RUN apt-get update && apt-get install -y \
    libreoffice-impress \
    libreoffice-common \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . /app
WORKDIR /app

# Streamlit config
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

EXPOSE 8501
CMD ["streamlit", "run", "streamlit_app.py"]
```

**Note:** Container uses LibreOffice for slide rendering (not PowerPoint COM).

### 6.5 Managed Identity Permissions

Grant the Container App's managed identity these roles:

| Azure Service | Role | Purpose |
|--------------|------|---------|
| Azure OpenAI | Cognitive Services OpenAI User | LLM calls for extraction/evaluation |
| Document Intelligence | Cognitive Services User | OCR for embedded images |
| Blob Storage | Storage Blob Data Contributor | Temporary file storage (optional) |
| Key Vault | Key Vault Secrets User | Access secrets (if using Key Vault) |

### 6.6 Streamlit Application Design (Full Implementation)

**Goal:** Complete single-page web UI for running the pipeline, viewing results, and downloading Word reports.

**Deployment:** Azure Container Apps or Azure Container Instances  
**Access Model:** Single user at a time, open access (no authentication for POC)  
**File:** `streamlit_app.py` (~300-400 lines)

---

#### 6.6.1 Page Layout Design

```
┌───────────────────────────────────────────────────────────────────────────────┐
│  📊 PI Calibration Evidence Evaluator                                          │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │ CONFIGURATION                                                            │  │
│  ├─────────────────────────────────────────────────────────────────────────┤  │
│  │                                                                          │  │
│  │  📁 Upload Files                           ⚙️ Settings                   │  │
│  │  ┌──────────────────────────────────┐     ┌──────────────────────────┐  │  │
│  │  │ Elements Excel:  [Browse...]     │     │ Model: [GPT-4.1      ▼]  │  │  │
│  │  │ ✅ calib_evidence.xlsx           │     │                          │  │  │
│  │  │                                  │     │                          │  │  │
│  │  │ Evidence PPTX:   [Browse...]     │     │                          │  │  │
│  │  │ ✅ evidence1-6.pptx              │     │                          │  │  │
│  │  │ ✅ evidence7+.pptx               │     │                          │  │  │
│  │  └──────────────────────────────────┘     └──────────────────────────┘  │  │
│  │                                                                          │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │ ELEMENT FILTER (Optional - Pre-Pipeline)                                 │  │
│  ├─────────────────────────────────────────────────────────────────────────┤  │
│  │                                                                          │  │
│  │  Filter elements before running pipeline:                                │  │
│  │  ┌───────────────────────────────────────────────────────────────────┐  │  │
│  │  │ ☑ 1.1 Process Monitoring                                          │  │  │
│  │  │ ☑ 1.2 Data Collection                                             │  │  │
│  │  │ ☐ 1.3 Quality Control (uncheck to skip)                           │  │  │
│  │  │ ☑ 2.1 Calibration Verification                                    │  │  │
│  │  │ ... (expandable list of all elements)                             │  │  │
│  │  └───────────────────────────────────────────────────────────────────┘  │  │
│  │  [Select All] [Deselect All]                                             │  │
│  │                                                                          │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                │
│  ┌──────────────────────────────────────────────────────────────────────────┐ │
│  │  [▶️ RUN FULL PIPELINE]                                                   │ │
│  └──────────────────────────────────────────────────────────────────────────┘ │
│                                                                                │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │ PIPELINE PROGRESS                                                        │  │
│  ├─────────────────────────────────────────────────────────────────────────┤  │
│  │                                                                          │  │
│  │  Stage: [Excel ✅] → [PPTX ✅] → [Matching ✅] → [Evaluation 🔄]         │  │
│  │                                                                          │  │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 67%                         │  │
│  │  Evaluating element 2.3 (37 of 55)...                                    │  │
│  │                                                                          │  │
│  │  📋 Recent Activity:                                                     │  │
│  │  • ✅ Element 2.2 evaluated: PASS (slides 12, 13)                        │  │
│  │  • ✅ Element 2.1 evaluated: PASS (slide 11)                             │  │
│  │  • ✅ Element 1.5 evaluated: NEEDS_MORE (no matching slides)             │  │
│  │                                                                          │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │ EVALUATION RESULTS                                                       │  │
│  ├─────────────────────────────────────────────────────────────────────────┤  │
│  │                                                                          │  │
│  │  Summary: ✅ 42 Pass | ⚠️ 8 Needs More | ❌ 5 Fail | Total: 55           │  │
│  │                                                                          │  │
│  │  ┌───────────────────────────────────────────────────────────────────┐  │  │
│  │  │ Element  │ Status     │ Slides        │ Summary                   │  │  │
│  │  │──────────│────────────│───────────────│───────────────────────────│  │  │
│  │  │ 1.1      │ ✅ Pass    │ 2, 3          │ Evidence shows process... │  │  │
│  │  │ 1.2      │ ✅ Pass    │ 4             │ Data collection method... │  │  │
│  │  │ 1.3      │ ⚠️ Needs   │ -             │ No matching evidence...   │  │  │
│  │  │ 2.1      │ ✅ Pass    │ 6, 7          │ Calibration verified...   │  │  │
│  │  │ 2.2      │ ❌ Fail    │ 8             │ Evidence incomplete...    │  │  │
│  │  │ ...      │ ...        │ ...           │ ...                       │  │  │
│  │  └───────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                          │  │
│  │  [Expand Row to See Full Reasoning + Evidence Text]                      │  │
│  │                                                                          │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │ DOWNLOAD REPORT                                                          │  │
│  ├─────────────────────────────────────────────────────────────────────────┤  │
│  │                                                                          │  │
│  │  Report Options:                                                         │  │
│  │  ☑ Include passed elements                                               │  │
│  │  ☑ Include failed elements                                               │  │
│  │  ☑ Include needs-more elements                                           │  │
│  │  ☑ Include evidence text excerpts                                        │  │
│  │                                                                          │  │
│  │  [📥 Download Word Report (.docx)]  [📥 Download JSON Results]           │  │
│  │                                                                          │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

#### 6.6.2 Component Breakdown

| Component | Streamlit Widget | Purpose |
|-----------|------------------|---------|
| Excel Upload | `st.file_uploader(type=['xlsx'])` | Single element file |
| PPTX Upload | `st.file_uploader(type=['pptx'], accept_multiple_files=True)` | One or more evidence files |
| Model Dropdown | `st.selectbox(["GPT-4.1", "GPT-5.1"])` | Select LLM model |
| Element Filter | `st.multiselect()` or checkbox list | Pre-filter elements |
| Run Button | `st.button("Run Full Pipeline")` | Start processing |
| Stage Progress | `st.columns()` + status icons | Visual pipeline stages |
| Progress Bar | `st.progress()` + `st.text()` | Real-time progress |
| Activity Log | `st.container()` with updates | Recent evaluation results |
| Results Table | `st.dataframe()` or `st.data_editor()` | Sortable, filterable results |
| Expandable Details | `st.expander()` | Full reasoning per element |
| Summary Stats | `st.metric()` columns | Pass/Fail/NeedMore counts |
| Report Options | `st.checkbox()` group | Customize report content |
| Download Buttons | `st.download_button()` | Word/JSON downloads |

---

#### 6.6.3 State Management

```python
# Session state keys
st.session_state.keys = {
    "pipeline_status": "idle" | "running" | "completed" | "error",
    "current_stage": 1-4,
    "progress_percent": 0-100,
    "current_element": "2.3",
    "results": [],           # List of evaluation results
    "activity_log": [],      # Recent activity for display
    "selected_elements": [], # Pre-filtered element IDs
    "uploaded_excel": None,  # File buffer
    "uploaded_pptx": [],     # List of file buffers
    "selected_model": "GPT-4.1",
}
```

---

#### 6.6.4 Pipeline Execution Flow

```python
def run_pipeline():
    # 1. Save uploaded files to temp directory
    temp_dir = tempfile.mkdtemp()
    excel_path = save_uploaded_file(st.session_state.uploaded_excel, temp_dir)
    pptx_paths = [save_uploaded_file(f, temp_dir) for f in st.session_state.uploaded_pptx]
    
    # 2. Run pipeline stages sequentially
    st.session_state.pipeline_status = "running"
    
    # Stage 1: Excel extraction
    st.session_state.current_stage = 1
    elements = extract_elements(excel_path, filter=st.session_state.selected_elements)
    
    # Stage 2: PPTX extraction
    st.session_state.current_stage = 2
    evidence = extract_evidence(pptx_paths, model=st.session_state.selected_model)
    
    # Stage 3: Matching
    st.session_state.current_stage = 3
    matches = match_evidence(elements, evidence)
    
    # Stage 4: Evaluation (with progress updates)
    st.session_state.current_stage = 4
    for i, element in enumerate(matches):
        result = evaluate_element(element, model=st.session_state.selected_model)
        st.session_state.results.append(result)
        st.session_state.progress_percent = (i + 1) / len(matches) * 100
        st.session_state.activity_log.insert(0, format_activity(result))
    
    st.session_state.pipeline_status = "completed"
```

---

#### 6.6.5 Live Progress Monitoring

The pipeline writes progress to `evaluation_progress.json`. Streamlit polls this file:

```python
progress_container = st.empty()

def update_progress_display():
    """Poll progress file and update UI"""
    while st.session_state.pipeline_status == "running":
        progress = load_json("evaluation_progress.json")
        
        with progress_container.container():
            # Stage indicators
            cols = st.columns(4)
            stages = ["Excel", "PPTX", "Matching", "Evaluation"]
            for i, (col, stage) in enumerate(zip(cols, stages)):
                if i < progress["current_stage"]:
                    col.success(f"✅ {stage}")
                elif i == progress["current_stage"]:
                    col.info(f"🔄 {stage}")
                else:
                    col.write(f"⬜ {stage}")
            
            # Progress bar
            st.progress(progress["completed"] / progress["total"])
            st.text(f"Evaluating element {progress['current_element']} "
                   f"({progress['completed']} of {progress['total']})...")
            
            # Recent activity
            st.subheader("📋 Recent Activity")
            for activity in progress["recent_results"][:5]:
                icon = {"PASS": "✅", "FAIL": "❌", "NEEDS_MORE": "⚠️"}[activity["verdict"]]
                st.write(f"{icon} Element {activity['element_id']}: {activity['verdict']}")
        
        time.sleep(1)  # Poll every second
```

**Estimated Effort:** 12-16 hours

### 6.7 Word Report Generator (DOCX)

**Goal:** Generate professional Word document with evaluation summary and per-element breakdown.

**Output Format:** `.docx` (Microsoft Word)  
**Library:** `python-docx`

---

#### 6.7.1 Report Structure

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│           PI CALIBRATION EVIDENCE EVALUATION REPORT              │
│                                                                  │
│  Generated: December 8, 2025 3:45 PM                             │
│  Model: GPT-4.1                                                  │
│  Evidence Files: evidence1-6.pptx, evidence7+.pptx               │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  EXECUTIVE SUMMARY                                               │
│  ─────────────────                                               │
│                                                                  │
│  Total Elements Evaluated: 55                                    │
│                                                                  │
│    ✅ Pass:        42 (76.4%)                                    │
│    ⚠️ Needs More:   8 (14.5%)                                    │
│    ❌ Fail:         5 (9.1%)                                     │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │          [Summary Bar Chart - Pass/Fail/NeedMore]          │  │
│  │          ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░▒▒▒                     │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ELEMENTS REQUIRING ATTENTION                                    │
│  ────────────────────────────                                    │
│                                                                  │
│  ❌ FAIL (5 elements)                                            │
│  • 2.2 - Calibration Documentation                               │
│  • 3.1 - Process Verification                                    │
│  • 4.3 - Quality Assurance                                       │
│  • 5.2 - Data Integrity                                          │
│  • 6.1 - System Validation                                       │
│                                                                  │
│  ⚠️ NEEDS MORE EVIDENCE (8 elements)                             │
│  • 1.3 - Quality Control                                         │
│  • 2.5 - Equipment Calibration                                   │
│  • ...                                                           │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  DETAILED ELEMENT BREAKDOWN                                      │
│  ─────────────────────────                                       │
│                                                                  │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  Element 1.1: Process Monitoring                                 │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                  │
│  Status: ✅ PASS                                                 │
│  Matching Slides: 2, 3 (from evidence1-6.pptx)                   │
│                                                                  │
│  Element Description:                                            │
│  "The calibration process shall include continuous monitoring    │
│   of key process parameters including temperature, pressure,     │
│   and flow rate."                                                │
│                                                                  │
│  Evaluation Reasoning:                                           │
│  The evidence slides demonstrate comprehensive process           │
│  monitoring capabilities. Slide 2 shows the monitoring           │
│  dashboard with real-time parameter tracking. Slide 3 provides   │
│  historical data analysis showing consistent monitoring over     │
│  the evaluation period.                                          │
│                                                                  │
│  Evidence Text Excerpts:                                         │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ From Slide 2:                                               │  │
│  │ "Process Monitoring Dashboard - Real-time tracking of       │  │
│  │  temperature (±0.5°C), pressure (±1 PSI), and flow rate    │  │
│  │  (±0.1 L/min). All parameters logged at 1-second           │  │
│  │  intervals..."                                              │  │
│  └────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ From Slide 3:                                               │  │
│  │ "Historical Analysis - 6-month monitoring data shows        │  │
│  │  99.7% uptime with automatic alerts triggered for any      │  │
│  │  parameter deviation..."                                    │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  Element 1.2: Data Collection                                    │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                  │
│  Status: ✅ PASS                                                 │
│  ...                                                             │
│                                                                  │
│  [Continues for each element...]                                 │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

#### 6.7.2 Report Content Options (User-Configurable)

| Option | Default | Description |
|--------|---------|-------------|
| Include Passed | ✅ Yes | Include elements with PASS verdict |
| Include Failed | ✅ Yes | Include elements with FAIL verdict |
| Include Needs More | ✅ Yes | Include elements with NEEDS_MORE verdict |
| Include Evidence Excerpts | ✅ Yes | Include text excerpts from matching slides |
| Include Reasoning | ✅ Yes | Include LLM evaluation reasoning |
| Include Element Description | ✅ Yes | Include original element text |

---

#### 6.7.3 Report Generator Implementation

```python
# reports/word_report.py

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from datetime import datetime
from typing import List, Dict, Optional

class ReportGenerator:
    """Generate Word document evaluation report."""
    
    def __init__(self, options: dict = None):
        self.options = options or {
            "include_pass": True,
            "include_fail": True,
            "include_needs_more": True,
            "include_excerpts": True,
            "include_reasoning": True,
            "include_description": True,
        }
        self.doc = Document()
        self._setup_styles()
    
    def _setup_styles(self):
        """Configure document styles."""
        # Title style
        title_style = self.doc.styles['Title']
        title_style.font.size = Pt(24)
        title_style.font.bold = True
        
        # Heading styles
        h1 = self.doc.styles['Heading 1']
        h1.font.size = Pt(16)
        h1.font.color.rgb = RGBColor(0, 0, 0)
    
    def generate(
        self, 
        results: List[Dict],
        model: str,
        evidence_files: List[str],
        output_path: str
    ) -> str:
        """Generate complete report."""
        
        # Title page
        self._add_title_page(model, evidence_files)
        
        # Executive summary
        self._add_executive_summary(results)
        
        # Elements requiring attention
        self._add_attention_section(results)
        
        # Detailed breakdown
        self._add_detailed_breakdown(results)
        
        # Save document
        self.doc.save(output_path)
        return output_path
    
    def _add_title_page(self, model: str, evidence_files: List[str]):
        """Add report title and metadata."""
        self.doc.add_heading('PI Calibration Evidence Evaluation Report', 0)
        
        self.doc.add_paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y %I:%M %p')}")
        self.doc.add_paragraph(f"Model: {model}")
        self.doc.add_paragraph(f"Evidence Files: {', '.join(evidence_files)}")
        self.doc.add_page_break()
    
    def _add_executive_summary(self, results: List[Dict]):
        """Add summary statistics."""
        self.doc.add_heading('Executive Summary', level=1)
        
        # Calculate counts
        pass_count = sum(1 for r in results if r['verdict'] == 'PASS')
        fail_count = sum(1 for r in results if r['verdict'] == 'FAIL')
        needs_count = sum(1 for r in results if r['verdict'] == 'NEEDS_MORE')
        total = len(results)
        
        self.doc.add_paragraph(f"Total Elements Evaluated: {total}")
        self.doc.add_paragraph(f"✅ Pass: {pass_count} ({pass_count/total*100:.1f}%)")
        self.doc.add_paragraph(f"⚠️ Needs More: {needs_count} ({needs_count/total*100:.1f}%)")
        self.doc.add_paragraph(f"❌ Fail: {fail_count} ({fail_count/total*100:.1f}%)")
    
    def _add_attention_section(self, results: List[Dict]):
        """Add section highlighting failed and needs-more elements."""
        self.doc.add_heading('Elements Requiring Attention', level=1)
        
        # Failed elements
        failed = [r for r in results if r['verdict'] == 'FAIL']
        if failed:
            self.doc.add_heading('❌ FAIL', level=2)
            for r in failed:
                self.doc.add_paragraph(f"• {r['element_id']} - {r.get('element_title', '')}")
        
        # Needs more elements
        needs_more = [r for r in results if r['verdict'] == 'NEEDS_MORE']
        if needs_more:
            self.doc.add_heading('⚠️ NEEDS MORE EVIDENCE', level=2)
            for r in needs_more:
                self.doc.add_paragraph(f"• {r['element_id']} - {r.get('element_title', '')}")
    
    def _add_detailed_breakdown(self, results: List[Dict]):
        """Add per-element detailed breakdown."""
        self.doc.add_heading('Detailed Element Breakdown', level=1)
        
        for result in results:
            # Skip based on options
            if result['verdict'] == 'PASS' and not self.options['include_pass']:
                continue
            if result['verdict'] == 'FAIL' and not self.options['include_fail']:
                continue
            if result['verdict'] == 'NEEDS_MORE' and not self.options['include_needs_more']:
                continue
            
            self._add_element_section(result)
    
    def _add_element_section(self, result: Dict):
        """Add single element breakdown."""
        # Element header
        self.doc.add_heading(
            f"Element {result['element_id']}: {result.get('element_title', '')}",
            level=2
        )
        
        # Status with icon
        icon = {"PASS": "✅", "FAIL": "❌", "NEEDS_MORE": "⚠️"}[result['verdict']]
        self.doc.add_paragraph(f"Status: {icon} {result['verdict']}")
        
        # Matching slides
        if result.get('matching_slides'):
            slides_text = ", ".join(str(s['slide_index']) for s in result['matching_slides'])
            sources = ", ".join(set(s['source_file'] for s in result['matching_slides']))
            self.doc.add_paragraph(f"Matching Slides: {slides_text} (from {sources})")
        
        # Element description
        if self.options['include_description'] and result.get('element_text'):
            self.doc.add_heading('Element Description:', level=3)
            self.doc.add_paragraph(result['element_text'])
        
        # Evaluation reasoning
        if self.options['include_reasoning'] and result.get('reasoning'):
            self.doc.add_heading('Evaluation Reasoning:', level=3)
            self.doc.add_paragraph(result['reasoning'])
        
        # Evidence excerpts
        if self.options['include_excerpts'] and result.get('evidence_excerpts'):
            self.doc.add_heading('Evidence Text Excerpts:', level=3)
            for excerpt in result['evidence_excerpts']:
                p = self.doc.add_paragraph()
                p.add_run(f"From Slide {excerpt['slide_index']}:").bold = True
                self.doc.add_paragraph(excerpt['text'][:500] + "..." if len(excerpt['text']) > 500 else excerpt['text'])
```

---

#### 6.7.4 Integration with Streamlit

```python
# In streamlit_app.py

from reports.word_report import ReportGenerator
import io

def generate_report_download():
    """Generate Word report and create download button."""
    
    # Get report options from UI
    options = {
        "include_pass": st.session_state.report_include_pass,
        "include_fail": st.session_state.report_include_fail,
        "include_needs_more": st.session_state.report_include_needs,
        "include_excerpts": st.session_state.report_include_excerpts,
        "include_reasoning": True,
        "include_description": True,
    }
    
    # Generate report to buffer
    generator = ReportGenerator(options)
    buffer = io.BytesIO()
    generator.generate(
        results=st.session_state.results,
        model=st.session_state.selected_model,
        evidence_files=[f.name for f in st.session_state.uploaded_pptx],
        output_path=buffer
    )
    buffer.seek(0)
    
    # Create download button
    st.download_button(
        label="📥 Download Word Report (.docx)",
        data=buffer,
        file_name=f"calibration_report_{datetime.now().strftime('%Y%m%d_%H%M')}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
```

**Estimated Effort:** 8-12 hours

---

### 6.8 Progress Monitoring (Real-time Updates)

**Approach:** Poll `evaluation_progress.json` during pipeline execution

```python
# In Streamlit app
import time

progress_placeholder = st.empty()

while st.session_state.pipeline_status == "running":
    progress_data = load_progress_file()
    
    with progress_placeholder.container():
        st.progress(progress_data["completed"] / progress_data["total"])
        st.write(f"Evaluating: {progress_data['current_element']}")
        
        if progress_data["latest_result"]:
            st.json(progress_data["latest_result"])
    
    time.sleep(1)  # Poll every second
```

### 6.8 Infrastructure as Code (Bicep)

**New files needed in `iac/` directory:**

```
iac/
├── main.bicep              # Existing (Document Intelligence)
├── container-app.bicep     # NEW: Container App + Environment
├── acr.bicep               # NEW: Azure Container Registry
├── identity.bicep          # NEW: Managed Identity + Role Assignments
└── parameters.json         # NEW: Environment-specific values
```

**Key Resources:**
- Azure Container Apps Environment
- Azure Container App (with Easy Auth)
- Azure Container Registry
- System-assigned Managed Identity
- Role assignments for Azure services

### 6.9 CI/CD Pipeline (GitHub Actions)

```yaml
# .github/workflows/deploy.yml
name: Build and Deploy to Azure Container Apps

on:
  push:
    branches: [main]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Login to Azure
        uses: azure/login@v1
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}
      
      - name: Build and push to ACR
        run: |
          az acr build --registry ${{ vars.ACR_NAME }} \
            --image calibration-app:${{ github.sha }} .
      
      - name: Deploy to Container App
        run: |
          az containerapp update \
            --name calibration-app \
            --resource-group ${{ vars.RESOURCE_GROUP }} \
            --image ${{ vars.ACR_NAME }}.azurecr.io/calibration-app:${{ github.sha }}
```

### 6.10 Security Considerations (POC)

1. **Authentication**
   - Open access (no authentication) for POC
   - Single user assumed at a time
   - Future: Add Easy Auth with Microsoft Entra ID if needed

2. **Secrets Management**
   - Environment variables for API keys (acceptable for POC)
   - Future: Use Azure Key Vault + Managed Identity

3. **Network Security**
   - Public ingress (standard for POC)
   - Future: IP restrictions or VNet integration

4. **Data Handling**
   - Uploaded files processed in-memory where possible
   - Temporary files cleaned up after processing
   - No persistent storage of customer data (stateless)

### 6.11 Deployment Effort Estimate (Updated)

| Component | Effort |
|-----------|--------|
| Dockerfile + container setup | 4-6 hours |
| Streamlit app (single page with all features) | 12-16 hours |
| Word Report Generator | 8-12 hours |
| Bicep IaC (Container Apps) | 4-6 hours |
| Managed Identity setup | 2-3 hours |
| CI/CD pipeline (optional) | 2-4 hours |
| Testing & debugging | 6-10 hours |
| **Deployment TOTAL** | **38-57 hours** |

---

## 7. Error Handling Strategy

### 7.1 Stage-Level Errors

| Stage | Possible Errors | Handling |
|-------|-----------------|----------|
| 1 (Excel) | File not found, wrong format, missing columns | Abort with clear message |
| 2 (PPTX) | Rendering failed, no slides found | Abort or skip file |
| 3 (Matching) | No elements found, no evidence | Warn and continue |
| 4 (Evaluation) | LLM timeout, API error | 3 retries, then mark as Error |
| 5 (Report) | Write permission, template error | Abort with message |

### 7.2 Retry Strategy
- LLM calls: 3 retries with exponential backoff (1s, 2s, 4s)
- Azure DI calls: 2 retries
- File operations: No retry, fail fast

---

## 8. Testing Plan

### 8.1 Unit Tests
- [ ] Excel extraction with various formats
- [ ] Element pattern regex matching
- [ ] Evidence-element matching logic
- [ ] LLM response parsing

### 8.2 Integration Tests
- [ ] Full pipeline with sample files
- [ ] Multi-PPTX processing
- [ ] Error recovery scenarios

### 8.3 Sample Data
- Use existing `source-docs/` files for testing:
  - `calib_evidence.xlsx` - Elements
  - `evidence1-6.pptx` - Evidence slides

---

## 9. Estimated Total Effort

### 9.1 Core Pipeline Development (✅ COMPLETED)

| Component | Status | Effort |
|-----------|--------|--------|
| Stage 1 (Excel CLI) | ✅ Done | 2-4 hours |
| Stage 2 (Multi-PPTX) | ✅ Done | 4-6 hours |
| Stage 3 (Matching updates) | ✅ Done | 2-3 hours |
| Stage 4 (Evaluation) | ✅ Done | 0 hours |
| Pipeline Orchestrator | ✅ Done | 8-12 hours |
| Testing | ✅ Done | 4-8 hours |
| Documentation | ✅ Done | 2-4 hours |
| **Pipeline TOTAL** | **COMPLETE** | **22-37 hours** |

### 9.2 Streamlit Frontend & Report Generator

| Component | Status | Effort |
|-----------|--------|--------|
| Streamlit app (full features) | 🔲 Pending | 12-16 hours |
| Word Report Generator | 🔲 Pending | 8-12 hours |
| Frontend Testing | 🔲 Pending | 4-6 hours |
| **Frontend TOTAL** | **Pending** | **24-34 hours** |

### 9.3 Azure Deployment

| Component | Status | Effort |
|-----------|--------|--------|
| Dockerfile + container setup | 🔲 Pending | 4-6 hours |
| Bicep IaC (Container Apps) | 🔲 Pending | 4-6 hours |
| Managed Identity setup | 🔲 Pending | 2-3 hours |
| CI/CD pipeline (optional) | 🔲 Pending | 2-4 hours |
| Deployment Testing | 🔲 Pending | 4-6 hours |
| **Deployment TOTAL** | **Pending** | **16-25 hours** |

### 9.4 Grand Total

| Phase | Status | Effort |
|-------|--------|--------|
| Core Pipeline | ✅ Complete | 22-37 hours |
| Streamlit + Report | 🔲 Pending | 24-34 hours |
| Azure Deployment | 🔲 Pending | 16-25 hours |
| **GRAND TOTAL** | | **62-96 hours** |

---

## 10. Recommended Implementation Order

### Phase 1: Core Pipeline ✅ COMPLETED
- ✅ Pipeline orchestrator (`run_pipeline.py`)
- ✅ Multi-PPTX support with source tracking
- ✅ Evidence-element matching
- ✅ LLM evaluation with progress

### Phase 2: Word Report Generator (NEXT)
1. Create `reports/word_report.py` module
2. Implement `ReportGenerator` class using `python-docx`
3. Add title page, executive summary, attention section
4. Add per-element breakdown with excerpts
5. Test with existing evaluation output
6. Integrate with CLI (`run_pipeline.py --report-format docx`)

### Phase 3: Streamlit Frontend
1. Create `streamlit_app.py` skeleton
2. Build file upload section (Excel + PPTX)
3. Add model selection dropdown
4. Implement element filter (multiselect after Excel upload)
5. Add "Run Pipeline" button with subprocess/threading
6. Build progress monitoring (poll JSON file)
7. Create results table with expandable details
8. Add report options and download buttons
9. Test locally end-to-end

### Phase 4: Containerization
1. Create `Dockerfile` with LibreOffice for slide rendering
2. Create `.dockerignore`
3. Test container build locally
4. Verify pipeline works in container environment
5. Test with sample files

### Phase 5: Azure Deployment
1. Create Azure Container Registry (ACR)
2. Push container image to ACR
3. Create Container Apps Environment
4. Deploy Container App with public ingress
5. Configure environment variables (API keys)
6. Test end-to-end in Azure

### Phase 6: Polish & CI/CD (Optional)
- GitHub Actions for automated builds
- Health checks and monitoring
- Error logging to Application Insights

---

## 11. Open Questions (Resolved & Remaining)

### Resolved Questions ✅

| Question | Decision |
|----------|----------|
| Report Format | Word/DOCX with text excerpts (no screenshots) |
| Multi-PPTX Handling | Continuous sequence with source tracking |
| Error Tolerance | Continue with remaining files |
| Model Selection | User selects from dropdown (GPT-4.1, GPT-5.1) |
| Authentication | Open access for POC (no auth) |
| Concurrent Users | Single user at a time |
| Scaling | Single replica sufficient for POC |

### Remaining Questions ❓

1. **File Size Limits:** What are acceptable limits for:
   - Excel file size (recommended: 10 MB)
   - PPTX file size (recommended: 100 MB per file)
   - Total upload size (recommended: 500 MB)

2. **Processing Timeout:** Large evidence sets may take 30+ minutes.
   - Current approach: Synchronous processing with progress polling
   - May need async job queue for very large files

3. **Data Retention:** Session-only (cleared when user refreshes) for POC.
   - Future: Consider persistent storage if needed

4. **LibreOffice vs Alternative:** Container uses LibreOffice for slide rendering.
   - LibreOffice selected (open source, no licensing)
   - Alternative: Azure-hosted rendering service (if available)

---

## 12. Appendix A: File Structure After Implementation

```
ai-calibration/
├── run_pipeline.py              # Main CLI entry point
├── streamlit_app.py             # Streamlit frontend
├── Dockerfile                   # Container definition
├── .dockerignore                # Docker ignore file
├── matching/
│   ├── __init__.py
│   └── match_evidence.py        # Evidence-element matching
├── evaluation/
│   ├── __init__.py
│   └── evaluate.py              # LLM evaluation CLI
├── utils/
│   ├── __init__.py
│   ├── element_extract.py       # Regex patterns
│   └── slide_to_markdown.py     # Slide text utilities
├── reports/                     # NEW
│   ├── __init__.py
│   └── word_report.py           # Word document generator
├── agents/
│   ├── __init__.py
│   └── evidence_evaluator.py    # LLM agent
├── extractors/
│   ├── __init__.py
│   ├── ppt_extract.py           # Basic PPTX
│   ├── xlsx_extract.py          # Excel parsing
│   └── helpers/
│       ├── multimodal_extract.py # Full PPTX pipeline
│       ├── llm_helpers.py
│       ├── pptx_helpers.py
│       └── di_helpers.py
├── tests/
│   └── ...                      # Test files
├── iac/                         # Infrastructure as Code
│   ├── main.bicep               # Document Intelligence
│   ├── container-app.bicep      # Container App
│   └── parameters.json          # Environment params
├── .github/
│   └── workflows/
│       └── deploy.yml           # CI/CD pipeline (optional)
├── source-docs/                 # Sample data & outputs
├── docs/
│   └── PIPELINE_PLAN.md         # This document
├── requirements.txt
├── .env.example
└── README.md
```

---

## 13. Appendix B: Environment Variables (Complete)

```bash
# ============================================
# Azure Document Intelligence
# ============================================
AZURE_DI_ENDPOINT=https://<resource>.cognitiveservices.azure.com
AZURE_DI_KEY=<key>  # Or use Managed Identity

# ============================================
# Azure OpenAI - GPT-4.1
# ============================================
AZURE_AI_ENDPOINT=https://<resource>.services.ai.azure.com
AZURE_AI_API_KEY=<key>  # Or use Managed Identity
GPT_4_1_DEPLOYMENT=<deployment-name>

# ============================================
# Azure OpenAI - GPT-5.1 (Optional)
# ============================================
AZURE_AI_GPT5_ENDPOINT=https://<resource>.services.ai.azure.com
AZURE_AI_GPT5_API_KEY=<key>
GPT_5_1_DEPLOYMENT=<deployment-name>

# ============================================
# Streamlit Configuration
# ============================================
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_SERVER_HEADLESS=true

# ============================================
# Authentication (set by Easy Auth automatically)
# ============================================
# These are injected by Azure Container Apps Easy Auth:
# - X-MS-CLIENT-PRINCIPAL (base64 encoded user info)
# - X-MS-CLIENT-PRINCIPAL-ID (user object ID)
# - X-MS-CLIENT-PRINCIPAL-NAME (user email/UPN)
```

---

## 14. Appendix C: Bicep Template Overview (Simplified - No Auth)

### container-app.bicep

```bicep
param location string = resourceGroup().location
param containerAppName string = 'calibration-app'
param containerAppEnvName string = 'calibration-env'
param acrName string
param imageName string

resource containerAppEnv 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: containerAppEnvName
  location: location
  properties: {}
}

resource containerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: containerAppName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: containerAppEnv.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8501
        transport: 'http'
      }
      registries: [
        {
          server: '${acrName}.azurecr.io'
          identity: 'system'
        }
      ]
      secrets: [
        {
          name: 'azure-ai-endpoint'
          value: '<your-azure-openai-endpoint>'
        }
        {
          name: 'azure-ai-key'
          value: '<your-azure-openai-key>'
        }
        {
          name: 'azure-di-endpoint'
          value: '<your-doc-intel-endpoint>'
        }
        {
          name: 'azure-di-key'
          value: '<your-doc-intel-key>'
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'calibration-app'
          image: imageName
          resources: {
            cpu: json('2.0')
            memory: '4Gi'
          }
          env: [
            { name: 'AZURE_AI_ENDPOINT', secretRef: 'azure-ai-endpoint' }
            { name: 'AZURE_AI_API_KEY', secretRef: 'azure-ai-key' }
            { name: 'AZURE_DI_ENDPOINT', secretRef: 'azure-di-endpoint' }
            { name: 'AZURE_DI_KEY', secretRef: 'azure-di-key' }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 1  // Single user, no scaling needed
      }
    }
  }
}

// No authentication for POC - open access
// Future: Add Easy Auth with Microsoft Entra ID if needed

output containerAppUrl string = 'https://${containerApp.properties.configuration.ingress.fqdn}'
output managedIdentityPrincipalId string = containerApp.identity.principalId
```

---

## 15. Appendix D: Dependencies (requirements.txt additions)

```txt
# Add to existing requirements.txt for Streamlit + Report
streamlit>=1.28.0
python-docx>=0.8.11
watchdog>=3.0.0  # For Streamlit file watching
```
