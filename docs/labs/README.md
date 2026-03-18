# Lab Quick Reference

This page provides a quick lookup table for all labs in the AI Calibration Evidence Evaluation series.

## All Labs at a Glance

| Lab | Title | Duration | Owner | Prereqs | Status |
|-----|-------|----------|-------|---------|--------|
| **0** | Environment Setup | 30 min | Moneypenny | None | Available |
| **1** | Understanding the Architecture | 20 min | M | Lab 0 | Available |
| **2** | Deploy Document Intelligence | 15 min | Moneypenny | Lab 0 | Available |
| **3** | Deploy Azure AI Services | 20 min | Bond | Lab 0 | Available |
| **4** | Deploy Storage Account | 15 min | Bond | Lab 0 | Available |
| **5** | Create the Logic App | 25 min | Bond | Labs 2-4 | Available |
| **6** | Add Image Upload Trigger | 20 min | Bond | Lab 5 | Available |
| **7** | Integrate Document Intelligence | 25 min | Bond | Lab 6 | Available |
| **8** | Add Azure OpenAI Vision | 30 min | Bond | Lab 7 | Available |
| **9** | Build Validation Logic | 25 min | Bond | Lab 8 | Available |
| **10** | Generate JSON Output | 20 min | Bond | Lab 9 | Available |
| **11** | End-to-End Testing | 30 min | Felix | Lab 10 | Available |
| **12** | Power Apps Audit Portal (Optional) | 60 min | Q | Lab 11 | Available |

---

## Lab Grouping by Phase

### Phase 1: Setup & Foundations (Labs 0-1)
- **Lab 0:** Create Azure Resource Group, `.env` file, clone repo
- **Lab 1:** Walkthrough of architecture; read-only; no deployments

**Time: 50 min**

### Phase 2: Deploy Azure Services (Labs 2-4)
- **Lab 2:** Document Intelligence (OCR)
- **Lab 3:** Azure AI Services (GPT-4.1 with Vision)
- **Lab 4:** Storage Account & Blob containers

**Time: 50 min** | **Prerequisite:** Lab 0

### Phase 3: Build the Logic App (Labs 5-10)
- **Lab 5:** Create Logic App Standard and first workflow
- **Lab 6:** Blob trigger for image upload
- **Lab 7:** Call Document Intelligence for text extraction
- **Lab 8:** Call Azure OpenAI for multimodal analysis
- **Lab 9:** Build validation & matching logic
- **Lab 10:** Generate structured JSON output

**Time: 2 hrs 35 min** | **Prerequisite:** Labs 2-4

### Phase 4: Verify & Extend (Labs 11-12)
- **Lab 11:** Upload test files, monitor execution, verify JSON output
- **Lab 12:** (Optional) Build Power Apps portal for auditors

**Time: 30 min core + 60 min optional** | **Prerequisite:** Lab 10 (Lab 11), Lab 11 (Lab 12)

---

## Jump to a Specific Lab

### Foundations
- [Lab 0: Environment Setup](lab-00-setup.md)
- [Lab 1: Understanding the Architecture](lab-01-architecture.md)

### Azure Services
- [Lab 2: Deploy Document Intelligence](lab-02-document-intelligence.md)
- [Lab 3: Deploy Azure AI Services](lab-03-ai-services.md)
- [Lab 4: Deploy Storage Account](lab-04-storage.md)

### Logic App Implementation
- [Lab 5: Create the Logic App](lab-05-logic-app-create.md)
- [Lab 6: Add Image Upload Trigger](lab-06-image-upload-trigger.md)
- [Lab 7: Integrate Document Intelligence](lab-07-document-intelligence-integration.md)
- [Lab 8: Add Azure OpenAI Vision](lab-08-openai-vision.md)
- [Lab 9: Build Validation Logic](lab-09-validation-logic.md)
- [Lab 10: Generate JSON Output](lab-10-json-output.md)

### Testing & Extension
- [Lab 11: End-to-End Testing](lab-11-testing.md)
- [Lab 12: Power Apps Audit Portal (Optional)](lab-12-powerapps.md)

