# Lab 1: Understanding the Architecture

**Estimated Time:** 20 minutes (reading)  
**Prerequisites:** Lab 0 (Environment Setup)  
**Next Lab:** [Lab 2: Deploy Document Intelligence →](lab-02-document-intelligence.md)

---

## Learning Objectives

By the end of this lab, you will understand:

- ✅ The **4-stage pipeline**: Extract Elements → Extract Evidence → Match → Evaluate
- ✅ Why **multimodal extraction** is essential (native text + OCR + vision AI)
- ✅ How **Logic Apps** will orchestrate this workflow
- ✅ What Azure services power each stage and why they matter

---

## The Problem We're Solving

**Audit Evidence Validation** is manual and slow. Today:

1. Auditors collect PowerPoint slides, photos, and scanned documents as evidence
2. They manually compare each piece of evidence against audit requirements
3. They make a judgment call: approved, rejected, or needs clarification
4. They document everything in a spreadsheet or Word document

**Our solution automates this:**
- Extracts evidence content from images and slides automatically
- Matches evidence to specific audit requirements
- Uses AI to evaluate whether evidence meets the criteria
- Returns a structured, repeatable verdict with confidence scores

---

## The 4-Stage Pipeline

Here's how audit evidence flows through the system:

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Stage 1    │     │   Stage 2    │     │   Stage 3    │     │   Stage 4    │
│              │     │              │     │              │     │              │
│  Elements    │ --> │   Evidence   │ --> │    Match     │ --> │   Evaluate   │
│              │     │              │     │              │     │              │
│ (Excel data) │     │ (OCR + Vision)    │  (Algorithm) │     │  (LLM/GPT)   │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
        │                   │                    │                    │
        ▼                   ▼                    ▼                    ▼
   audit_points    slide_content      matched_pairs         verdicts
   + criteria      + extracted_text   + confidence          + explanations
