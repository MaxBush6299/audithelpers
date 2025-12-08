# AI Calibration Evidence Evaluation Pipeline

A complete Python pipeline for extracting, matching, and evaluating PI calibration evidence from documents (PPTX, XLSX) using Azure AI services.

## Overview

This toolkit automates the PI calibration evidence evaluation process:

1. **Extract** PI elements and calibrator instructions from Excel
2. **Extract** evidence content from PowerPoint presentations using multimodal AI
3. **Match** evidence slides to their corresponding PI elements
4. **Evaluate** whether evidence meets calibration criteria using an LLM agent

## Features

- **Multi-Source Extraction**: Combines native PPTX text, Document Intelligence OCR, and LLM vision for comprehensive content extraction
- **Multi-Model Support**: GPT-4.1 and GPT-5.1 with automatic fallback
- **Multi-File Processing**: Process multiple evidence PPTX files with continuous slide indexing
- **Intelligent Matching**: Pattern-based matching of evidence slides to PI elements
- **LLM Evaluation**: AI-powered assessment of evidence against calibration criteria
- **Incremental Progress**: Real-time progress tracking for monitoring

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PI Calibration Evidence Evaluation Pipeline               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌───────────┐  │
│  │   Stage 1    │    │   Stage 2    │    │   Stage 3    │    │  Stage 4  │  │
│  │   Excel      │ -> │   PPTX       │ -> │   Matching   │ -> │  LLM      │  │
│  │   Extract    │    │   Extract    │    │   Engine     │    │  Evaluate │  │
│  └──────────────┘    └──────────────┘    └──────────────┘    └───────────┘  │
│        │                   │                   │                   │         │
│        ▼                   ▼                   ▼                   ▼         │
│   elements.json      evidence.json     matched_evidence.json  results.json  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Multimodal Extraction (Stage 2)

The PPTX extraction uses three complementary sources for maximum accuracy:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Multimodal Extraction Pipeline                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                   │
│  │  Native PPTX │    │  DI OCR on   │    │  Slide Image │                   │
│  │  Text Extract│ +  │  Embedded    │ +  │  (rendered)  │                   │
│  │  (python-pptx)    │  Images      │    │              │                   │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘                   │
│         │                   │                   │                            │
│         └───────────────────┴───────────────────┘                            │
│                             │                                                │
│                             ▼                                                │
│                    ┌────────────────┐                                        │
│                    │  GPT-4.1 or    │                                        │
│                    │  GPT-5.1       │                                        │
│                    │  Vision        │                                        │
│                    └────────┬───────┘                                        │
│                             │                                                │
│                             ▼                                                │
│                    ┌────────────────┐                                        │
│                    │  Clean JSON    │                                        │
│                    │  Output        │                                        │
│                    └────────────────┘                                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Source 1: Native PPTX Text** - Cleanest for text boxes, tables, and native content  
**Source 2: Document Intelligence OCR** - Captures text from embedded screenshots/images  
**Source 3: LLM Vision** - Validates and reconciles all sources, catches edge cases

**Model Fallback**: When using GPT-5.1, if a slide returns empty, the system automatically retries with GPT-4.1.

## Project Structure

```
ai-calibration/
├── run_pipeline.py               # Main pipeline orchestrator (entry point)
├── extractors/                   # Extraction modules
│   ├── ppt_extract.py           # PPTX extraction with DI OCR
│   ├── xlsx_extract.py          # Excel extraction (PI elements)
│   └── helpers/                 # Helper modules
│       ├── config.py            # Configuration classes
│       ├── pptx_helpers.py      # PPTX iteration utilities
│       ├── di_helpers.py        # Document Intelligence API
│       ├── llm_helpers.py       # GPT vision analysis
│       ├── slide_renderer.py    # Slide to image rendering
│       ├── multimodal_extract.py # Combined extraction pipeline
│       └── blob_helpers.py      # Azure Blob Storage utilities
├── matching/                     # Evidence matching logic
│   └── match_evidence.py        # Match slides to PI elements
├── evaluation/                   # LLM evaluation
│   └── evaluate.py              # Evaluate evidence against criteria
├── agents/                       # LLM agents
│   └── evidence_evaluator.py    # Evidence evaluation agent
├── utils/                        # Shared utilities
│   ├── element_extract.py       # PI element pattern extraction
│   └── slide_to_markdown.py     # Convert slides to Markdown
├── tests/                        # Test files
│   ├── test_pptx_extract.py     # Test DI-based extraction
│   └── test_multimodal_extract.py # Test multimodal pipeline
├── iac/                          # Azure Infrastructure as Code
│   ├── main.bicep               # Main deployment template
│   ├── modules/                 # Bicep modules
│   └── parameters/              # Environment parameters
├── docs/                         # Documentation
├── source-docs/                  # Sample documents (gitignored)
├── requirements.txt              # Python dependencies
├── .env                          # Environment variables (gitignored)
└── README.md                     # This file
```

## Installation

### 1. Clone and Setup Python Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Mac/Linux)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Deploy Azure Resources

```bash
cd iac

# Deploy to Azure (creates Storage, Document Intelligence, AI Services)
az deployment group create \
  --resource-group <your-rg> \
  --template-file main.bicep \
  --parameters parameters/dev.bicepparam
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```env
# Azure Document Intelligence
AZURE_DI_ENDPOINT=https://<your-di>.cognitiveservices.azure.com
AZURE_DI_KEY=<your-di-key>