---

## What Each Lab Phase Teaches

### Phase 1: Setup & Foundations
- Azure security best practices (secrets, RBAC)
- How the 5-stage pipeline works (conceptual)
- Visual architecture overview

### Phase 2: Deploy Azure Services
- Document Intelligence (OCR) pricing and capabilities
- Azure AI Services (GPT) deployment
- Blob Storage for file handling

### Phase 3: Build the Logic App
- Logic App Standard workflows
- Blob triggers
- HTTP actions to call Azure services
- JSON parsing and transformation
- Control flow (loops, conditions)

### Phase 4: Verify & Extend
- Testing Logic App workflows
- Reading run history and logs
- Troubleshooting common failures
- (Optional) Building a frontend UI in Power Apps

---

## Success Checkpoint per Phase

### After Phase 1
- ✅ Azure Resource Group created
- ✅ Repository cloned
- ✅ `.env` file configured
- ✅ Understand the 5-stage pipeline flow

### After Phase 2
- ✅ Document Intelligence endpoint in `.env`
- ✅ Azure AI Services endpoint in `.env`
- ✅ Storage Account with 4 blob containers

### After Phase 3
- ✅ Logic App created and triggered
- ✅ Image upload automatically calls Document Intelligence
- ✅ Azure OpenAI Vision analyzes images
- ✅ Logic App outputs structured JSON

### After Phase 4
- ✅ End-to-end test successful: image → JSON verdict
- ✅ (Optional) Power Apps portal displays results

---

## Common Navigation Patterns

**"I just finished Lab 5, what's next?"**  
→ [Lab 6: Add Image Upload Trigger](lab-06-image-upload-trigger.md)

**"I'm stuck on deploying Azure AI Services."**  
→ [Lab 3 Troubleshooting](lab-03-ai-services.md#troubleshooting) + [General Troubleshooting](troubleshooting.md)

**"I want to understand the architecture before deploying."**  
→ [Lab 1: Understanding the Architecture](lab-01-architecture.md)

**"I just want the Power Apps portal, can I skip the Logic App?"**  
→ No. Lab 11 (testing) confirms the Logic App works; Lab 12 requires that. Start at Lab 5.

**"How long will this take?"**  
→ **Core labs (0-11):** ~5.5 hours over a few days | **With Power Apps:** +60 min

---

## Resources by Topic

### Architecture & Concepts
- [Lab 1: Understanding the Architecture](lab-01-architecture.md)
- [Multimodal Extraction Concept Guide](concepts/multimodal-extraction.md)
- [Evidence Matching Concept Guide](concepts/evidence-matching.md)

### Deployment & Configuration
- [Lab 0: Environment Setup](lab-00-setup.md)
- [Lab 2-4: Azure Services](lab-02-document-intelligence.md)

### Logic App Development
- [Lab 5: Create the Logic App](lab-05-logic-app-create.md)
- [Labs 6-10: Build Each Stage](lab-06-image-upload-trigger.md)

### Testing & Troubleshooting
- [Lab 11: End-to-End Testing](lab-11-testing.md)
- [Troubleshooting Guide](troubleshooting.md)

### Reference
- [JSON Schemas](reference/json-schemas.md)
- [Cost Estimation](reference/cost-estimation.md)

---

## Tips for Success

1. **Don't skip Lab 1** — The architecture overview prevents confusion later
2. **Test as you go** — After Lab 5, upload a test image to verify the trigger works
3. **Save the `.env` file** — You'll reference it across all labs
4. **Keep a notebook** — Log the endpoints and keys from each service (or keep `.env` handy)
5. **Join the team chat** — Ask questions if something feels unclear

---

## Team Contacts by Lab

| Lab(s) | Owner | Contact |
|--------|-------|---------|
| 0, 2 | Moneypenny | moneypenny@team.local |
| 1 | M (Lead) | m@team.local |
| 3-10 | Bond | bond@team.local |
| 11 | Felix | felix@team.local |
| 12 | Q | q@team.local |

---

*Last updated: March 2026*
