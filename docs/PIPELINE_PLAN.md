# GM Calibration Evidence Evaluation Pipeline
## Planning Document

**Version:** 1.0  
**Date:** December 8, 2025  
**Status:** Planning

---

## 1. Executive Summary

This document outlines the plan to consolidate existing components into a unified end-to-end pipeline that:
1. Accepts an Excel file containing PI calibration elements
2. Accepts one or more PowerPoint files containing evidence slides
3. Processes through extraction, matching, and LLM evaluation
4. Produces a final evaluation report

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

### 6.2 Authentication Strategy: Microsoft Entra ID

**Approach:** Use Microsoft Entra ID (Azure AD) for authentication via Azure Container Apps Easy Auth.

**Benefits:**
- No custom auth code required
- SSO with Microsoft 365 accounts
- Role-based access control (RBAC) possible
- Managed identity for backend Azure services (no API keys in code)

**Implementation:**
1. **Easy Auth Configuration** - Enable built-in authentication on Container App
2. **Allowed Users** - Configure allowed tenant/users in Entra ID app registration
3. **Managed Identity** - Use system-assigned managed identity for Azure OpenAI, Document Intelligence, and Blob Storage access

### 6.3 Azure Container Apps Configuration

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

### 6.6 Streamlit Application Design (POC - Minimal)

**File:** `streamlit_app.py` (single file, ~100-150 lines)

**Goal:** Super simple frontend to demonstrate the pipeline capability.

