---
layout: default
title: Lab 2: Document Intelligence
parent: Labs
nav_order: 3
---
# Lab 2: Deploy Document Intelligence

**Estimated duration:** 15 minutes  
**Prerequisites:** Lab 0 (Environment Setup), Lab 1 (Architecture)  
**Owner:** Moneypenny  
**Objective:** Deploy an Azure Document Intelligence resource and configure it for OCR in the audit pipeline.

---

## What You'll Learn

In this lab, you will:

- ✅ Understand what Azure Document Intelligence does and why we need it
- ✅ Deploy a Document Intelligence resource in Azure Portal
- ✅ Retrieve the endpoint URL and API key
- ✅ Store credentials securely in your `.env` file
- ✅ Learn why S0 pricing tier is required for layout analysis

---

## Prerequisites

Before starting this lab, ensure you have:

- ✅ **Lab 0 completed** — Resource Group created and `.env` file ready
- ✅ **Azure Portal access** — Contributor or higher access to your Resource Group
- ✅ **Resource Group name** — Copy it from Lab 0 (e.g., `rg-audit-pipeline-js`)

---

## What Is Document Intelligence?

**Azure Document Intelligence** (formerly Cognitive Services Computer Vision API) is an AI service that extracts structured data from documents and images using OCR (Optical Character Recognition) and deep learning models.

### Why We Need It

In the audit pipeline, PowerPoint evidence slides often contain:
- Screenshots of system interfaces
- Photos of physical equipment or documents
- Scanned forms and compliance records
- Handwritten notes or annotations

Document Intelligence extracts text from these images with high accuracy, understanding layout, tables, forms, and hierarchical structure. This is **Stage 2: Extract Evidence** in the pipeline.

### What We'll Use: The Layout API

The **Layout API** is the specific Document Intelligence model for this project:

| Feature | What It Does | Example |
|---------|-------------|---------|
| **Text Extraction** | Recognizes all text with position and formatting | "Role-Based Access Control: ✓ Enabled" |
| **Layout Understanding** | Preserves document structure | Headers, paragraphs, bullet points, tables |
| **Reading Order** | Determines natural reading order | Top-to-bottom, left-to-right with context |
| **Table Detection** | Extracts table content and relationships | Compliance matrices, audit findings tables |
| **Form Recognition** | Identifies form fields and values | Equipment calibration records, sign-off sheets |

### Pricing Tier: Why S0?

