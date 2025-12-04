# AI Calibration Evidence Extraction

A Python toolkit for extracting and analyzing content from GM calibration evidence documents (PPTX, XLSX) using Azure AI services.

## Features

- **PPTX Extraction**: Extract text, tables, and images from PowerPoint presentations
- **Excel Extraction**: Extract structured data from Excel workbooks
- **Document Intelligence OCR**: Extract text from embedded images using Azure Document Intelligence
- **Multimodal Analysis**: Combine native text + OCR + LLM vision for optimal text extraction
- **Multi-Model Support**: GPT-4.1 and GPT-5.1 models supported (separate endpoints)
- **Azure Infrastructure**: Bicep templates for deploying required Azure resources

## Architecture

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

## Project Structure

```
ai-calibration/
├── extractors/                    # Main extraction modules
│   ├── ppt_extract.py            # PPTX extraction with DI OCR
│   ├── xlsx_extract.py           # Excel extraction
│   └── helpers/                  # Helper modules
│       ├── config.py             # Configuration classes
│       ├── pptx_helpers.py       # PPTX iteration utilities
│       ├── di_helpers.py         # Document Intelligence API
│       ├── llm_helpers.py        # GPT-4.1 vision analysis
│       ├── slide_renderer.py     # Slide to image rendering
│       ├── multimodal_extract.py # Combined extraction pipeline
│       └── blob_helpers.py       # Azure Blob Storage utilities
├── iac/                          # Azure Infrastructure as Code
│   ├── main.bicep               # Main deployment template
│   ├── modules/                 # Bicep modules
│   └── parameters/              # Environment parameters
├── source-docs/                  # Sample documents (gitignored)
├── test_pptx_extract.py         # Test DI-based extraction
├── test_multimodal_extract.py   # Test multimodal pipeline
├── requirements.txt             # Python dependencies
├── .env                         # Environment variables (gitignored)
└── README.md                    # This file
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

### Basic PPTX Extraction (Document Intelligence)

Extract text and OCR from embedded images:

```python
from extractors.ppt_extract import pptx_to_unified_json

# Extract with compact output
result = pptx_to_unified_json(
    "path/to/presentation.pptx",
    output_path="output.json",
    compact=True  # Simplified JSON without polygon coordinates
)

print(f"Extracted {len(result['slides'])} slides")
```

Output format:
```json
{
  "slides": [
    {
      "index": 1,
      "title": "Slide Title",
      "text": ["text content from shapes"],
      "images": [
        {
          "name": "image.png",
          "ocr_text": "Text extracted from image via OCR"
        }
      ]
    }
  ]
}
```

### Multimodal Extraction (Recommended)

For best results, use the multimodal pipeline that combines all three sources:

```python
from extractors.helpers import quick_extract, quick_extract_gpt5

# Extracts using:
# 1. Native PPTX text (cleanest for text boxes)
# 2. Document Intelligence OCR (for embedded images)
# 3. LLM Vision (validates and structures everything)

# Using GPT-4.1 (default)
result = quick_extract(
    "path/to/presentation.pptx",
    output_path="output.json",
    verbose=True
)

# Using GPT-5.1
result = quick_extract(
    "path/to/presentation.pptx",
    output_path="output.json",
    model="gpt-5.1"  # Use GPT-5.1 instead
)

# Or use the convenience function
result = quick_extract_gpt5("path/to/presentation.pptx")
```

### Excel Extraction

```python
from extractors.xlsx_extract import extract_xlsx

result = extract_xlsx("path/to/workbook.xlsx")
for sheet in result["sheets"]:
    print(f"Sheet: {sheet['name']}, Rows: {len(sheet['data'])}")
```

### Direct Helper Usage

```python
from extractors.helpers import (
    DIConfig,
    LLMConfig,
    analyze_image_bytes,
    normalize_di_result,
    analyze_slide_multimodal,
)

# Document Intelligence OCR
di = DIConfig(endpoint="...", key="...")
result = analyze_image_bytes(di, image_bytes, "png")
text = normalize_di_result(result, compact=True)["text"]

# LLM Vision Analysis
llm = LLMConfig(endpoint="...", api_key="...", deployment="gpt-4.1")
text = analyze_slide_multimodal(llm, slide_image_bytes, extracted_text)
```

## Running Tests

```bash
# Test DI-based PPTX extraction
python test_pptx_extract.py

# Test multimodal extraction with GPT-4.1 (default)
python test_multimodal_extract.py

# Test multimodal extraction with GPT-5.1
python test_multimodal_extract.py --gpt5
```

## Requirements

### Python Dependencies
- `python-pptx` - PPTX parsing
- `openpyxl` - Excel parsing  
- `azure-ai-documentintelligence` - OCR
- `openai` - GPT-4.1 API
- `pymupdf` - PDF/image handling
- `comtypes` - PowerPoint COM (Windows only)

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

## License

Internal use only - GM Calibration Project

## Troubleshooting

### "LibreOffice not found"
Install LibreOffice or use Windows with PowerPoint installed for slide rendering.

### "comtypes" errors on Windows
```bash
pip install comtypes
```

### DI OCR fails on certain images
Check the `*_unsupported_images.json` output file for images that couldn't be processed.