```

### Stage 1: Extract Elements from Audit Spreadsheet

**What it does:** Reads the audit requirements spreadsheet and extracts each audit point and its criteria.

**Input:** Excel file with columns like:
- Audit Point ID
- Audit Requirement
- Success Criteria
- Auditor Instructions

**Output:** `elements.json` — a structured list of what we're looking for

**Example:**
```json
{
  "audit_point_id": "AP-001",
  "requirement": "System Access Control",
  "criteria": "All users must have role-based access control (RBAC) configured",
  "instructions": "Look for screenshots showing RBAC settings or access control panel"
}
```

**Azure Service:** ✅ **No cloud service needed** — this is local Excel parsing (Python openpyxl library)

---

### Stage 2: Extract Evidence from Slides (Multimodal Magic)

**What it does:** Reads PowerPoint slides or images and extracts all text content using three complementary sources.

**Why Multimodal?** A single approach isn't enough:

| Source | Captures | Example |
|--------|----------|---------|
| **Native PPTX Text** | Text typed directly into slides | Slide title, bullet points |
| **OCR (Document Intelligence)** | Text in embedded screenshots/photos | Screenshots of forms, system panels |
| **AI Vision (GPT)** | Handwriting, complex layouts, context | Handwritten notes, whiteboard photos |

**The Process:**

1. **Extract native text** from the PPTX file (fastest, most reliable)
2. **Run OCR** on any embedded images using Azure Document Intelligence
3. **Render each slide** as an image (high-quality visual)
4. **Send to GPT-4.1 or GPT-5.1** for vision analysis
   - AI reviews all extracted text
   - AI looks at the rendered slide image
   - AI validates, corrects, and structures the final output

**Output:** `evidence.json` — all text from all slides, in reading order

**Example:**
```json
{
  "slide_index": 8,
  "extracted_text": "Access Control Configuration\n\n✓ Role-based access control enabled\n✓ Admin users: 3\n✓ Read-only users: 12\n\nLast configured: 2024-03-15 by J. Smith"
}
```

**Azure Services:**
- 🟦 **Azure Document Intelligence** — OCR on embedded images
- 🟦 **Azure AI Foundry (GPT-4.1/5.1)** — multimodal vision analysis

---

### Stage 3: Match Evidence to Audit Points

**What it does:** Compares each piece of evidence to each audit requirement and identifies matches.

**How it works:**
1. Takes the audit points from Stage 1
2. Takes the evidence slides from Stage 2
3. Runs a matching algorithm that scores how relevant each slide is to each audit point
4. Creates pairs: (audit_point, evidence_slide, confidence_score)

**Output:** `matched_evidence.json` — which slides address which audit requirements

**Example:**
```json
{
  "audit_point_id": "AP-001",
  "requirement": "System Access Control",
  "matched_slides": [
    {
      "slide_index": 8,
      "slide_text": "Access Control Configuration...",
      "relevance_score": 0.95,
      "reasoning": "Slide directly shows RBAC configuration"
    }
  ]
}
```

**Azure Service:** ✅ **No cloud service needed** — this is logic executed in the Logic App (pattern matching)

---

### Stage 4: Evaluate Evidence Against Criteria

**What it does:** Uses an AI agent to judge whether each piece of matched evidence actually **meets** the audit criteria.

**How it works:**
1. Takes a matched pair: (audit requirement + evidence slide)
2. Sends to GPT-4.1/5.1 with the question: "Does this evidence meet the criteria?"
3. AI returns:
   - **Verdict:** APPROVED, REJECTED, or CONDITIONAL
   - **Confidence:** 0.0 to 1.0 (how sure is the AI)
   - **Explanation:** Why it made this judgment

**Output:** `evaluation_results.json` — verdicts with explanations

**Example:**
```json
{
  "audit_point_id": "AP-001",
  "verdict": "APPROVED",
  "confidence": 0.92,
  "explanation": "The slide clearly shows role-based access control is configured with proper admin/read-only role separation. Configuration date and technician are documented.",
  "extracted_evidence": [
    "Role-based access control enabled",
    "Admin users: 3",
    "Read-only users: 12",
    "Last configured: 2024-03-15 by J. Smith"
  ],
  "processing_time_ms": 2340
}
```

**Azure Service:**
- 🟦 **Azure AI Foundry (GPT-4.1/5.1)** — LLM evaluation with instructions

---

## The JSON Output Format

This is what you'll get at the end of the pipeline. It's designed to be consumed by Power Apps, Power BI dashboards, or downstream APIs.

```json
{
  "audit_point_id": "AP-001",
  "audit_requirement": "System Access Control",
  "verdict": "APPROVED",
  "confidence": 0.92,
  "explanation": "The slide clearly shows the calibration procedure was followed with proper documentation of technician and date.",
  "extracted_evidence": [
    "calibration date: 2024-03-15",
    "technician: J. Smith",
    "procedure: Standard calibration checklist",
    "equipment verified: Yes"
  ],
  "source_slide_index": 8,
  "processing_time_ms": 2340,
  "timestamp": "2024-03-18T10:32:15Z"
}
```

**Key fields:**
- `verdict` — APPROVED | REJECTED | CONDITIONAL
- `confidence` — 0.0 to 1.0 (0 = unsure, 1.0 = very sure)
- `explanation` — Human-readable reasoning
- `extracted_evidence` — Key facts the AI found
- `processing_time_ms` — How long the evaluation took

---

## Why Logic Apps?

We're using **Azure Logic Apps** to orchestrate this entire pipeline. Here's why:

| Benefit | Why It Matters |
|---------|----------------|
| **Portal-Native** | No code deployment needed; build in the Azure Portal with clicks |
| **Pre-Built Connectors** | Direct integrations to Azure AI, Storage, and Office 365 |
| **Visual Workflow** | See the entire pipeline as a diagram; easy to explain to non-technical users |
| **Error Handling** | Retry logic, error notifications, and detailed run history built-in |
| **Audit Trail** | Every execution is logged; track what happened and when |
| **Scalability** | Automatically handles parallel processing without custom code |
| **Maintenance** | Auditors can modify the workflow themselves (within guardrails) |

**Logic Apps are ideal for this use case** because:
- We're orchestrating multiple Azure services
- The workflow is mostly glue (calling APIs, transforming data)
- Auditors will maintain and extend it after deployment
- Visual workflows are easier to audit than code

---

## The Azure Services Involved

Here's the complete Azure service stack:

### Core Processing

| Service | Purpose | Cost Model | When Used |
|---------|---------|-----------|-----------|
| **Document Intelligence** | Extract text from embedded images (OCR) | Per page processed | Every embedded image in evidence |
| **Azure OpenAI (GPT-4.1/5.1)** | Multimodal vision + LLM evaluation | Per tokens consumed | Every slide + every evaluation |
| **Blob Storage** | Store uploaded evidence and results | Per GB stored + operations | All pipeline input/output files |

### Logic Apps Infrastructure

| Service | Purpose |
|---------|---------|
| **Logic App (Standard)** | The orchestration engine and workflow host |
| **App Service Plan** | Compute for the Logic App |
| **Application Insights** | Monitoring and diagnostics |

### Support

| Service | Purpose |
|---------|---------|
| **Key Vault** | Secure storage for API keys and secrets |
| **Azure Monitor** | Alerts and dashboards |

---

## Data Flow Diagram

Here's how data moves through the system:

```
┌────────────────────────────────────────────────────────────────────┐
│                    AUDITOR (End User)                              │
│  Uploads PowerPoint slides + audit requirements Excel              │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
        ┌─────────────────────────────────────┐
        │  Blob Storage                       │
        │  (Evidence uploaded)                │
        └────────────┬────────────────────────┘
                     │
                     ▼
        ┌─────────────────────────────────────┐
        │  Logic App Trigger                  │
        │  (File upload detected)             │
        └────────────┬────────────────────────┘
                     │
              ┌──────┴──────┬──────────────────────┐
              ▼             ▼                      ▼
        ┌──────────┐  ┌──────────┐  ┌──────────────────────┐
        │  Doc     │  │  Blob    │  │  Condition Logic     │
        │  Intel   │  │  Extract │  │  (Match algorithm)   │
        │  (OCR)   │  │  (Native)│  │                      │
        └────┬─────┘  └────┬─────┘  └──────────┬───────────┘
             │             │                    │
             └─────────────┼────────────────────┘
                           │
                           ▼
                 ┌──────────────────────┐
                 │  Render as Image     │
                 │  (Each slide)        │
                 └──────────┬───────────┘
                            │
                            ▼
              ┌──────────────────────────────┐
              │  Azure OpenAI (GPT Vision)   │
              │  - Validate text            │
              │  - Evaluate against criteria│
              │  - Generate explanation     │
              └──────────┬───────────────────┘
                         │
                         ▼
              ┌──────────────────────────┐
              │  Format JSON Output      │
              │  (Verdict + confidence)  │
              └──────────┬────────────────┘
                         │
                         ▼
              ┌──────────────────────────┐
              │  Blob Storage (Results)  │
              │  Ready for Power Apps    │
              └──────────────────────────┘
