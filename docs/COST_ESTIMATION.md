# Cost Estimation Guide

This document provides detailed cost estimates for running the PI Calibration Evidence Evaluation Pipeline, broken down by **Phase 1: Extraction** (cached) and **Phase 2: Evaluation** (not cached).

## Table of Contents

1. [Overview](#overview)
2. [Phase 1: Extraction Costs (Cached)](#phase-1-extraction-costs-cached)
3. [Phase 2: Evaluation Costs (Not Cached)](#phase-2-evaluation-costs-not-cached)
4. [Model Comparison](#model-comparison)
5. [Total Cost Examples](#total-cost-examples)
6. [Caching Benefits](#caching-benefits)
7. [Cost Optimization Tips](#cost-optimization-tips)
8. [References](#references)

---

## Overview

The pipeline processes calibration evidence in two distinct phases with different cost profiles:

| Phase | Stage | Service Used | Cached? | Cost Profile |
|-------|-------|--------------|---------|--------------|
| **Phase 1: Extraction** | Stage 2 | Document Intelligence + GPT-4.1/5.1 Vision | ✅ Yes | ~$0.05-$0.07/slide |
| **Phase 2: Evaluation** | Stage 4 | GPT-4.1/5.1 (Text Only) | ❌ No | ~$0.016/element |

**Key Insight**: On re-runs with the same source documents, you only pay for Phase 2 (evaluation), resulting in **83-87% cost savings**.

---

## Phase 1: Extraction Costs (Cached)

Phase 1 extracts text and data from PowerPoint slides using Document Intelligence for OCR and GPT Vision for interpretation.

### Azure Document Intelligence

| Model | Price per Page | Use Case |
|-------|----------------|----------|
| `prebuilt-layout` | $0.01 | OCR for embedded images in slides |

### Azure OpenAI GPT-4.1 / GPT-5.1 Vision

Used to interpret slide images and extract structured calibration data.

| Model | Input (per 1K tokens) | Output (per 1K tokens) |
|-------|----------------------|------------------------|
| GPT-4.1 | $0.002 | $0.008 |
| GPT-5.1 | *Check [Azure Pricing](https://azure.microsoft.com/pricing/details/cognitive-services/openai-service/)* | *Check [Azure Pricing](https://azure.microsoft.com/pricing/details/cognitive-services/openai-service/)* |

#### Token Estimation for Slide Extraction

Based on actual pipeline runs:

| Component | Tokens | Notes |
|-----------|--------|-------|
| Image tokens (per slide) | ~1,100 | 768x768 low-detail mode |
| System prompt | ~500 | Extraction instructions |
| Output (structured JSON) | ~800-1,500 | Varies by content density |

**Estimated cost per slide (GPT-4.1 Vision):**
- Input: ~1,600 tokens × $0.002/1K = ~$0.0032
- Output: ~1,200 tokens × $0.008/1K = ~$0.0096
- **Total GPT cost per slide: ~$0.013**
- **Total with DI OCR: ~$0.023/slide** (if slide has embedded images)

For slides with multiple embedded images requiring OCR:
- **Estimated: $0.05-$0.07 per slide**

---

## Phase 2: Evaluation Costs (Not Cached)

Phase 2 evaluates extracted elements against PI requirements using GPT text models (no vision needed).

### Azure OpenAI GPT-4.1 / GPT-5.1 (Text Only)

| Model | Input (per 1K tokens) | Output (per 1K tokens) |
|-------|----------------------|------------------------|
| GPT-4.1 | $0.002 | $0.008 |
| GPT-5.1 | *Check [Azure Pricing](https://azure.microsoft.com/pricing/details/cognitive-services/openai-service/)* | *Check [Azure Pricing](https://azure.microsoft.com/pricing/details/cognitive-services/openai-service/)* |

#### Token Estimation for Element Evaluation

| Component | Tokens | Notes |
|-----------|--------|-------|
| System prompt | ~800 | Evaluation rubric and criteria |
| Element context | ~500-1,000 | Extracted text, tables, metadata |
| Output (evaluation JSON) | ~300-500 | Score, reasoning, recommendations |

**Estimated cost per element (GPT-4.1):**
- Input: ~1,200 tokens × $0.002/1K = ~$0.0024
- Output: ~400 tokens × $0.008/1K = ~$0.0032
- **Total per element: ~$0.006**

With overhead for context and retries:
- **Practical estimate: ~$0.016 per element**

---

## Model Comparison

### GPT-4.1 vs GPT-5.1

| Factor | GPT-4.1 | GPT-5.1 |
|--------|---------|---------|
| Availability | Generally Available | Check region availability |
| Input Cost | $0.002/1K tokens | Check [Azure Pricing](https://azure.microsoft.com/pricing/details/cognitive-services/openai-service/) |
| Output Cost | $0.008/1K tokens | Check [Azure Pricing](https://azure.microsoft.com/pricing/details/cognitive-services/openai-service/) |
| Vision Support | ✅ Yes | ✅ Yes |
| Recommended For | Production workloads | Latest capabilities |

> **Note**: GPT-5.1 pricing may vary. Always check the [Azure OpenAI Pricing Page](https://azure.microsoft.com/pricing/details/cognitive-services/openai-service/) for current rates.

---

## Total Cost Examples

### Example: 69-Slide Presentation with 54 Evidence Elements

#### First Run (No Cache)

| Phase | Items | Cost per Item | Total |
|-------|-------|---------------|-------|
| **Phase 1: Extraction** | 69 slides | ~$0.063/slide | ~$4.35 |
| **Phase 2: Evaluation** | 54 elements | ~$0.016/element | ~$0.86 |
| **Total First Run** | | | **~$5.21** |

#### Subsequent Runs (With Cache)

| Phase | Items | Cost per Item | Total |
|-------|-------|---------------|-------|
| **Phase 1: Extraction** | 69 slides | $0.00 (cached) | $0.00 |
| **Phase 2: Evaluation** | 54 elements | ~$0.016/element | ~$0.86 |
| **Total Cached Run** | | | **~$0.86** |

**Savings: ~$4.35 (83% reduction)**

### Scaling Examples

| Document Size | Elements | First Run | Cached Re-run | Savings |
|---------------|----------|-----------|---------------|---------|
| Small (20 slides, 15 elements) | 15 | ~$1.50 | ~$0.24 | 84% |
| Medium (50 slides, 40 elements) | 40 | ~$3.79 | ~$0.64 | 83% |
| Large (100 slides, 80 elements) | 80 | ~$7.58 | ~$1.28 | 83% |
| Extra Large (200 slides, 150 elements) | 150 | ~$14.99 | ~$2.40 | 84% |

---

## Caching Benefits

### What Gets Cached (Phase 1)

The extraction cache stores:
- ✅ Slide image renderings
- ✅ Document Intelligence OCR results
- ✅ GPT Vision extraction outputs
- ✅ Structured JSON for each slide

### What Doesn't Get Cached (Phase 2)

Evaluation results are regenerated each run because:
- Evaluation criteria may change
- Element scores need to reflect current requirements
- Fresh analysis ensures accuracy

### Cache Storage Options

| Option | Storage | Best For |
|--------|---------|----------|
| **Azure Blob Storage** | Cloud-based, persistent | Production, team sharing |
| **Local File Cache** | `.extraction_cache/` folder | Development, testing |

### Re-run Cost Breakdown

When you re-run the pipeline with cached extraction:

```
First Run:
├── Phase 1: Extraction ──────── $4.35 (PAID)
└── Phase 2: Evaluation ──────── $0.86 (PAID)
                                 ═══════
                          Total: $5.21

Cached Re-run:
├── Phase 1: Extraction ──────── $0.00 (CACHED ✓)
└── Phase 2: Evaluation ──────── $0.86 (PAID)
                                 ═══════
                          Total: $0.86  (83% savings!)
```

---

## Cost Optimization Tips

### 1. Leverage Caching
- Use Azure Blob Storage for persistent caching across sessions
- Only re-extract when source documents actually change
- Use `--skip-cache` flag sparingly (forces full re-extraction)

### 2. Batch Processing
- Process multiple documents in a single session
- Extraction cache is reusable across pipeline runs

### 3. Model Selection
- GPT-4.1 offers excellent price/performance for most use cases
- Consider GPT-5.1 for complex documents requiring latest capabilities

### 4. Image Optimization
- Use `low` detail mode for slide rendering (768x768)
- Reduces token count while maintaining accuracy

### 5. Monitor Usage
- Track Azure OpenAI token consumption in Azure Portal
- Set up cost alerts for unexpected spikes

---

## References

- [Azure OpenAI Pricing](https://azure.microsoft.com/pricing/details/cognitive-services/openai-service/)
- [Azure Document Intelligence Pricing](https://azure.microsoft.com/pricing/details/ai-document-intelligence/)
- [GPT-4.1 Vision Token Calculation](https://learn.microsoft.com/azure/ai-services/openai/how-to/gpt-with-vision)
- [Azure Blob Storage Pricing](https://azure.microsoft.com/pricing/details/storage/blobs/)