# Azure AI Foundry - GPT-4.1
AZURE_AI_ENDPOINT=https://<your-ai-resource>.services.ai.azure.com
AZURE_AI_API_KEY=<your-ai-key>
GPT_4_1_DEPLOYMENT=<your-gpt4-deployment-name>

# Azure AI Foundry - GPT-5.1 (optional, separate endpoint)
AZURE_AI_GPT5_ENDPOINT=https://<your-gpt5-resource>.services.ai.azure.com
AZURE_AI_GPT5_API_KEY=<your-gpt5-key>
GPT_5_1_DEPLOYMENT=<your-gpt5-deployment-name>

# Azure Blob Storage (optional)
AZURE_STORAGE_CONNECTION_STRING=<your-connection-string>
```

## Usage

### Full Pipeline (Recommended)

Run the complete pipeline from Excel elements through evaluation:

```bash
python run_pipeline.py \
    --elements-xlsx source-docs/calib_evidence.xlsx \
    --evidence-pptx source-docs/evidence1-6.pptx source-docs/evidence7-15.pptx \
    --output-dir output/ \
    --model gpt-5.1
```

**Pipeline Options:**

| Option | Description |
|--------|-------------|
| `--elements-xlsx` | Excel file with PI elements and calibrator instructions |
| `--evidence-pptx` | One or more PPTX files with evidence slides |
| `--output-dir` | Output directory for JSON results (default: `./output`) |
| `--model` | Model to use: `gpt-4.1` or `gpt-5.1` (default: `gpt-4.1`) |
| `--skip-extraction` | Skip PPTX extraction, use existing `evidence.json` |
| `--skip-evaluation` | Skip LLM evaluation stage |
| `--no-di` | Disable Document Intelligence OCR |

**Output Files:**

| File | Description |
|------|-------------|
| `elements.json` | Extracted PI elements from Excel |
| `evidence.json` | Extracted slide content from all PPTX files |
| `matched_evidence.json` | Evidence matched to PI elements |
| `evaluation_results.json` | LLM evaluation verdicts |
| `evaluation_progress.json` | Real-time progress (for monitoring) |

### Individual Stages

#### Stage 1: Excel Extraction

```python
from extractors.xlsx_extract import extract_pi_rows_xlsx

elements = extract_pi_rows_xlsx("path/to/calibration.xlsx", verbose=True)
print(f"Extracted {len(elements)} PI elements")
```

#### Stage 2: PPTX Extraction

```python
from extractors.helpers.multimodal_extract import quick_extract, quick_extract_multi

# Single file
result = quick_extract(
    "path/to/evidence.pptx",
    output_path="evidence.json",
    model="gpt-5.1",  # or "gpt-4.1"
    verbose=True
)

# Multiple files with continuous indexing
result = quick_extract_multi(
    ["evidence1.pptx", "evidence2.pptx"],
    output_path="evidence.json",
    model="gpt-5.1"
)
```

#### Stage 3: Evidence Matching

```python
from matching.match_evidence import build_elements_lookup, match_slides_to_elements

# Build lookup from elements
elements_lookup = build_elements_lookup(elements_data)

# Match evidence to elements
result = match_slides_to_elements(evidence_data, elements_lookup)
print(f"Matched {result.statistics['matched_slides']} slides")
```

#### Stage 4: LLM Evaluation

```python
from evaluation.evaluate import evaluate_matched_evidence

results = evaluate_matched_evidence(
    matched_evidence_path="matched_evidence.json",
    output_path="evaluation_results.json",
    progress_path="evaluation_progress.json"
)
```

### Utilities

#### Convert Slides to Markdown

```bash
# Single slide
python -m utils.slide_to_markdown evidence.json 4

# Range of slides
python -m utils.slide_to_markdown evidence.json 1-10

# All slides
python -m utils.slide_to_markdown evidence.json --all -o output/
```

## Running Tests

```bash
# Test from tests directory
python tests/test_pptx_extract.py
python tests/test_multimodal_extract.py --gpt5
```

## Requirements

### Python Dependencies

- `python-pptx` - PPTX parsing
- `openpyxl` - Excel parsing  
- `azure-ai-documentintelligence` - OCR
- `openai` - GPT API
- `pymupdf` - PDF/image handling
- `comtypes` - PowerPoint COM (Windows only)
- `python-dotenv` - Environment variables

### Azure Services

- **Azure Document Intelligence** - OCR for embedded images
- **Azure AI Foundry** - GPT-4.1 and/or GPT-5.1 vision models
- **Azure Blob Storage** (optional) - Temporary file storage

### System Requirements (for Multimodal)

- **Windows**: Microsoft PowerPoint (preferred) or LibreOffice
- **Mac/Linux**: LibreOffice (`brew install --cask libreoffice`)

## Supported Formats

### Images (for OCR)
- PNG, JPEG, BMP, TIFF, HEIF, PDF
- ❌ WMF, EMF (tracked but not processed)

### Documents
- PPTX (PowerPoint)
- XLSX (Excel)

## Troubleshooting

### "LibreOffice not found"
Install LibreOffice or use Windows with PowerPoint installed for slide rendering.

### "comtypes" errors on Windows
```bash
pip install comtypes
```

### Empty slides in output
- Check if Document Intelligence credentials are configured
- GPT-5.1 may return empty for some slides - the pipeline automatically falls back to GPT-4.1
- Run with `--model gpt-4.1` if GPT-5.1 consistently fails

### DI OCR fails on certain images
Check the `*_unsupported_images.json` output file for images that couldn't be processed.

## License

Internal use only
