# PowerPoint Evidence Extraction Solution

## Overview

This solution automatically extracts all text content from PowerPoint presentations, including text that is embedded within screenshots, photos of whiteboards, scanned forms, and other images. It produces clean, structured output that can be used for search, analysis, compliance review, or further processing.

---

## How It Works

The solution uses a three-stage pipeline to ensure complete and accurate text extraction:

```
    ┌─────────────────────────────────────────────────────────────────┐
    │                    PowerPoint File (.pptx)                      │
    └─────────────────────────────────────────────────────────────────┘
                                   │
           ┌───────────────────────┼───────────────────────┐
           ▼                       ▼                       ▼
    ┌─────────────┐        ┌─────────────┐        ┌─────────────┐
    │   Stage 1   │        │   Stage 2   │        │   Stage 3   │
    │             │        │             │        │             │
    │ Native Text │        │  Image OCR  │        │ Slide Image │
    │ Extraction  │        │ (Azure AI)  │        │ Rendering   │
    └──────┬──────┘        └──────┬──────┘        └──────┬──────┘
           │                      │                      │
           │    Text from         │    Text from         │    Visual
           │    text boxes        │    screenshots       │    snapshot
           │                      │                      │
           └──────────────────────┴──────────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │        Stage 4          │
                    │                         │
                    │   AI Vision Analysis    │
                    │   (GPT-4.1 or GPT-5.1)  │
                    │                         │
                    │   Validates, corrects,  │
                    │   and structures the    │
                    │   final output          │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │     Clean JSON Output   │
                    │                         │
                    │  • Slide-by-slide text  │
                    │  • Logical reading order│
                    │  • Ready for analysis   │
                    └─────────────────────────┘
```

---

## Stage 1: Native Text Extraction

**What happens:** The system opens the PowerPoint file and reads all text that was typed directly into slides—titles, bullet points, text boxes, table cells, and speaker notes.

**Why it matters:** This text is already perfectly accurate since it comes directly from PowerPoint's internal structure. It provides a reliable foundation for the extraction.

**Technical reference:** `extractors/helpers/pptx_helpers.py` — functions like `iter_text_shapes()` and `iter_table_cells()` walk through each slide's content.

---

## Stage 2: Image OCR (Optical Character Recognition)

**What happens:** The system identifies all images embedded in the presentation (screenshots, photos, scanned documents) and sends them to Azure Document Intelligence for text recognition.

**Why it matters:** Many presentations contain screenshots of forms, systems, or spreadsheets. Without OCR, this text would be completely invisible to the extraction process.

**Technical reference:** `extractors/helpers/di_helpers.py` — the `analyze_image_bytes()` function sends images to Azure and returns the recognized text.

**Supported image formats:** PNG, JPEG, BMP, TIFF, PDF

---

## Stage 3: Slide Rendering

**What happens:** Each slide is rendered as a high-resolution image (PNG), exactly as it would appear when viewing the presentation.

**Why it matters:** This creates a "ground truth" visual that the AI can reference to validate and correct the extracted text.

**Technical reference:** `extractors/helpers/slide_renderer.py` — uses Microsoft PowerPoint (on Windows) or LibreOffice to render slides at 150 DPI.

---

## Stage 4: AI Vision Analysis

**What happens:** The AI model (GPT-4.1 or GPT-5.1) receives:
1. The rendered slide image
2. All text extracted from Stages 1 and 2

The AI then "looks at" the slide and produces a final, accurate text extraction by:
- Validating the extracted text against what it sees
- Correcting OCR errors (especially in handwriting)
- Organizing content in logical reading order
- Filling in any gaps missed by earlier stages

**Why it matters:** This is the key differentiator. The AI can read handwritten notes, interpret complex layouts, and fix mistakes that pure OCR makes with unusual fonts or low-quality images.

**Technical reference:** `extractors/helpers/llm_helpers.py` — the `analyze_slide_multimodal()` function sends the image and extracted text to the AI model.

---

## Output Format

The solution produces a JSON file with the following structure:

```json
{
  "source_file": "presentation.pptx",
  "total_slides": 69,
  "slides": [
    {
      "index": 1,
      "text": "Title Slide\n\n2025 Annual Report\nCompany Name\n\nConfidential\n\n1"
    },
    {
      "index": 2,
      "text": "Section Header\n\nBullet point one\nBullet point two\n\n[Table content extracted here]\n\n2"
    }
  ]
}
```

Each slide's text is:
- **Complete** — includes all visible text from any source
- **Ordered** — arranged in logical top-to-bottom, left-to-right reading order
- **Clean** — formatted for readability without unnecessary markup

---

## Running the Extraction

### Basic Usage

```python
from extractors.helpers import quick_extract

# Extract with GPT-4.1 (default)
result = quick_extract("presentation.pptx", output_path="output.json")

# Extract with GPT-5.1 (higher accuracy)
result = quick_extract("presentation.pptx", output_path="output.json", model="gpt-5.1")
```

### Command Line

```bash
# Using GPT-4.1
python test_multimodal_extract.py

# Using GPT-5.1
python test_multimodal_extract.py --gpt5
```

---

## Model Options

The solution supports two AI vision models:

| Model | Speed | Accuracy | Best For |
|-------|-------|----------|----------|
| **GPT-4.1** | ~3 sec/slide | Very Good | Standard documents, typed content |
| **GPT-5.1** | ~5 sec/slide | Excellent | Complex layouts, handwriting, forms |

Both models produce high-quality results. GPT-5.1 may perform better on challenging content like handwritten notes or complex table structures.

---

## Azure Services Used

| Service | Purpose | Cost Model |
|---------|---------|------------|
| **Azure Document Intelligence** | OCR for embedded images | Per page processed |
| **Azure OpenAI / AI Foundry** | Vision analysis (GPT-4.1/5.1) | Per token processed |

Estimated cost for a 70-slide presentation: **$1-2 USD**

---

## What Makes This Approach Unique

### Traditional OCR Limitations

Standard OCR tools struggle with:
- ❌ Handwritten content
- ❌ Stylized or decorative fonts
- ❌ Low-resolution screenshots
- ❌ Complex multi-column layouts
- ❌ Text overlaid on images

### Our Multimodal Advantage

By combining native extraction, OCR, and AI vision:
- ✅ Reads handwriting reliably
- ✅ Understands document structure and context
- ✅ Self-corrects OCR errors
- ✅ Handles any layout or format

---

## Security & Data Handling

- All processing uses Azure services with enterprise security
- Documents are processed in memory; temporary files are cleaned up
- No data is retained by AI services after processing
- Supports deployment in customer's own Azure subscription

---