```

---

## Conceptual Walkthrough

Let's trace one audit requirement through the entire pipeline:

### Requirements
- **Audit Point:** "Equipment was properly calibrated"
- **Success Criteria:** "Evidence must show calibration date, technician name, and procedure followed"
- **What auditors look for:** Screenshots or photos of calibration records

### Stage 1: Extract Requirements
```
Input: Excel file
Output: {
  "id": "CAL-001",
  "requirement": "Equipment was properly calibrated",
  "criteria": "Must show date, technician, procedure"
}
```

### Stage 2: Extract Evidence
```
Input: PowerPoint slide (image of a calibration form)
Output: {
  "slide_index": 8,
  "text": "CALIBRATION RECORD\nDate: 2024-03-15\nTechnician: J. Smith\nProcedure: Standard Cal Check\n✓ Passed all checks"
}
```

### Stage 3: Match
```
Logic: Does this slide relate to CAL-001?
Output: {
  "audit_point": "CAL-001",
  "slide_index": 8,
  "match_score": 0.98,
  "reason": "Calibration record directly addresses requirement"
}
```

### Stage 4: Evaluate
```
Logic App sends to GPT:
"Does this evidence meet the criteria?
  - Criteria: Show date, technician, procedure
  - Evidence: [text from slide above]"

Output: {
  "verdict": "APPROVED",
  "confidence": 0.95,
  "explanation": "Evidence clearly shows calibration was performed on 2024-03-15 by J. Smith following standard procedure. All criteria met."
}
```

---

## Key Takeaways

1. **4-Stage Pipeline** — Extract, Extract (multimodal), Match, Evaluate
2. **Multimodal = Robust** — Combining native text, OCR, and AI vision handles any document format
3. **Logic Apps = No Code** — Portal clicks, visual workflows, easy to audit and maintain
4. **AI Evaluation = Intelligent** — Uses LLMs to make judgment calls, not just keyword matching
5. **Structured Output** — JSON verdicts ready for Power Apps, dashboards, or downstream systems

---

## Next Steps

Now that you understand the architecture:

1. **Lab 2** will deploy Document Intelligence for OCR
2. **Lab 3** will deploy Azure AI Services for GPT access
3. **Labs 5-10** will build the Logic App that ties it all together
4. **Lab 11** will test the end-to-end flow

---

## Resources

- [Azure Document Intelligence Overview](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/)
- [Azure OpenAI Service](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
- [Azure Logic Apps Documentation](https://learn.microsoft.com/en-us/azure/logic-apps/)
- [Azure Blob Storage](https://learn.microsoft.com/en-us/azure/storage/blobs/)

---

[← Previous: Environment Setup](lab-00-setup.md) | [Next: Deploy Document Intelligence →](lab-02-document-intelligence.md)
