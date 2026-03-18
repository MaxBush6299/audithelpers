# AI Calibration Evidence Evaluation Lab Series

Welcome to the **AI Calibration Evidence Evaluation** guided lab series. This hands-on course teaches Solution Engineers and audit teams how to deploy and operate a production-grade automation solution for evaluating audit evidence using Azure AI services and Logic Apps.

## What You'll Build

A **Logic App-based pipeline** that processes audit evidence (images of slides, forms, and documents) and returns structured evaluation decisions:

```json
{
  "auditElement": "System Access Control",
  "evidence": "Screenshot showing access control panel",
  "verdict": "APPROVED",
  "confidence": 0.92,
  "explanation": "Evidence clearly shows implemented access control with role-based enforcement."
}
```

**Key workflow:**
1. Upload audit evidence images to Azure Storage
2. Logic App extracts text from images (OCR + Vision AI)
3. Matches evidence to audit points
4. Evaluates using Azure OpenAI
5. Returns structured JSON with verdict + confidence + explanation
6. (Optional) Display results in a Power Apps audit portal

---

## Prerequisites

- ✅ **Azure Subscription** with permissions to create resources (Resource Groups, App Service Plans, Logic Apps, Storage, AI Services)
- ✅ **Access to Azure AI Services** (quota for deployments like GPT-4.1 and Document Intelligence)
- ✅ **Browser** for Azure Portal (no local CLI required—this is portal-forward)
- ✅ **Audit evidence files** (bring your own PPTX slides, images, or documents—no sample data provided)

---

## Success Criteria

By completing this lab series (Labs 0-11), you will have:

- ✅ A working Logic App that processes audit evidence images end-to-end
- ✅ Understanding of the multimodal extraction architecture (native extraction + OCR + Vision AI)
- ✅ Ability to troubleshoot failures and extend the system
- ✅ JSON output consumable by Power Apps or other downstream systems

---

## Lab Sequence

| Lab | Title | Duration | Owner | Link |
|-----|-------|----------|-------|------|
| 0 | Environment Setup | 30 min | Moneypenny | [Lab 0](labs/lab-00-setup.md) |
| 1 | Understanding the Architecture | 20 min | M | [Lab 1](labs/lab-01-architecture.md) |
| 2 | Deploy Document Intelligence | 15 min | Moneypenny | [Lab 2](labs/lab-02-document-intelligence.md) |
| 3 | Deploy Azure AI Services | 20 min | Bond | [Lab 3](labs/lab-03-ai-services.md) |
| 4 | Deploy Storage Account | 15 min | Bond | [Lab 4](labs/lab-04-storage.md) |
| 5 | Create the Logic App | 25 min | Bond | [Lab 5](labs/lab-05-logic-app-create.md) |
| 6 | Add Image Upload Trigger | 20 min | Bond | [Lab 6](labs/lab-06-image-upload-trigger.md) |
| 7 | Integrate Document Intelligence | 25 min | Bond | [Lab 7](labs/lab-07-document-intelligence-integration.md) |
| 8 | Add Azure OpenAI Vision | 30 min | Bond | [Lab 8](labs/lab-08-openai-vision.md) |
| 9 | Build Validation Logic | 25 min | Bond | [Lab 9](labs/lab-09-validation-logic.md) |
| 10 | Generate JSON Output | 20 min | Bond | [Lab 10](labs/lab-10-json-output.md) |
| 11 | End-to-End Testing | 30 min | Felix | [Lab 11](labs/lab-11-testing.md) |
| 12 | Power Apps Audit Portal (Optional) | 60 min | Q | [Lab 12](labs/lab-12-power-apps.md) |

**Total Time:**
- Core labs (0-11): ~5.5 hours
- Optional Power Apps (Lab 12): +60 min

---

## How to Use This Lab Series

1. **Start with Lab 0** — Set up your Azure environment and clone the repository
2. **Read Lab 1** — Understand the architecture before building
3. **Follow Labs 2-4** — Deploy Azure resources (portal clicks only)
4. **Build Labs 5-10** — Create the Logic App and wire up each stage
5. **Test with Lab 11** — Verify end-to-end and troubleshoot
6. **(Optional) Lab 12** — Build a Power Apps portal for non-technical users

Each lab takes 15-30 minutes and builds on the previous one. **No prior Logic App experience required** — we walk through each step.

---

## Architecture Overview

```
Audit Evidence (Images/PPTX)
        ↓
    Upload to Blob Storage
        ↓
    Logic App Trigger
        ↓
    ┌─────────────────────────────┐
    │ Stage 1: Extract Text       │ (OCR + Vision)
    └──────────────┬──────────────┘
                   ↓
    ┌─────────────────────────────┐
    │ Stage 2: Match to Audit Points
    └──────────────┬──────────────┘
                   ↓
    ┌─────────────────────────────┐
    │ Stage 3: Evaluate w/ Azure AI│
    └──────────────┬──────────────┘
                   ↓
    ┌─────────────────────────────┐
    │ Stage 4: Generate JSON Output│
    └──────────────┬──────────────┘
                   ↓
         JSON Results to Storage
      (Ready for Power Apps / API)
```

---

## What's Locked (No Changes)

These architectural decisions are final and will not change during the lab series:

1. **No Azure Functions** — All processing is inline Logic App actions; simpler deployment footprint
2. **Auth deferred** — Authentication is post-lab hardening; this MVP focuses on core logic
3. **JSON output format** — All results are structured JSON, consumable by Power Apps and downstream systems
4. **Bring your own data** — No sample files provided; you test with your own audit evidence
5. **Portal-forward** — All deployment via Azure Portal clicks; zero CLI required (except repo clone)
6. **GitHub Pages docs** — This site uses Microsoft Learn styling; all labs are browser-based
7. **Linear sequence** — Labs must be completed in order; each builds on the previous

---

## Support & Questions

Each lab includes:
- ✅ **Step-by-step portal screenshots** (where available)
- ✅ **Troubleshooting section** — common errors and fixes
- ✅ **Concept boxes** — why we're doing this (non-technical overview)
- ✅ **Links to official Azure docs** — when you want to go deeper

For questions, see the **[Troubleshooting Guide](labs/troubleshooting.md)** or check the **[Architecture Deep Dive](labs/lab-01-architecture.md)**.

---

## Next Steps

**Ready to get started?** → **[Go to Lab 0: Environment Setup](labs/lab-00-setup.md)**

---

*Lab series maintained by the AI Calibration team. Last updated: March 2026.*