We're deploying the **S0 (Standard)** pricing tier because:
- ✅ Required for Layout API (Lite tier doesn't support it)
- ✅ Supports high-volume OCR in the audit pipeline
- ✅ Includes all features we need: forms, tables, layout analysis
- ✅ Reasonable cost for production use (~$1-2 per 1000 pages)

---

## Step 1: Navigate to Azure Portal

1. Go to [Azure Portal](https://portal.azure.com)
2. Sign in with your Azure account
3. You should see your Resource Group from Lab 0 in the recent resources area

---

## Step 2: Create a Document Intelligence Resource

### 2.1 Open the Resource Creation Flow

1. In the Azure Portal, click the **+ Create a resource** button (top-left or search bar)
2. In the search box, type **Document Intelligence**
3. From the results, select **Document Intelligence** (the official Microsoft service, not a third-party offering)
4. Click **Create**

### 2.2 Fill in the Resource Details

You'll now see the **Create Document Intelligence** form. Fill in the fields:

#### Subscription
- **Subscription:** Select your Azure subscription (should auto-populate)

#### Resource Group
- **Resource Group:** Select the Resource Group you created in Lab 0 (e.g., `rg-audit-pipeline-js`)
  - If you don't see it, check that you're in the correct subscription

#### Instance Details
- **Region:** Select the **same region** as your Resource Group (e.g., `East US 2`)
  - ✅ Keeping resources in the same region reduces latency and data transfer costs
- **Name:** Enter a name following the naming convention: `doc-intel-audit-{your-initials}`
  - *Example:* If your initials are `js`, use `doc-intel-audit-js`
  - ✅ This naming convention helps organize resources when multiple team members share a subscription

#### Pricing Tier
- **Pricing Tier:** Select **S0 (Standard)**
  - ⚠️ Do NOT select "Lite" — it doesn't support the Layout API
  - S0 is required for form, table, and layout analysis

#### Tags (Optional)
- **Tags:** You can optionally add tags like `Project: AI-Calibration` and `Environment: Dev`
  - Tags help with billing and resource organization

### 2.3 Review and Create

1. Click **Review + create**
2. Review the summary (subscription, Resource Group, name, region, pricing tier)
3. Click **Create**

Wait for the deployment to complete. You should see a **Deployment succeeded** message (usually 30-60 seconds).

---

## Step 3: Retrieve Your Endpoint and Key

Once deployment is complete:

### 3.1 Navigate to Your Resource

1. Click **Go to resource** (from the deployment completion page), OR
2. Search for your resource name (`doc-intel-audit-{initials}`) in the Azure Portal search bar
3. You're now on the Document Intelligence resource overview page

### 3.2 Get the Endpoint URL

1. In the left sidebar, click **Keys and Endpoint**
2. You'll see:
   - **Endpoint:** A URL like `https://eastus2.api.cognitive.microsoft.com/`
   - **Key 1:** Your primary API key
   - **Key 2:** Your secondary API key

3. Copy the **Endpoint** URL (you'll need it in Step 4)

### 3.3 Get the API Key

1. On the same **Keys and Endpoint** page, copy **Key 1** (the primary key)
2. Never share this key; treat it like a password

---

## Step 4: Update Your .env File

Now you'll add the Document Intelligence credentials to your `.env` file.

### 4.1 Open Your .env File

1. Open your `.env` file from Lab 0 (located in your project root directory)
2. Find the section that says `# Document Intelligence (Lab 2)`

### 4.2 Fill in the Values

Replace the placeholder values with what you just copied:

```bash
# Document Intelligence (Lab 2)
DOCUMENT_INTELLIGENCE_ENDPOINT=https://eastus2.api.cognitive.microsoft.com/
DOCUMENT_INTELLIGENCE_KEY=your-key-here
```

**Example:**
```bash
# Document Intelligence (Lab 2)
DOCUMENT_INTELLIGENCE_ENDPOINT=https://eastus2.api.cognitive.microsoft.com/
DOCUMENT_INTELLIGENCE_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
```

### 4.3 Save Your File

Save the `.env` file locally. Do **NOT** commit it to Git.

---

## Security & Best Practices

### ⚠️ Keep Your Key Safe

- ✅ **DO:** Store the key in `.env` (local, untracked)
- ✅ **DO:** Keep `.env` in your `.gitignore`
- ✅ **DO:** Rotate keys every 90 days (regenerate them in Azure Portal)
- ❌ **DON'T:** Commit `.env` to GitHub or any repository
- ❌ **DON'T:** Share keys in Slack, email, or documentation
- ❌ **DON'T:** Hardcode keys in your code

### Production Hardening

For production deployments (after core labs are complete):

1. **Use Azure Key Vault** — Store keys in Key Vault instead of `.env`
2. **Use Managed Identity** — In Logic App, authenticate via managed identity instead of API keys
3. **Rotate keys regularly** — Every 90 days, regenerate keys in Azure Portal
4. **Enable Azure Monitor** — Log all API calls and errors
5. **Set up alerts** — If API failures spike, get notified

See [Azure Well-Architected Framework - Security](https://learn.microsoft.com/en-us/azure/architecture/framework/security/) for more.

---

## Verification Checklist

Verify that your Document Intelligence resource is ready:

- ✅ **Resource deployed:** `doc-intel-audit-{initials}` appears in your Resource Group
- ✅ **Endpoint retrieved:** You have a URL like `https://eastus2.api.cognitive.microsoft.com/`
- ✅ **Key stored securely:** Key 1 is in your `.env` file, not in code or Git
- ✅ **Region matches:** Document Intelligence is in the same region as your Resource Group
- ✅ **Pricing tier is S0:** Verified in the resource overview under "Pricing tier"

---

## Understanding Document Intelligence APIs

While we'll primarily use the **Layout API** via Logic App, it's helpful to know what other APIs are available:

| API | Use Case |
|-----|----------|
| **Layout API** | General document layout, text, tables (what we're using) |
| **General Document** | Forms with key-value pairs and checkboxes |
| **Read API** | Simple text extraction without layout analysis |
| **Business Card** | Extracts contact info from business cards |
| **Invoice** | Extracts line items, amounts, vendor info |
| **Receipt** | Extracts vendor, date, items, total from receipts |

For the audit pipeline, **Layout API** is sufficient because audit evidence is typically screenshots, forms, or photos — not specialized documents like invoices.

---

## Troubleshooting

### Q: I see "Pricing tier 'Lite' does not support this operation"

**A:** You selected the Lite pricing tier. Document Intelligence Lite doesn't support the Layout API. Delete this resource and create a new one, selecting **S0 (Standard)** instead.

### Q: I can't find "Document Intelligence" in the create resource search

**A:** Make sure you're searching for "Document Intelligence" (the current name). Older documentation may refer to it as "Computer Vision" or "Form Recognizer." If you can't find it:
1. Try searching for **"Azure AI Document Intelligence"**
2. Verify you have the correct subscription and region selected

### Q: I got "Insufficient quota" error

**A:** Your subscription may have hit the quota limit for this region. Either:
1. Use a different region (e.g., switch from `East US 2` to `West US 2`)
2. Contact your Azure administrator to request a quota increase
3. Wait a few minutes and try again (temporary limit may have reset)

### Q: Where do I find my Resource Group name?

**A:** From Lab 0, your Resource Group should be named `rg-audit-pipeline-{your-initials}`. If you forget:
1. Go to Azure Portal → **Resource Groups**
2. Look for the one you created in Lab 0
3. Copy its exact name

### Q: Can I change the region after creating the resource?

**A:** No. If you need to change the region, delete the resource and create a new one in the correct region. Your `.env` file will auto-update once you have the new endpoint.

---

## Key Concepts

### OCR (Optical Character Recognition)

**OCR** is the process of converting images of text into machine-readable text. Document Intelligence uses advanced deep learning models to:
- Recognize characters with 99%+ accuracy
- Understand layout and structure
- Handle handwriting, different fonts, and various languages

### API Endpoint

An **endpoint** is the URL where your service listens for requests. Every Azure Cognitive Service has a unique endpoint based on region:
- East US 2: `https://eastus2.api.cognitive.microsoft.com/`
- West US 2: `https://westus2.api.cognitive.microsoft.com/`

When your Logic App calls Document Intelligence, it uses this endpoint + your API key to authenticate.

### API Key

An **API key** is a secret credential that proves you're authorized to use the service. Think of it as a password:
- Keep it private (like a password)
- Rotate it periodically
- Use different keys for different environments (dev, staging, prod)

---

## Next Steps

Document Intelligence is now deployed and ready to use. In **Lab 3**, you'll deploy Azure OpenAI (GPT-4/5) for the multimodal vision analysis and evaluation stages of the pipeline.

Before Lab 3, optionally:
- Review [Azure Document Intelligence documentation](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/)
- Explore the [Layout API reference](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/how-to-guides/use-sdk-v4-0?view=doc-intel-docs&tabs=csharp)

When you're ready to proceed:

---

[← Previous: Understanding the Architecture](lab-01-architecture.md) | [Next: Deploy Azure AI Services →](lab-03-azure-ai.md)

---

*Lab 2 created by Moneypenny. Last updated: March 2026.*