**Single Page Layout:**
```
┌─────────────────────────────────────────────────────┐
│  🔍 GM Calibration Evidence Evaluator (POC)         │
├─────────────────────────────────────────────────────┤
│                                                     │
│  📁 Upload Files                                    │
│  ┌───────────────────────────────────────────────┐  │
│  │ [Excel File]     [Browse...]                  │  │
│  │ [PPTX File(s)]   [Browse...]                  │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│  [▶ Run Evaluation]                                 │
│                                                     │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 45%              │
│  Evaluating element 2.3...                          │
│                                                     │
│  📊 Results (live)                                  │
│  ┌───────────────────────────────────────────────┐  │
│  │ Element │ Status              │ Slides        │  │
│  │─────────│─────────────────────│───────────────│  │
│  │ 1.1     │ ✅ Pass             │ 2, 3          │  │
│  │ 1.2     │ ❓ Needs Evidence   │ -             │  │
│  │ 2.1     │ ✅ Pass             │ 6             │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│  [📥 Download Results JSON]                         │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Features (POC only):**
- Single page (no multi-page navigation)
- File uploaders for Excel + PPTX
- One "Run" button
- Progress bar + current element text
- Simple results table (st.dataframe)
- Download button for JSON results

**Not Included (Future):**
- ❌ Configuration options
- ❌ Model selection
- ❌ Charts/visualizations  
- ❌ Filtering/sorting
- ❌ Expandable details
- ❌ Excel/PDF report download

**Estimated Effort:** 4-6 hours (down from 16-24)

### 6.7 Progress Monitoring (Real-time Updates)

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

### 6.10 Security Considerations

1. **Authentication**
   - Microsoft Entra ID via Easy Auth (no custom auth code)
   - Restrict to specific tenant/security groups

2. **Secrets Management**
   - Use Azure Key Vault for sensitive configuration
   - Managed Identity for service-to-service auth
   - No API keys in environment variables or code

3. **Network Security**
   - Container App ingress can be restricted to specific IPs
   - Consider VNet integration for enterprise deployment
   - All Azure service calls use private endpoints (optional)

4. **Data Handling**
   - Uploaded files processed in-memory where possible
   - Temporary files cleaned up after processing
   - No persistent storage of customer data (stateless)

### 6.11 Deployment Effort Estimate

| Component | Effort |
|-----------|--------|
| Dockerfile + container setup | 4-6 hours |
| Streamlit app (5 pages) | 16-24 hours |
| Bicep IaC (Container Apps) | 4-8 hours |
| Entra ID / Easy Auth config | 2-4 hours |
| Managed Identity setup | 2-3 hours |
| CI/CD pipeline | 2-4 hours |
| Testing & debugging | 8-12 hours |
| **Deployment TOTAL** | **38-61 hours** |

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

### 9.1 Core Pipeline Development

| Component | Effort |
|-----------|--------|
| Stage 1 (Excel CLI) | 2-4 hours |
| Stage 2 (Multi-PPTX) | 4-6 hours |
| Stage 3 (Matching updates) | 2-3 hours |
| Stage 4 (Evaluation) | 0 hours (done) |
| Stage 5 (Report Generation) | 8-16 hours |
| Pipeline Orchestrator | 8-12 hours |
| Testing | 4-8 hours |
| Documentation | 2-4 hours |
| **Pipeline TOTAL** | **30-53 hours** |

### 9.2 Azure Deployment & Streamlit Frontend (POC)

| Component | Effort |
|-----------|--------|
| Dockerfile + container setup | 4-6 hours |
| Streamlit app (single page POC) | 4-6 hours |
| Bicep IaC (Container Apps) | 4-8 hours |
| Entra ID / Easy Auth config | 2-4 hours |
| Managed Identity setup | 2-3 hours |
| CI/CD pipeline | 2-4 hours |
| Testing & debugging | 4-6 hours |
| **Deployment TOTAL** | **22-37 hours** |

### 9.3 Grand Total

| Phase | Effort |
|-------|--------|
| Core Pipeline | 30-53 hours |
| Azure Deployment + Streamlit (POC) | 22-37 hours |
| **GRAND TOTAL** | **52-90 hours** |

---

## 10. Recommended Implementation Order

### Phase 1: Core Pipeline (Priority)
- Pipeline orchestrator (`run_pipeline.py`)
- Multi-PPTX support
- Basic Excel report generation

### Phase 2: Containerization
- Dockerfile with LibreOffice
- Local container testing
- Verify pipeline works in container

### Phase 3: Azure Infrastructure
- Bicep templates for Container Apps
- Azure Container Registry setup
- Managed Identity configuration

### Phase 4: Streamlit Frontend
- Basic upload + processing flow
- Progress visualization
- Results dashboard

### Phase 5: Authentication & Security
- Entra ID app registration
- Easy Auth configuration
- Role-based access (if needed)

### Phase 6: CI/CD & Polish
- GitHub Actions workflow
- Automated deployments
- Monitoring and logging

---

## 11. Open Questions

### Pipeline Questions

1. **Report Format Priority:** Which format is most important for calibrators? (Excel recommended for initial version)

2. **Multi-PPTX Handling:** Should evidence from multiple files be treated as:
   - One continuous sequence (current assumption)
   - Separate evidence sets per file

3. **Error Tolerance:** If one PPTX fails to process, should the pipeline:
   - Abort entirely
   - Continue with remaining files (recommended)

4. **Intermediate Files:** Should intermediate JSON files be:
   - Kept for debugging
   - Cleaned up after successful completion
   - User-configurable

5. **Model Selection:** Should the pipeline:
   - Use same model for extraction and evaluation
   - Allow different models per stage

### Deployment Questions

6. **Tenant Restriction:** Should access be limited to:
   - Single tenant (GM employees only)
   - Specific security groups
   - Anyone with Microsoft account (not recommended)

7. **File Size Limits:** What are acceptable limits for:
   - Excel file size (recommended: 10 MB)
   - PPTX file size (recommended: 100 MB per file)
   - Total upload size (recommended: 500 MB)

8. **Processing Timeout:** Large evidence sets may take 30+ minutes. Should we:
   - Use async processing with job status polling
   - Extend HTTP request timeout
   - Implement background job queue

9. **Data Retention:** How long should results be kept?
   - Session only (cleared on logout)
   - 24 hours
   - User-configurable

10. **Scaling Strategy:** Expected concurrent users?
    - Low volume: Single replica sufficient
    - High volume: Configure autoscaling rules

11. **LibreOffice vs Alternative:** Container uses LibreOffice for slide rendering. Consider:
    - LibreOffice (current plan, open source)
    - Azure-hosted rendering service (if available)
    - Pre-render slides client-side before upload

---

## 12. Appendix A: File Structure After Implementation

```
ai-calibration/
├── run_pipeline.py              # NEW: Main entry point
├── streamlit_app.py             # NEW: Streamlit frontend (single file POC)
├── evaluate_evidence.py         # Existing: Stage 4
├── match_evidence_to_elements.py # Existing: Stage 3
├── Dockerfile                   # NEW: Container definition
├── .dockerignore                # NEW: Docker ignore file
├── agents/
│   ├── __init__.py
│   └── evidence_evaluator.py    # Existing: LLM agent
├── extractors/
│   ├── __init__.py
│   ├── ppt_extract.py           # Existing: Basic PPTX
│   ├── xlsx_extract.py          # Existing: Excel parsing
│   └── helpers/
│       ├── multimodal_extract.py # Existing: Full PPTX pipeline
│       ├── llm_helpers.py
│       └── ...
├── helper/
│   └── element_extract.py       # Existing: Regex patterns
├── reports/                     # NEW: Report generation
│   ├── __init__.py
│   └── excel_report.py
├── iac/                         # Infrastructure as Code
│   ├── main.bicep               # Existing (Document Intelligence)
│   ├── container-app.bicep      # NEW: Container App
│   ├── acr.bicep                # NEW: Container Registry
│   ├── identity.bicep           # NEW: Managed Identity
│   └── parameters.json          # NEW: Environment params
├── .github/
│   └── workflows/
│       └── deploy.yml           # NEW: CI/CD pipeline
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
# Azure Blob Storage (Optional - for file staging)
# ============================================
AZURE_STORAGE_ACCOUNT=<storage-account-name>
AZURE_STORAGE_CONTAINER=calibration-files

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

## 14. Appendix C: Bicep Template Overview

### container-app.bicep (Simplified)

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
        }
      ]
      scale: {
        minReplicas: 0
        maxReplicas: 3
      }
    }
  }
}

// Enable Easy Auth (Microsoft Entra ID)
resource authConfig 'Microsoft.App/containerApps/authConfigs@2023-05-01' = {
  parent: containerApp
  name: 'current'
  properties: {
    platform: {
      enabled: true
    }
    globalValidation: {
      unauthenticatedClientAction: 'RedirectToLoginPage'
    }
    identityProviders: {
      azureActiveDirectory: {
        enabled: true
        registration: {
          clientId: '<app-registration-client-id>'
          openIdIssuer: 'https://login.microsoftonline.com/<tenant-id>/v2.0'
        }
        validation: {
          allowedAudiences: [
            'api://<app-registration-client-id>'
          ]
        }
      }
    }
  }
}

output containerAppUrl string = 'https://${containerApp.properties.configuration.ingress.fqdn}'
output managedIdentityPrincipalId string = containerApp.identity.principalId
```
