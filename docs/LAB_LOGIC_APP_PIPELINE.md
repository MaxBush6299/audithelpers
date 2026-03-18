# Lab: Rebuilding the PI Calibration Pipeline as an Azure Logic App

## Overview

In this lab, you will rebuild the existing Python-based PI Calibration Evidence Evaluation pipeline as an **Azure Logic App (Standard)** workflow that is automatically triggered when files are uploaded to an Azure Blob Storage container.

### What You'll Build

```
┌──────────────────────────────────────────────────────────────────────┐
│                     Blob Storage Container                           │
│   "calibration-inbox"                                                │
│   ├── job-001/                                                       │
│   │   ├── calib_evidence.xlsx       ← Elements definition            │
│   │   └── evidence1-6.pptx          ← Evidence slides                │
│   └── job-002/                                                       │
│       ├── calib_evidence.xlsx                                        │
│       └── evidence1-6.pptx                                          │
└──────────────────────┬───────────────────────────────────────────────┘
                       │ Blob trigger (new blob detected)
                       ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    Azure Logic App (Standard)                        │
│                                                                      │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌───────┐│
│  │ Stage 1  │──▶│ Stage 2  │──▶│ Stage 3  │──▶│ Stage 4  │──▶│Stage 5││
│  │ Extract  │   │ Extract  │   │ Match    │   │ Evaluate │   │Report ││
│  │ Elements │   │ Evidence │   │ Evidence │   │ w/ LLM   │   │ Gen   ││
│  │ (Excel)  │   │ (PPTX)  │   │          │   │          │   │       ││
│  └─────────┘   └─────────┘   └─────────┘   └─────────┘   └───────┘│
│       │              │             │              │            │      │
│       ▼              ▼             ▼              ▼            ▼      │
│   elements.json  evidence.json  matched.json  results.json report.docx│
│                                                                      │
│   All outputs written to: "calibration-results/{job-id}/"            │
└──────────────────────────────────────────────────────────────────────┘
```

### Current Pipeline vs. Logic App Pipeline

| Aspect | Current (Python CLI) | Logic App Pipeline |
|--------|---------------------|--------------------|
| Trigger | Manual (`python run_pipeline.py`) | Automatic (blob upload) |
| Compute | Local machine / Container App | Logic App + Azure Functions |
| Orchestration | Python script (`run_pipeline.py`) | Logic App workflow designer |
| State | Local files on disk | Blob Storage containers |
| Monitoring | Console output | Logic App run history + Application Insights |
| Scaling | Single execution | Concurrent job processing |

### Prerequisites

- An Azure subscription with Contributor access
- Azure CLI installed and logged in (`az login`)
- VS Code with the **Azure Logic Apps (Standard)** extension
- Python 3.10+ (for Azure Functions development)
- An existing Azure OpenAI resource with a GPT-4.1 (or later) deployment
- An existing Azure Document Intelligence resource
- An Azure Storage Account

---

## Lab Architecture

The Logic App will orchestrate **five Azure Functions**, one for each pipeline stage. Each Function reads its input from Blob Storage and writes its output back to Blob Storage. The Logic App chains them together and handles errors.

```
Logic App Workflow
│
├── Trigger: "When a blob is added" (calibration-inbox/{job-id}/*.pptx)
│
├── Action: Get job metadata (list blobs in job folder)
│
├── Action: Call Function → Stage 1: Extract Elements (xlsx → elements.json)
│
├── Action: Call Function → Stage 2: Extract Evidence (pptx → evidence.json)
│
├── Action: Call Function → Stage 3: Match Evidence (elements + evidence → matched.json)
│
├── Action: Call Function → Stage 4: Evaluate Evidence (matched → results.json)
│
├── Action: Call Function → Stage 5: Generate Report (results → report.docx)
│
├── Action: Send notification (email/Teams with result summary)
│
└── Action: Move processed files to "calibration-archive/{job-id}/"
```

---

## Exercise 1: Set Up Azure Resources

### Step 1.1: Create a Resource Group

```bash
az group create \
  --name rg-calibration-pipeline \
  --location eastus2
```

### Step 1.2: Create a Storage Account

This storage account will hold input files, intermediate outputs, and final results.

```bash
az storage account create \
  --name stcalibpipeline \
  --resource-group rg-calibration-pipeline \
  --location eastus2 \
  --sku Standard_LRS \
  --kind StorageV2
```

### Step 1.3: Create Blob Containers

```bash
# Get the connection string
CONN_STR=$(az storage account show-connection-string \
  --name stcalibpipeline \
  --resource-group rg-calibration-pipeline \
  --query connectionString -o tsv)

# Create containers
az storage container create --name calibration-inbox --connection-string "$CONN_STR"
az storage container create --name calibration-results --connection-string "$CONN_STR"
az storage container create --name calibration-archive --connection-string "$CONN_STR"
az storage container create --name calibration-cache --connection-string "$CONN_STR"
```

**Container purposes:**

| Container | Purpose |
|-----------|---------|
| `calibration-inbox` | Upload input files here (xlsx + pptx in job folders) |
| `calibration-results` | Pipeline writes all outputs here |
| `calibration-archive` | Processed inputs are moved here after completion |
| `calibration-cache` | Caches extraction results to avoid re-processing |

### Step 1.4: Create a Logic App (Standard)

```bash
# Create an App Service Plan for the Logic App (WS1 = Workflow Standard 1)
az appservice plan create \
  --name plan-calibration-logic \
  --resource-group rg-calibration-pipeline \
  --location eastus2 \
  --sku WS1

# Create the Logic App
az logicapp create \
  --name logic-calibration-pipeline \
  --resource-group rg-calibration-pipeline \
  --plan plan-calibration-logic \
  --storage-account stcalibpipeline
```

### Step 1.5: Create a Function App (for pipeline stage functions)

```bash
az functionapp create \
  --name func-calibration-stages \
  --resource-group rg-calibration-pipeline \
  --storage-account stcalibpipeline \
  --consumption-plan-location eastus2 \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --os-type Linux
```

### Step 1.6: Configure Application Settings

Set environment variables that mirror what the current pipeline reads from `.env`:

```bash
az functionapp config appsettings set \
  --name func-calibration-stages \
  --resource-group rg-calibration-pipeline \
  --settings \
    "AZURE_OPENAI_ENDPOINT=https://<your-openai-resource>.openai.azure.com/" \
    "AZURE_OPENAI_API_KEY=<your-api-key>" \
    "AZURE_OPENAI_DEPLOYMENT=gpt-41" \
    "AZURE_DI_ENDPOINT=https://<your-di-resource>.cognitiveservices.azure.com/" \
    "AZURE_DI_KEY=<your-di-key>" \
    "AZURE_STORAGE_CONNECTION_STRING=$CONN_STR"
```

> **Security Note:** In production, use **Key Vault references** or **Managed Identity** instead of storing secrets in app settings. See [Step 1.7](#step-17-optional-configure-managed-identity) for the recommended approach.

### Step 1.7: (Optional) Configure Managed Identity

```bash
# Enable system-assigned managed identity on the Function App
az functionapp identity assign \
  --name func-calibration-stages \
  --resource-group rg-calibration-pipeline

# Get the principal ID
PRINCIPAL_ID=$(az functionapp identity show \
  --name func-calibration-stages \
  --resource-group rg-calibration-pipeline \
  --query principalId -o tsv)

# Grant Storage Blob Data Contributor on the storage account
STORAGE_ID=$(az storage account show \
  --name stcalibpipeline \
  --resource-group rg-calibration-pipeline \
  --query id -o tsv)

az role assignment create \
  --assignee "$PRINCIPAL_ID" \
  --role "Storage Blob Data Contributor" \
  --scope "$STORAGE_ID"
```

---

## Exercise 2: Build the Azure Functions (Pipeline Stages)

Each pipeline stage becomes an HTTP-triggered Azure Function. The Logic App will call each Function, passing blob paths as parameters.

### Step 2.1: Initialize the Function App Project

```bash
mkdir calibration-functions
cd calibration-functions
func init --python --model v2
```

### Step 2.2: Define Shared Utilities

Create a shared helpers module that all functions will use for Blob I/O.

**File: `shared/blob_io.py`**

```python
"""Shared blob I/O utilities for all pipeline stage functions."""
import json
import os
from io import BytesIO
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential


def get_blob_service() -> BlobServiceClient:
    """Get BlobServiceClient using connection string or managed identity."""
    conn_str = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
    if conn_str:
        return BlobServiceClient.from_connection_string(conn_str)
    
    account_name = os.environ.get("AZURE_STORAGE_ACCOUNT_NAME", "stcalibpipeline")
    return BlobServiceClient(
        account_url=f"https://{account_name}.blob.core.windows.net",
        credential=DefaultAzureCredential()
    )


def read_blob_bytes(container: str, blob_path: str) -> bytes:
    """Read a blob and return its bytes."""
    client = get_blob_service()
    blob_client = client.get_blob_client(container, blob_path)
    return blob_client.download_blob().readall()


def read_blob_json(container: str, blob_path: str) -> dict:
    """Read a blob and parse it as JSON."""
    data = read_blob_bytes(container, blob_path)
    return json.loads(data.decode("utf-8"))


def write_blob_json(container: str, blob_path: str, data: dict) -> str:
    """Write a dict as JSON to a blob. Returns the blob path."""
    client = get_blob_service()
    blob_client = client.get_blob_client(container, blob_path)
    content = json.dumps(data, indent=2, ensure_ascii=False)
    blob_client.upload_blob(content.encode("utf-8"), overwrite=True)
    return blob_path


def write_blob_bytes(container: str, blob_path: str, data: bytes,
                     content_type: str = "application/octet-stream") -> str:
    """Write bytes to a blob. Returns the blob path."""
    from azure.storage.blob import ContentSettings
    client = get_blob_service()
    blob_client = client.get_blob_client(container, blob_path)
    blob_client.upload_blob(
        data, overwrite=True,
        content_settings=ContentSettings(content_type=content_type)
    )
    return blob_path


def list_blobs_in_folder(container: str, folder_prefix: str) -> list[str]:
    """List all blob names under a folder prefix."""
    client = get_blob_service()
    container_client = client.get_container_client(container)
    return [
        blob.name for blob in container_client.list_blobs(name_starts_with=folder_prefix)
    ]
```

Create `shared/__init__.py`:

```python
from .blob_io import (
    read_blob_bytes,
    read_blob_json,
    write_blob_json,
    write_blob_bytes,
    list_blobs_in_folder,
)
```

### Step 2.3: Stage 1 Function — Extract Elements from Excel

This function replaces the `run_stage1_excel_extraction()` call in `run_pipeline.py`. It reads the Excel file from blob storage and writes `elements.json` to the results container.

**File: `function_app.py`** (add this function)

```python
import azure.functions as func
import json
import logging
import os
from io import BytesIO

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


@app.function_name("stage1_extract_elements")
@app.route(route="stage1", methods=["POST"])
def stage1_extract_elements(req: func.HttpRequest) -> func.HttpResponse:
    """
    Stage 1: Extract PI elements from an Excel file in blob storage.
    
    Request body:
    {
        "job_id": "job-001",
        "xlsx_blob": "job-001/calib_evidence.xlsx"
    }
    
    Response:
    {
        "job_id": "job-001",
        "elements_blob": "job-001/elements.json",
        "elements_count": 42
    }
    """
    try:
        body = req.get_json()
        job_id = body["job_id"]
        xlsx_blob = body["xlsx_blob"]
        
        logging.info(f"[Stage 1] Job {job_id}: Extracting elements from {xlsx_blob}")
        
        # Read Excel file from blob storage
        from shared.blob_io import read_blob_bytes, write_blob_json
        xlsx_bytes = read_blob_bytes("calibration-inbox", xlsx_blob)
        
        # Use the existing extraction logic
        from extractors.xlsx_extract import extract_pi_rows_xlsx
        elements = extract_pi_rows_xlsx(BytesIO(xlsx_bytes), verbose=False)
        
        # Write output to results container
        output_blob = f"{job_id}/elements.json"
        write_blob_json("calibration-results", output_blob, elements)
        
        return func.HttpResponse(
            json.dumps({
                "job_id": job_id,
                "elements_blob": output_blob,
                "elements_count": len(elements)
            }),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        logging.error(f"[Stage 1] Error: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )
```

### Step 2.4: Stage 2 Function — Extract Evidence from PPTX

This is the most compute-intensive stage. It reads the PPTX from blob, uses Document Intelligence for OCR, renders slides, and calls the LLM for multimodal extraction.

**Add to `function_app.py`:**

```python
@app.function_name("stage2_extract_evidence")
@app.route(route="stage2", methods=["POST"])
def stage2_extract_evidence(req: func.HttpRequest) -> func.HttpResponse:
    """
    Stage 2: Extract evidence from PPTX using multimodal LLM.
    
    Request body:
    {
        "job_id": "job-001",
        "pptx_blobs": ["job-001/evidence1-6.pptx"]
    }
    
    Response:
    {
        "job_id": "job-001",
        "evidence_blob": "job-001/evidence.json",
        "total_slides": 25
    }
    """
    try:
        body = req.get_json()
        job_id = body["job_id"]
        pptx_blobs = body["pptx_blobs"]
        
        logging.info(f"[Stage 2] Job {job_id}: Extracting evidence from {len(pptx_blobs)} file(s)")
        
        from shared.blob_io import read_blob_bytes, write_blob_json
        from extractors.helpers.multimodal_extract import quick_extract, quick_extract_multi
        import tempfile
        
        # Download PPTX files to a temp directory (needed for python-pptx)
        with tempfile.TemporaryDirectory() as tmp_dir:
            local_paths = []
            for blob_name in pptx_blobs:
                pptx_bytes = read_blob_bytes("calibration-inbox", blob_name)
                filename = blob_name.split("/")[-1]
                local_path = os.path.join(tmp_dir, filename)
                with open(local_path, "wb") as f:
                    f.write(pptx_bytes)
                local_paths.append(local_path)
            
            # Run extraction
            output_path = os.path.join(tmp_dir, "evidence.json")
            model = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-41")
            
            if len(local_paths) == 1:
                evidence = quick_extract(
                    local_paths[0],
                    output_path=output_path,
                    verbose=False,
                    use_di=True,
                    model=model,
                    use_cache=False
                )
            else:
                evidence = quick_extract_multi(
                    local_paths,
                    output_path=output_path,
                    verbose=False,
                    use_di=True,
                    model=model,
                    use_cache=False
                )
        
        # Write to results container
        output_blob = f"{job_id}/evidence.json"
        write_blob_json("calibration-results", output_blob, evidence)
        
        total_slides = evidence.get("total_slides", len(evidence.get("slides", [])))
        
        return func.HttpResponse(
            json.dumps({
                "job_id": job_id,
                "evidence_blob": output_blob,
                "total_slides": total_slides
            }),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        logging.error(f"[Stage 2] Error: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )
```

### Step 2.5: Stage 3 Function — Match Evidence to Elements

**Add to `function_app.py`:**

```python
@app.function_name("stage3_match_evidence")
@app.route(route="stage3", methods=["POST"])
def stage3_match_evidence(req: func.HttpRequest) -> func.HttpResponse:
    """
    Stage 3: Match evidence slides to PI elements.
    
    Request body:
    {
        "job_id": "job-001",
        "elements_blob": "job-001/elements.json",
        "evidence_blob": "job-001/evidence.json"
    }
    """
    try:
        body = req.get_json()
        job_id = body["job_id"]
        elements_blob = body["elements_blob"]
        evidence_blob = body["evidence_blob"]
        
        logging.info(f"[Stage 3] Job {job_id}: Matching evidence to elements")
        
        from shared.blob_io import read_blob_json, write_blob_json
        from matching.match_evidence import (
            build_elements_lookup,
            match_slides_to_elements,
            serialize_result
        )
        
        # Read inputs from results container
        elements = read_blob_json("calibration-results", elements_blob)
        evidence = read_blob_json("calibration-results", evidence_blob)
        
        # Run matching
        elements_lookup = build_elements_lookup(elements)
        result = match_slides_to_elements(evidence, elements_lookup)
        output_data = serialize_result(result)
        
        # Write output
        output_blob = f"{job_id}/matched_evidence.json"
        write_blob_json("calibration-results", output_blob, output_data)
        
        stats = result.statistics
        
        return func.HttpResponse(
            json.dumps({
                "job_id": job_id,
                "matched_blob": output_blob,
                "matched_slides": stats["matched_slides"],
                "elements_with_evidence": stats["elements_with_evidence"]
            }),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        logging.error(f"[Stage 3] Error: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )
```

### Step 2.6: Stage 4 Function — Evaluate Evidence with LLM

**Add to `function_app.py`:**

```python
@app.function_name("stage4_evaluate")
@app.route(route="stage4", methods=["POST"])
def stage4_evaluate(req: func.HttpRequest) -> func.HttpResponse:
    """
    Stage 4: Evaluate evidence with LLM agent.
    
    Request body:
    {
        "job_id": "job-001",
        "matched_blob": "job-001/matched_evidence.json"
    }
    """
    try:
        body = req.get_json()
        job_id = body["job_id"]
        matched_blob = body["matched_blob"]
        
        logging.info(f"[Stage 4] Job {job_id}: Evaluating evidence with LLM")
        
        from shared.blob_io import read_blob_json, write_blob_json
        from agents.evidence_evaluator import EvidenceEvaluationAgent, EvaluationStatus
        
        # Read matched evidence
        matched_data = read_blob_json("calibration-results", matched_blob)
        matched_elements = matched_data.get("matched_elements", [])
        
        # Initialize the evaluation agent
        agent = EvidenceEvaluationAgent()
        
        results = []
        stats = {"pass": 0, "fail": 0, "needs_more_evidence": 0, "error": 0}
        
        for element in matched_elements:
            pi_element = element.get("pi_element", "Unknown")
            ask_look_for = element.get("ask_look_for", "")
            calibrator_notes = element.get("calibrator_notes", "")
            evidence_slides = element.get("evidence_slides", [])
            
            # Build evidence text
            evidence_text = "\n\n".join([
                f"--- Slide {s.get('slide_number', '?')} ---\n{s.get('text', '')}"
                for s in evidence_slides
            ])
            
            # Evaluate
            eval_result = agent.evaluate(
                pi_element=pi_element,
                ask_look_for=ask_look_for,
                calibrator_notes=calibrator_notes,
                evidence_text=evidence_text
            )
            
            result_dict = eval_result.to_dict()
            results.append(result_dict)
            
            # Update statistics
            status_key = eval_result.status.value.lower().replace(" ", "_")
            stats[status_key] = stats.get(status_key, 0) + 1
        
        # Write results
        output_data = {
            "job_id": job_id,
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "statistics": stats,
            "total_elements": len(matched_elements),
            "results": results
        }
        
        output_blob = f"{job_id}/evaluation_results.json"
        write_blob_json("calibration-results", output_blob, output_data)
        
        return func.HttpResponse(
            json.dumps({
                "job_id": job_id,
                "evaluation_blob": output_blob,
                "statistics": stats
            }),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        logging.error(f"[Stage 4] Error: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )
```

### Step 2.7: Stage 5 Function — Generate Word Report

**Add to `function_app.py`:**

```python
@app.function_name("stage5_report")
@app.route(route="stage5", methods=["POST"])
def stage5_report(req: func.HttpRequest) -> func.HttpResponse:
    """
    Stage 5: Generate Word report from evaluation results.
    
    Request body:
    {
        "job_id": "job-001",
        "evaluation_blob": "job-001/evaluation_results.json",
        "matched_blob": "job-001/matched_evidence.json"
    }
    """
    try:
        body = req.get_json()
        job_id = body["job_id"]
        evaluation_blob = body["evaluation_blob"]
        matched_blob = body["matched_blob"]
        
        logging.info(f"[Stage 5] Job {job_id}: Generating Word report")
        
        from shared.blob_io import read_blob_json, write_blob_bytes
        from reports.word_report import generate_word_report
        import tempfile
        
        # Download the JSON files to temp for the report generator
        with tempfile.TemporaryDirectory() as tmp_dir:
            import json
            
            eval_data = read_blob_json("calibration-results", evaluation_blob)
            matched_data = read_blob_json("calibration-results", matched_blob)
            
            eval_path = os.path.join(tmp_dir, "evaluation_results.json")
            matched_path = os.path.join(tmp_dir, "matched_evidence.json")
            report_path = os.path.join(tmp_dir, "evaluation_report.docx")
            
            with open(eval_path, "w", encoding="utf-8") as f:
                json.dump(eval_data, f, indent=2, ensure_ascii=False)
            with open(matched_path, "w", encoding="utf-8") as f:
                json.dump(matched_data, f, indent=2, ensure_ascii=False)
            
            # Generate report
            generate_word_report(
                evaluation_results_path=eval_path,
                output_path=report_path,
                matched_evidence_path=matched_path,
                evidence_files=["evidence.pptx"],
                options={
                    "include_pass": True,
                    "include_fail": True,
                    "include_needs_more": True,
                    "include_excerpts": True,
                    "include_reasoning": True,
                    "include_description": True,
                    "max_excerpt_length": 500,
                }
            )
            
            # Read the generated report
            with open(report_path, "rb") as f:
                report_bytes = f.read()
        
        # Upload report to results container
        output_blob = f"{job_id}/evaluation_report.docx"
        write_blob_bytes(
            "calibration-results", output_blob, report_bytes,
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
        return func.HttpResponse(
            json.dumps({
                "job_id": job_id,
                "report_blob": output_blob
            }),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        logging.error(f"[Stage 5] Error: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )
```

### Step 2.8: Add the Requirements File

**File: `requirements.txt`**

```
azure-functions
azure-storage-blob>=12.0.0
azure-identity>=1.0.0
azure-ai-documentintelligence>=1.0.0
openai>=1.0.0
openpyxl>=3.0.0
python-pptx>=0.6.21
python-docx>=0.8.11
pymupdf>=1.24.0
python-dotenv>=1.0.0
```

### Step 2.9: Copy Existing Pipeline Code

The Functions reference the existing extractors, matching, agents, and reports modules. Copy them into the Function App project:

```bash
# From the ai-calibration project root:
cp -r extractors/ calibration-functions/extractors/
cp -r matching/   calibration-functions/matching/
cp -r agents/     calibration-functions/agents/
cp -r reports/    calibration-functions/reports/
cp -r utils/      calibration-functions/utils/
```

> **Note:** In production, you would publish these as a shared Python package. For this lab, copying them directly is fine.

### Step 2.10: Deploy the Function App

```bash
cd calibration-functions

# Deploy to Azure
func azure functionapp publish func-calibration-stages
```

Verify the deployment:

```bash
# List deployed functions
az functionapp function list \
  --name func-calibration-stages \
  --resource-group rg-calibration-pipeline \
  --output table
```

You should see five functions listed:
- `stage1_extract_elements`
- `stage2_extract_evidence`
- `stage3_match_evidence`
- `stage4_evaluate`
- `stage5_report`

---

## Exercise 3: Build the Logic App Workflow

Now that the Functions are deployed, you'll create the Logic App workflow that orchestrates them.

### Step 3.1: Open the Logic App in VS Code

1. Open VS Code
2. Install the **Azure Logic Apps (Standard)** extension if not already installed
3. Open the Azure sidebar panel (Ctrl+Shift+A)
4. Under **Logic Apps**, find `logic-calibration-pipeline`
5. Right-click → **Open in Designer**

### Step 3.2: Create a New Workflow

1. In the Logic App project, create a new folder: `calibration-pipeline/`
2. Inside it, create `workflow.json`

Here is the complete workflow definition. We'll walk through each section below.

**File: `calibration-pipeline/workflow.json`**

```json
{
    "definition": {
        "$schema": "https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#",
        "actions": {
            "Initialize_job_id": {
                "type": "InitializeVariable",
                "inputs": {
                    "variables": [
                        {
                            "name": "job_id",
                            "type": "string",
                            "value": "@{first(split(triggerBody()?['Name'], '/'))}"
                        }
                    ]
                },
                "runAfter": {}
            },
            "List_job_files": {
                "type": "ApiConnection",
                "inputs": {
                    "host": {
                        "connection": {
                            "name": "@parameters('$connections')['azureblob']['connectionId']"
                        }
                    },
                    "method": "get",
                    "path": "/v2/datasets/@{encodeURIComponent('stcalibpipeline')}/foldersV2/@{encodeURIComponent(variables('job_id'))}",
                    "queries": {
                        "nextPageMarker": "",
                        "useFlatListing": true
                    }
                },
                "runAfter": {
                    "Initialize_job_id": ["Succeeded"]
                }
            },
            "Find_xlsx_and_pptx": {
                "type": "InitializeVariable",
                "inputs": {
                    "variables": [
                        {
                            "name": "xlsx_blob",
                            "type": "string",
                            "value": ""
                        }
                    ]
                },
                "runAfter": {
                    "List_job_files": ["Succeeded"]
                }
            },
            "Set_file_paths": {
                "type": "Scope",
                "actions": {
                    "For_each_blob": {
                        "type": "Foreach",
                        "foreach": "@body('List_job_files')?['value']",
                        "actions": {
                            "Check_if_xlsx": {
                                "type": "If",
                                "expression": {
                                    "and": [
                                        {
                                            "endsWith": [
                                                "@items('For_each_blob')?['Name']",
                                                ".xlsx"
                                            ]
                                        }
                                    ]
                                },
                                "actions": {
                                    "Set_xlsx_blob": {
                                        "type": "SetVariable",
                                        "inputs": {
                                            "name": "xlsx_blob",
                                            "value": "@items('For_each_blob')?['Name']"
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "runAfter": {
                    "Find_xlsx_and_pptx": ["Succeeded"]
                }
            },
            "Stage_1_Extract_Elements": {
                "type": "Http",
                "inputs": {
                    "method": "POST",
                    "uri": "https://func-calibration-stages.azurewebsites.net/api/stage1",
                    "headers": {
                        "x-functions-key": "@parameters('functionAppKey')"
                    },
                    "body": {
                        "job_id": "@variables('job_id')",
                        "xlsx_blob": "@variables('xlsx_blob')"
                    }
                },
                "runAfter": {
                    "Set_file_paths": ["Succeeded"]
                },
                "runtimeConfiguration": {
                    "staticResult": {
                        "name": "stage1_output"
                    }
                }
            },
            "Stage_2_Extract_Evidence": {
                "type": "Http",
                "inputs": {
                    "method": "POST",
                    "uri": "https://func-calibration-stages.azurewebsites.net/api/stage2",
                    "headers": {
                        "x-functions-key": "@parameters('functionAppKey')"
                    },
                    "body": {
                        "job_id": "@variables('job_id')",
                        "pptx_blobs": ["@{variables('job_id')}/evidence.pptx"]
                    }
                },
                "runAfter": {
                    "Set_file_paths": ["Succeeded"]
                },
                "runtimeConfiguration": {
                    "staticResult": {
                        "name": "stage2_output"
                    }
                }
            },
            "Stage_3_Match_Evidence": {
                "type": "Http",
                "inputs": {
                    "method": "POST",
                    "uri": "https://func-calibration-stages.azurewebsites.net/api/stage3",
                    "headers": {
                        "x-functions-key": "@parameters('functionAppKey')"
                    },
                    "body": {
                        "job_id": "@variables('job_id')",
                        "elements_blob": "@body('Stage_1_Extract_Elements')?['elements_blob']",
                        "evidence_blob": "@body('Stage_2_Extract_Evidence')?['evidence_blob']"
                    }
                },
                "runAfter": {
                    "Stage_1_Extract_Elements": ["Succeeded"],
                    "Stage_2_Extract_Evidence": ["Succeeded"]
                }
            },
            "Stage_4_Evaluate": {
                "type": "Http",
                "inputs": {
                    "method": "POST",
                    "uri": "https://func-calibration-stages.azurewebsites.net/api/stage4",
                    "headers": {
                        "x-functions-key": "@parameters('functionAppKey')"
                    },
                    "body": {
                        "job_id": "@variables('job_id')",
                        "matched_blob": "@body('Stage_3_Match_Evidence')?['matched_blob']"
                    }
                },
                "runAfter": {
                    "Stage_3_Match_Evidence": ["Succeeded"]
                }
            },
            "Stage_5_Generate_Report": {
                "type": "Http",
                "inputs": {
                    "method": "POST",
                    "uri": "https://func-calibration-stages.azurewebsites.net/api/stage5",
                    "headers": {
                        "x-functions-key": "@parameters('functionAppKey')"
                    },
                    "body": {
                        "job_id": "@variables('job_id')",
                        "evaluation_blob": "@body('Stage_4_Evaluate')?['evaluation_blob']",
                        "matched_blob": "@body('Stage_3_Match_Evidence')?['matched_blob']"
                    }
                },
                "runAfter": {
                    "Stage_4_Evaluate": ["Succeeded"]
                }
            },
            "Archive_Input_Files": {
                "type": "Scope",
                "actions": {
                    "Copy_to_archive": {
                        "type": "Foreach",
                        "foreach": "@body('List_job_files')?['value']",
                        "actions": {
                            "Copy_blob": {
                                "type": "ApiConnection",
                                "inputs": {
                                    "host": {
                                        "connection": {
                                            "name": "@parameters('$connections')['azureblob']['connectionId']"
                                        }
                                    },
                                    "method": "post",
                                    "path": "/v2/datasets/@{encodeURIComponent('stcalibpipeline')}/copyFile",
                                    "queries": {
                                        "source": "/calibration-inbox/@{items('Copy_to_archive')?['Name']}",
                                        "destination": "/calibration-archive/@{items('Copy_to_archive')?['Name']}",
                                        "overwrite": true
                                    }
                                }
                            }
                        }
                    }
                },
                "runAfter": {
                    "Stage_5_Generate_Report": ["Succeeded"]
                }
            },
            "Send_Completion_Notification": {
                "type": "Http",
                "inputs": {
                    "method": "POST",
                    "uri": "@parameters('teamsWebhookUrl')",
                    "headers": {
                        "Content-Type": "application/json"
                    },
                    "body": {
                        "text": "**Calibration Pipeline Complete** ✅\n\nJob: @{variables('job_id')}\n\nResults:\n- Pass: @{body('Stage_4_Evaluate')?['statistics']?['pass']}\n- Fail: @{body('Stage_4_Evaluate')?['statistics']?['fail']}\n- Needs More Evidence: @{body('Stage_4_Evaluate')?['statistics']?['needs_more_evidence']}\n\nReport available in: calibration-results/@{variables('job_id')}/evaluation_report.docx"
                    }
                },
                "runAfter": {
                    "Archive_Input_Files": ["Succeeded"]
                }
            },
            "Handle_Pipeline_Error": {
                "type": "Scope",
                "actions": {
                    "Send_Error_Notification": {
                        "type": "Http",
                        "inputs": {
                            "method": "POST",
                            "uri": "@parameters('teamsWebhookUrl')",
                            "headers": {
                                "Content-Type": "application/json"
                            },
                            "body": {
                                "text": "**Calibration Pipeline FAILED** ❌\n\nJob: @{variables('job_id')}\n\nCheck Logic App run history for details."
                            }
                        }
                    }
                },
                "runAfter": {
                    "Stage_1_Extract_Elements": ["Failed", "TimedOut"],
                    "Stage_2_Extract_Evidence": ["Failed", "TimedOut"],
                    "Stage_3_Match_Evidence": ["Failed", "TimedOut"],
                    "Stage_4_Evaluate": ["Failed", "TimedOut"],
                    "Stage_5_Generate_Report": ["Failed", "TimedOut"]
                }
            }
        },
        "triggers": {
            "When_a_blob_is_added": {
                "type": "ApiConnection",
                "inputs": {
                    "host": {
                        "connection": {
                            "name": "@parameters('$connections')['azureblob']['connectionId']"
                        }
                    },
                    "method": "get",
                    "path": "/datasets/default/triggers/batch/onupdatedfile",
                    "queries": {
                        "folderId": "/calibration-inbox",
                        "maxFileCount": 1
                    }
                },
                "recurrence": {
                    "frequency": "Minute",
                    "interval": 1
                },
                "splitOn": "@triggerBody()",
                "conditions": [
                    {
                        "expression": "@endsWith(triggerBody()?['Name'], '.pptx')"
                    }
                ]
            }
        },
        "contentVersion": "1.0.0.0",
        "outputs": {},
        "parameters": {
            "$connections": {
                "type": "Object"
            },
            "functionAppKey": {
                "type": "SecureString"
            },
            "teamsWebhookUrl": {
                "type": "String",
                "defaultValue": ""
            }
        }
    },
    "kind": "Stateful"
}
```

### Step 3.3: Understanding the Workflow

Let's break down what each section does:

#### Trigger: `When_a_blob_is_added`

```
Polls the "calibration-inbox" container every minute.
Fires when a new .pptx file is detected.
The condition filter ensures we only trigger on PPTX uploads
(not when the xlsx is uploaded separately).
```

**Key design decision:** Users upload files into a **job folder** structure:
```
calibration-inbox/
  job-001/
    calib_evidence.xlsx    ← Upload this first
    evidence1-6.pptx       ← Upload this second (triggers the pipeline)
```

The `.pptx` upload acts as the "start signal" — it implies the Excel file is already there.

#### Stages 1 and 2 Run in Parallel

Notice in the workflow that `Stage_1_Extract_Elements` and `Stage_2_Extract_Evidence` both depend only on `Set_file_paths`. This means the Logic App executes them **in parallel**, saving time.

```
Set_file_paths
   ├── Stage 1 (extract elements)  ──┐
   └── Stage 2 (extract evidence)  ──┤
                                      ▼
                              Stage 3 (match)
                                      │
                              Stage 4 (evaluate)
                                      │
                              Stage 5 (report)
```

#### Error Handling: `Handle_Pipeline_Error`

The `Handle_Pipeline_Error` scope runs if **any** stage fails or times out. It sends a Teams notification with the error details.

---

## Exercise 4: Configure the Logic App Connections

### Step 4.1: Create the Blob Storage API Connection

In the Azure Portal:

1. Navigate to your Logic App → **API connections**
2. Click **+ Add**
3. Search for **Azure Blob Storage**
4. Configure:
   - **Connection Name:** `blob-calibration`
   - **Authentication Type:** Managed Identity (recommended) or Access Key
   - **Storage Account:** `stcalibpipeline`
5. Click **Create**

### Step 4.2: Set Logic App Parameters

Navigate to your Logic App → **Configuration** → **Application settings** and add:

| Setting | Value |
|---------|-------|
| `functionAppKey` | The default host key from `func-calibration-stages` |
| `teamsWebhookUrl` | Your Teams incoming webhook URL (optional) |

To get the function app key:

```bash
az functionapp keys list \
  --name func-calibration-stages \
  --resource-group rg-calibration-pipeline \
  --query "functionKeys.default" -o tsv
```

### Step 4.3: Set Timeout for Long-Running Stages

Stage 2 (PPTX extraction) and Stage 4 (LLM evaluation) can take several minutes per file. Configure appropriate timeouts on those HTTP actions.

In the workflow JSON, add a `limit` property to the long-running actions:

```json
"Stage_2_Extract_Evidence": {
    "type": "Http",
    "inputs": { ... },
    "limit": {
        "timeout": "PT30M"
    }
}
```

This sets a 30-minute timeout (ISO 8601 duration format).

> **Recommendation:** For very large PPTX files (50+ slides), consider switching Stage 2 to use **Durable Functions** with the async HTTP pattern. The Logic App would poll for completion instead of waiting synchronously.

---

## Exercise 5: Test the Pipeline End-to-End

### Step 5.1: Prepare Test Files

Create a job folder and upload your test files:

```bash
# Create a unique job ID
JOB_ID="job-$(date +%Y%m%d%H%M%S)"

# Upload the Excel file first
az storage blob upload \
  --account-name stcalibpipeline \
  --container-name calibration-inbox \
  --file source-docs/calib_evidence.xlsx \
  --name "$JOB_ID/calib_evidence.xlsx" \
  --auth-mode login

# Upload the PPTX file (this triggers the pipeline)
az storage blob upload \
  --account-name stcalibpipeline \
  --container-name calibration-inbox \
  --file source-docs/evidence1-6.pptx \
  --name "$JOB_ID/evidence1-6.pptx" \
  --auth-mode login

echo "Job submitted: $JOB_ID"
```

### Step 5.2: Monitor the Logic App Run

1. Open the Azure Portal
2. Navigate to **Logic App** → `logic-calibration-pipeline`
3. Click **Overview** → **Run History**
4. You should see a new run in progress
5. Click into the run to see each action's status

Each step will show:
- **Green checkmark:** Succeeded
- **Blue spinner:** In progress  
- **Red X:** Failed (click to see error details)

### Step 5.3: Verify the Output

```bash
# List results for the job
az storage blob list \
  --account-name stcalibpipeline \
  --container-name calibration-results \
  --prefix "$JOB_ID/" \
  --output table

# Download the evaluation report
az storage blob download \
  --account-name stcalibpipeline \
  --container-name calibration-results \
  --name "$JOB_ID/evaluation_report.docx" \
  --file evaluation_report.docx \
  --auth-mode login
```

Expected files in `calibration-results/{job-id}/`:

| File | Stage | Description |
|------|-------|-------------|
| `elements.json` | 1 | Extracted PI elements from Excel |
| `evidence.json` | 2 | Extracted slide content (multimodal) |
| `matched_evidence.json` | 3 | Elements matched to evidence slides |
| `evaluation_results.json` | 4 | LLM evaluation (Pass/Fail/Needs More) |
| `evaluation_report.docx` | 5 | Formatted Word document report |

---

## Exercise 6: Add Monitoring and Observability

### Step 6.1: Enable Application Insights

```bash
# Create Application Insights
az monitor app-insights component create \
  --app ai-calibration-insights \
  --location eastus2 \
  --resource-group rg-calibration-pipeline \
  --application-type web

# Get the instrumentation key
APPINSIGHTS_KEY=$(az monitor app-insights component show \
  --app ai-calibration-insights \
  --resource-group rg-calibration-pipeline \
  --query instrumentationKey -o tsv)

# Add to Function App
az functionapp config appsettings set \
  --name func-calibration-stages \
  --resource-group rg-calibration-pipeline \
  --settings "APPINSIGHTS_INSTRUMENTATIONKEY=$APPINSIGHTS_KEY"
```

### Step 6.2: Add Custom Metrics

Add logging to your Functions to track pipeline-specific metrics:

```python
# At the top of each stage function, add:
import logging

# The Azure Functions runtime automatically sends logs to App Insights
# Use structured logging for better querying:
logging.info(
    "Pipeline stage completed",
    extra={
        "custom_dimensions": {
            "job_id": job_id,
            "stage": "stage1",
            "elements_count": len(elements),
            "duration_seconds": elapsed
        }
    }
)
```

### Step 6.3: Query Pipeline Metrics in Log Analytics

After a few runs, query your pipeline data in the Azure Portal → Application Insights → Logs:

```kusto
// Average duration per stage
customEvents
| where name == "Pipeline stage completed"
| extend stage = tostring(customDimensions.stage),
         duration = todouble(customDimensions.duration_seconds)
| summarize avg(duration), percentile(duration, 95) by stage
| order by stage asc

// Job success rate over time
requests
| where name startswith "stage"
| summarize 
    total = count(),
    failed = countif(resultCode != "200")
    by bin(timestamp, 1h)
| extend success_rate = round(100.0 * (total - failed) / total, 1)
```

---

## Exercise 7: Production Hardening

### Step 7.1: Use Durable Functions for Long-Running Stages

For production workloads, Stage 2 (PPTX extraction with LLM) can take 10-30 minutes for large files. Convert it to a **Durable Functions orchestration** with the async HTTP pattern:

```python
# stage2_orchestrator.py (Durable Functions pattern)
import azure.functions as func
import azure.durable_functions as df


def orchestrator_function(context: df.DurableOrchestrationContext):
    """Orchestrate the extraction of a multi-slide PPTX."""
    input_data = context.get_input()
    job_id = input_data["job_id"]
    pptx_blobs = input_data["pptx_blobs"]
    
    # Fan out: process each PPTX file in parallel
    parallel_tasks = []
    for pptx_blob in pptx_blobs:
        task = context.call_activity(
            "extract_single_pptx",
            {"job_id": job_id, "pptx_blob": pptx_blob}
        )
        parallel_tasks.append(task)
    
    # Fan in: wait for all extractions to complete
    results = yield context.task_all(parallel_tasks)
    
    # Merge results
    merged = yield context.call_activity(
        "merge_evidence",
        {"job_id": job_id, "partial_results": results}
    )
    
    return merged


main = df.Orchestrator.create(orchestrator_function)
```

The Logic App would then use the **async HTTP pattern**:
1. POST to start the orchestration → get a `statusQueryGetUri`
2. Poll the status URI until the orchestration completes

### Step 7.2: Add Retry Policies

Add retry policies to the Logic App workflow for transient failures (e.g., OpenAI rate limits):

```json
"Stage_4_Evaluate": {
    "type": "Http",
    "inputs": { ... },
    "retryPolicy": {
        "type": "exponential",
        "count": 3,
        "interval": "PT30S",
        "minimumInterval": "PT10S",
        "maximumInterval": "PT5M"
    }
}
```

### Step 7.3: Add Concurrency Control

Prevent too many simultaneous pipeline runs from overwhelming your OpenAI quota:

In the trigger configuration:

```json
"When_a_blob_is_added": {
    "type": "ApiConnection",
    ...
    "operationOptions": "SingleInstance",
    "runtimeConfiguration": {
        "concurrency": {
            "runs": 3
        }
    }
}
```

This limits the Logic App to 3 concurrent runs. Additional triggers will queue.

### Step 7.4: Implement Dead-Letter Handling

For jobs that fail after all retries, move them to a dead-letter container:

Add to the `Handle_Pipeline_Error` scope:

```json
"Move_to_dead_letter": {
    "type": "ApiConnection",
    "inputs": {
        "host": {
            "connection": {
                "name": "@parameters('$connections')['azureblob']['connectionId']"
            }
        },
        "method": "post",
        "path": "/v2/datasets/@{encodeURIComponent('stcalibpipeline')}/copyFile",
        "queries": {
            "source": "/calibration-inbox/@{variables('job_id')}",
            "destination": "/calibration-deadletter/@{variables('job_id')}",
            "overwrite": true
        }
    }
}
```

---

## Exercise 8: Infrastructure as Code (Bicep)

### Step 8.1: Create a Bicep Template for the Full Solution

**File: `iac/logic-app-pipeline.bicep`**

```bicep
targetScope = 'resourceGroup'

@description('Base name for all resources')
param baseName string = 'calibpipe'

@description('Location for all resources')
param location string = resourceGroup().location

@description('Azure OpenAI endpoint')
@secure()
param azureOpenAiEndpoint string

@description('Azure OpenAI API key')
@secure()
param azureOpenAiApiKey string

@description('Azure OpenAI deployment name')
param azureOpenAiDeployment string = 'gpt-41'

@description('Azure Document Intelligence endpoint')
@secure()
param azureDiEndpoint string

@description('Azure Document Intelligence key')
@secure()
param azureDiKey string

var uniqueSuffix = uniqueString(resourceGroup().id)
var storageAccountName = toLower('${baseName}st${take(uniqueSuffix, 8)}')
var functionAppName = '${baseName}-func-${uniqueSuffix}'
var logicAppName = '${baseName}-logic-${uniqueSuffix}'
var appInsightsName = '${baseName}-insights'
var appServicePlanName = '${baseName}-plan'
var logicAppPlanName = '${baseName}-logic-plan'

// Storage Account
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
  }
}

// Blob containers
resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01' = {
  parent: storageAccount
  name: 'default'
}

var containerNames = ['calibration-inbox', 'calibration-results', 'calibration-archive', 'calibration-cache']

resource containers 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = [
  for name in containerNames: {
    parent: blobService
    name: name
  }
]

// Application Insights
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
  }
}

// Function App (Consumption plan)
resource functionPlan 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: appServicePlanName
  location: location
  sku: {
    name: 'Y1'
    tier: 'Dynamic'
  }
  kind: 'functionapp'
  properties: {
    reserved: true  // Linux
  }
}

resource functionApp 'Microsoft.Web/sites@2023-01-01' = {
  name: functionAppName
  location: location
  kind: 'functionapp,linux'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: functionPlan.id
    siteConfig: {
      pythonVersion: '3.11'
      linuxFxVersion: 'Python|3.11'
      appSettings: [
        { name: 'AzureWebJobsStorage', value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};AccountKey=${storageAccount.listKeys().keys[0].value}' }
        { name: 'FUNCTIONS_WORKER_RUNTIME', value: 'python' }
        { name: 'FUNCTIONS_EXTENSION_VERSION', value: '~4' }
        { name: 'APPINSIGHTS_INSTRUMENTATIONKEY', value: appInsights.properties.InstrumentationKey }
        { name: 'AZURE_OPENAI_ENDPOINT', value: azureOpenAiEndpoint }
        { name: 'AZURE_OPENAI_API_KEY', value: azureOpenAiApiKey }
        { name: 'AZURE_OPENAI_DEPLOYMENT', value: azureOpenAiDeployment }
        { name: 'AZURE_DI_ENDPOINT', value: azureDiEndpoint }
        { name: 'AZURE_DI_KEY', value: azureDiKey }
        { name: 'AZURE_STORAGE_CONNECTION_STRING', value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};AccountKey=${storageAccount.listKeys().keys[0].value}' }
      ]
    }
  }
}

// Logic App (Standard)
resource logicAppPlan 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: logicAppPlanName
  location: location
  sku: {
    name: 'WS1'
    tier: 'WorkflowStandard'
  }
  kind: 'elastic'
}

resource logicApp 'Microsoft.Web/sites@2023-01-01' = {
  name: logicAppName
  location: location
  kind: 'functionapp,workflowapp'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: logicAppPlan.id
    siteConfig: {
      appSettings: [
        { name: 'AzureWebJobsStorage', value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};AccountKey=${storageAccount.listKeys().keys[0].value}' }
        { name: 'FUNCTIONS_WORKER_RUNTIME', value: 'node' }
        { name: 'FUNCTIONS_EXTENSION_VERSION', value: '~4' }
        { name: 'APPINSIGHTS_INSTRUMENTATIONKEY', value: appInsights.properties.InstrumentationKey }
        { name: 'APP_KIND', value: 'workflowApp' }
        { name: 'AzureFunctionsJobHost__extensionBundle__id', value: 'Microsoft.Azure.Functions.ExtensionBundle.Workflows' }
        { name: 'AzureFunctionsJobHost__extensionBundle__version', value: '[1.*, 2.0.0)' }
      ]
    }
  }
}

// RBAC: Function App → Storage Blob Data Contributor
resource storageBlobRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAccount.id, functionApp.id, 'Storage Blob Data Contributor')
  scope: storageAccount
  properties: {
    principalId: functionApp.identity.principalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
    principalType: 'ServicePrincipal'
  }
}

output storageAccountName string = storageAccount.name
output functionAppName string = functionApp.name
output logicAppName string = logicApp.name
output functionAppUrl string = 'https://${functionApp.properties.defaultHostName}'
```

### Step 8.2: Deploy

```bash
az deployment group create \
  --resource-group rg-calibration-pipeline \
  --template-file iac/logic-app-pipeline.bicep \
  --parameters \
    azureOpenAiEndpoint='https://<your-openai>.openai.azure.com/' \
    azureOpenAiApiKey='<your-key>' \
    azureDiEndpoint='https://<your-di>.cognitiveservices.azure.com/' \
    azureDiKey='<your-di-key>'
```

---

## Summary

In this lab you:

1. **Created Azure resources** — Storage Account with inbox/results/archive containers, a Function App for pipeline stages, and a Logic App for orchestration.

2. **Built 5 Azure Functions** — Each wrapping an existing pipeline stage:
   - Stage 1: Excel element extraction (`extractors/xlsx_extract.py`)
   - Stage 2: PPTX multimodal evidence extraction (`extractors/helpers/multimodal_extract.py`)
   - Stage 3: Evidence-to-element matching (`matching/match_evidence.py`)
   - Stage 4: LLM-based evaluation (`agents/evidence_evaluator.py`)
   - Stage 5: Word report generation (`reports/word_report.py`)

3. **Created a Logic App workflow** — Triggered by blob uploads, orchestrating all five Functions with parallel execution (Stages 1 & 2), error handling, archiving, and Teams notifications.

4. **Added monitoring** — Application Insights with custom metrics and KQL queries for pipeline analytics.

5. **Hardened for production** — Retry policies, concurrency limits, Durable Functions for long-running stages, and dead-letter handling.

6. **Wrote Infrastructure as Code** — Bicep template for repeatable deployment of the complete solution.

### Architecture Comparison

```
BEFORE (Python CLI):                    AFTER (Logic App + Functions):
                                        
┌──────────────────┐                    ┌─────────────────────────┐
│  User runs       │                    │  User uploads files to  │
│  python           │                    │  blob storage           │
│  run_pipeline.py │                    └───────────┬─────────────┘
└────────┬─────────┘                                │
         │                                          ▼
         ▼                              ┌─────────────────────────┐
┌──────────────────┐                    │  Logic App triggers     │
│  Sequential      │                    │  automatically          │
│  stages on       │                    └───────────┬─────────────┘
│  local machine   │                                │
└────────┬─────────┘                    ┌───────────┴─────────────┐
         │                              │  Azure Functions        │
         ▼                              │  (parallel + serverless)│
┌──────────────────┐                    └───────────┬─────────────┘
│  Output files    │                                │
│  on local disk   │                                ▼
└──────────────────┘                    ┌─────────────────────────┐
                                        │  Results in blob +      │
                                        │  Teams notification     │
                                        └─────────────────────────┘
```

### Next Steps

- **Add a Power App or Streamlit front-end** that reads results from blob storage for a richer UI experience.
- **Implement RBAC** so only authorized users can upload to the inbox container.
- **Add Azure API Management** in front of the Functions for rate limiting and API key management.
- **Set up CI/CD** with GitHub Actions to deploy Functions and Logic App workflow changes automatically.
