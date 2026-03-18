---
layout: default
title: Lab 4: Storage Account
parent: Labs
nav_order: 5
---
# Lab 4: Deploy Azure Blob Storage Account

**Estimated duration:** 20 minutes  
**Owner:** Bond  
**Objective:** Create an Azure Blob Storage account and containers for the audit pipeline to store evidence images and results.

---

## What You'll Learn

In this lab, you will:

- ✅ Understand Azure Blob Storage and when to use it for file-based workflows
- ✅ Create a Storage Account with naming conventions for global uniqueness
- ✅ Create containers for organizing input (evidence) and output (results)
- ✅ Retrieve your Storage Account connection string and name
- ✅ Update your `.env` file with storage credentials
- ✅ Understand how Logic App will use Blob Storage to trigger workflows

> **📝 Note:** This lab creates the storage infrastructure only. In Lab 5+, Logic App will read from the input container and write results to the output container.

---

## Prerequisites

Before starting this lab, ensure you have:

- ✅ **Lab 0 complete:** Resource Group created (`rg-audit-pipeline-{your-initials}`)
- ✅ **Azure subscription** with **Storage Account Contributor** or **Contributor** role at the Resource Group level
- ✅ **`.env` file** from Lab 0 with placeholders ready to fill in
- ✅ **Naming convention ready:** Know your initials for the storage account name

---

## What Is Azure Blob Storage?

**Blob Storage** is Azure's object storage service for unstructured data like images, documents, and JSON files. Unlike traditional file systems, Blob Storage is:

- **Scalable:** Store terabytes of data without managing disk space
- **Durable:** Data is automatically replicated and protected
- **Accessible:** Files are organized in containers (like folders) and accessed via HTTP/HTTPS
- **Audit-pipeline-ready:** Logic App can trigger workflows when files are uploaded

**Why Blob Storage for this project?**
- **Input container:** Stores audit evidence images uploaded by users
- **Output container:** Stores JSON results (confidence scores, explanations) for downstream apps
- **Trigger-friendly:** Logic App can watch for new blobs and start workflows automatically

---

## Step 1: Navigate to Create a Storage Account

### 1.1 Open Azure Portal

1. Go to [Azure Portal](https://portal.azure.com)
2. Sign in with your Azure account

### 1.2 Start Storage Account Creation

1. In the search bar at the top, type **storage account** and select **Storage accounts**
2. Click **+ Create** (or **Create storage account** if the button is visible)
3. This opens the "Create storage account" wizard

---

## Step 2: Configure Storage Account Settings

### 2.1 Basics Tab

Fill in the following details:

1. **Subscription:** Select your Azure subscription
2. **Resource group:** Select the Resource Group from Lab 0 (e.g., `rg-audit-pipeline-js`)
3. **Storage account name:** Use this naming convention:
   - Format: `staudit{your-initials}{4-random-digits}`
   - Example: If your name is Jane Smith, use `stauditjs1847`
   - **Important:** Storage account names are **globally unique**, must be **lowercase**, and **no hyphens**
   - If your name is taken, try a different 4-digit suffix

> **💡 Tip:** The Azure Portal will tell you if the name is available. Keep trying variations until you find one that works.

4. **Region:** Select the same region as your Resource Group from Lab 0 (e.g., **East US 2**)

### 2.2 Advanced Tab (Optional)

Leave default settings:
- **Performance:** Standard (sufficient for audit pipelines)
- **Redundancy:** LRS (Locally Redundant Storage) — appropriate for lab environments
  - *Note:* For production, use GRS (Geo-Redundant Storage) for data resilience

> **📝 Note:** For this lab, Standard + LRS is cost-effective and sufficient. In production, choose redundancy based on your organization's requirements.

### 2.3 Networking Tab (Optional)

Leave as default:
- **Connectivity method:** Public endpoint (lab environment)

> **📝 Note:** In production, restrict to private endpoints or specific IP ranges.

### 2.4 Data Protection Tab (Optional)

Leave as default. Your containers will be **Private** (recommended for security).

---

## Step 3: Review and Create

1. Click **Review + Create** at the bottom
2. Review your settings:
   - Storage account name matches the naming convention
   - Resource Group is correct
   - Region matches Lab 0
3. Click **Create**

Wait for the deployment to complete (~2 minutes). You'll see **"Deployment succeeded"** when done.

> **💡 Tip:** Copy your storage account name to your `.env` file immediately. You'll reference it in Step 5.

---

## Step 4: Create Containers

Containers are like folders in Blob Storage. You'll create two: one for input (evidence images) and one for output (JSON results).

### 4.1 Navigate to Your Storage Account

1. Once deployment is complete, click **Go to resource**
2. Or: In the search bar, search for your storage account name (e.g., `stauditjs1847`)
3. Click on your storage account in the results

### 4.2 Create the Input Container

1. In the left menu, select **Containers** (under "Data storage")
2. Click **+ Container**
3. Fill in:
   - **Name:** `audit-input`
   - **Public access level:** Private (default)
4. Click **Create**

> **🔒 Security Note:** Keep containers Private. Logic App will authenticate using the connection string, not public access.

### 4.3 Create the Output Container

1. Click **+ Container** again
2. Fill in:
   - **Name:** `audit-output`
   - **Public access level:** Private (default)
3. Click **Create**

You now have two containers:
- `audit-input` — where Logic App watches for new evidence images
- `audit-output` — where Logic App writes JSON results

---

## Step 5: Get Your Connection String and Account Name

Your connection string is a credential that lets applications (like Logic App) authenticate to your storage account.

### 5.1 Retrieve the Connection String

1. In your Storage Account menu, select **Access keys** (under "Security + networking")
2. Under **key1**, you'll see:
   - **Connection string:** A long string starting with `DefaultEndpointProtocol=https;...`
3. Click the **Copy** icon to copy the full connection string
4. Paste it somewhere safe (you'll need it in Step 6)

### 5.2 Get the Storage Account Name

1. In the same **Access keys** view, or in the Storage Account overview, note your storage account name (e.g., `stauditjs1847`)

> **⚠️ Security Warning:** Your connection string contains your storage account key — it's like a password. **Treat it with the same care as your API keys:**
> - Never share it via email or Slack
> - Never commit it to Git
> - Store it only in your `.env` file (which is in `.gitignore`)

---

## Step 6: Update Your .env File

Update your `.env` file with the Storage Account credentials.

### 6.1 Add Storage Variables

Open your `.env` file (from Lab 0) and update the Storage Account section:

```bash
# Storage Account (Lab 4)
STORAGE_CONNECTION_STRING=DefaultEndpointProtocol=https;AccountName=stauditjs1847;AccountKey=...
STORAGE_ACCOUNT_NAME=stauditjs1847
```

Replace:
- `STORAGE_CONNECTION_STRING` with the connection string from Step 5.1
- `STORAGE_ACCOUNT_NAME` with your storage account name (e.g., `stauditjs1847`)

### 6.2 Verify Your .env File

Your `.env` file should now look like:

```bash
# Azure Subscription
AZURE_SUBSCRIPTION_ID=your-subscription-id-here
AZURE_RESOURCE_GROUP=rg-audit-pipeline-{your-initials}
AZURE_LOCATION=eastus2

# Document Intelligence (Lab 2)
DOCUMENT_INTELLIGENCE_ENDPOINT=https://{region}.api.cognitive.microsoft.com/
DOCUMENT_INTELLIGENCE_KEY=your-doc-intelligence-api-key-here

# Azure AI Services / Azure OpenAI (Lab 3)
AZURE_OPENAI_ENDPOINT=https://{deployment-name}.openai.azure.com/
AZURE_OPENAI_KEY=your-azure-openai-api-key-here
AZURE_OPENAI_MODEL=gpt-4-vision-preview
AZURE_OPENAI_VERSION=2024-02-15-preview

# Storage Account (Lab 4) ✅ UPDATED
STORAGE_CONNECTION_STRING=DefaultEndpointProtocol=https;AccountName=stauditjs1847;AccountKey=...
STORAGE_ACCOUNT_NAME=stauditjs1847

# Logic App (Lab 5+)
LOGIC_APP_NAME=logic-app-audit-pipeline
LOGIC_APP_RESOURCE_GROUP=rg-audit-pipeline-{your-initials}
```

---

## Step 7: Understand How Logic App Uses Blob Storage

In Labs 5+, your Logic App workflow will:

1. **Watch for uploads:** Monitor the `audit-input` container for new images
2. **Extract and analyze:** Pass each image through Document Intelligence and Azure OpenAI
3. **Write results:** Save JSON output (confidence score, explanation, approval/rejection) to the `audit-output` container

**Example result file** (generated by Logic App):
```json
{
  "evidence_id": "slide_001.png",
  "audit_point": "Revenue Recognition Policy",
  "approved": true,
  "confidence": 0.94,
  "explanation": "Evidence clearly demonstrates adherence to ASC 606 requirements.",
  "timestamp": "2026-03-18T10:30:00Z"
}
```

Logic App uses your **connection string** (stored in `.env`) to authenticate to Blob Storage without needing additional passwords or keys.

---

## Step 8: Verify Your Setup

Use this checklist to confirm your Blob Storage is ready:

- ✅ **Storage Account created:** `staudit{initials}{4-digits}` exists in Azure Portal
- ✅ **Containers created:** `audit-input` and `audit-output` exist in your Storage Account
- ✅ **Containers are Private:** Confirmed in the Container properties
- ✅ **Connection string retrieved:** Stored in `.env` file (not committed to Git)
- ✅ **Storage Account name added:** `STORAGE_ACCOUNT_NAME` in `.env`
- ✅ **`.env` file NOT committed:** `.gitignore` still includes `*.env`

If all items are checked, you're ready for Lab 5 (Create the Logic App).

---

## Troubleshooting

### Q: My storage account name is not available

**A:** Storage account names are globally unique across Azure. If your chosen name is taken, try:
1. Different 4-digit suffix (e.g., `stauditjs1849` instead of `stauditjs1847`)
2. Different initials if available (e.g., `stauditjsmith1847`)

Keep trying until you find an available name.

### Q: How do I verify my containers are private?

**A:**
1. In your Storage Account, go to **Containers**
2. Click on a container (e.g., `audit-input`)
3. In the overview, check **Public access level** — it should be **Private**

If it's not Private, click **Change access level** and select **Private**.

### Q: I accidentally made my container public. How do I fix it?

**A:**
1. In your Storage Account, go to **Containers**
2. Right-click on the container and select **Change access level**
3. Select **Private**
4. Click **OK**

### Q: What if I lose my connection string?

**A:** You can retrieve it anytime:
1. Go to your Storage Account in the Portal
2. Click **Access keys** (under "Security + networking")
3. Copy the connection string from **key1**

> **⚠️ Security Note:** Every time you view your connection string, it's visible to anyone with access to your computer. If it's ever compromised, you can regenerate it by clicking **Regenerate** (this will rotate the key and invalidate old connection strings).

### Q: Can I use my storage account for other projects?

**A:** Yes, one storage account can have many containers for different projects. However, for this lab, keep input/output separated to make Logic App configuration easier.

---

## Key Concepts

### Blob Storage Containers

A **container** is a grouping mechanism within Blob Storage, similar to a folder:
- **Isolation:** Different projects can have different containers
- **Access control:** You can set permissions per container
- **Organization:** `audit-input` for uploads, `audit-output` for results

### Connection Strings

A **connection string** is a credential that includes:
- Storage account name
- Storage account key (secret)
- Protocol (HTTPS)

It's used by applications to authenticate without storing username/password. Treat it like an API key.

### Public vs. Private Containers

- **Private:** Only accessible with a valid connection string (secure for Logic App)
- **Public:** Accessible to anyone with the URL (not suitable for sensitive data)

For this project, **Private is always the right choice**.

### Redundancy (LRS vs. GRS)

- **LRS (Locally Redundant Storage):** Data replicated within one data center. Good for labs, cost-effective, less resilient
- **GRS (Geo-Redundant Storage):** Data replicated across regions. Good for production, higher cost, more resilient

For this lab, LRS is sufficient.

---

## Phase 2 Complete ✅

You now have all core Azure resources deployed:

| Resource | Lab | Status | .env Variable |
|---|---|---|---|
| Resource Group | Lab 0 | ✅ Created | `AZURE_RESOURCE_GROUP` |
| Document Intelligence | Lab 2 | ✅ Created | `DOCUMENT_INTELLIGENCE_ENDPOINT`, `DOCUMENT_INTELLIGENCE_KEY` |
| Azure OpenAI | Lab 3 | ✅ Created | `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_KEY` |
| Blob Storage | Lab 4 | ✅ Created | `STORAGE_CONNECTION_STRING`, `STORAGE_ACCOUNT_NAME` |

Your `.env` file now contains 6 critical variables:
```bash
AZURE_RESOURCE_GROUP
DOCUMENT_INTELLIGENCE_ENDPOINT
DOCUMENT_INTELLIGENCE_KEY
AZURE_OPENAI_ENDPOINT
AZURE_OPENAI_KEY
STORAGE_CONNECTION_STRING
STORAGE_ACCOUNT_NAME
```

**Next step:** In Lab 5, you'll create the **Logic App workflow** that ties everything together.

---

## Security & Post-Lab Hardening

This lab sets up a basic, unsecured environment for learning. For production use, implement these hardening steps **after** you complete the core labs (Labs 0-11):

1. **Rotate connection strings regularly** — Every 90 days, regenerate keys in Azure Portal
2. **Use Managed Identity** — Logic App should authenticate via system-assigned identity, not connection strings
3. **Enable Azure Storage encryption** — Enable encryption at rest (default in most regions)
4. **Add blob-level access policies** — Restrict access by IP, time, or scope
5. **Enable Azure Monitor & Log Analytics** — Track all storage access and modifications
6. **Audit and compliance** — Enable Azure Policy to enforce encryption and access controls

See [Azure Storage security best practices](https://learn.microsoft.com/en-us/azure/storage/common/storage-security-guide) for more.

---

## Next Steps

You're now ready for **Lab 5: Create the Logic App**!

In Lab 5, you'll create a Logic App workflow that:
- Watches the `audit-input` container for new images
- Calls Document Intelligence to extract text and structure
- Sends extracted data to Azure OpenAI for analysis
- Writes results to the `audit-output` container

[← Previous: Deploy Azure AI Services](lab-03-azure-ai.md)

[Next: Create the Logic App →](lab-05-logic-app.md)

---

*Lab 4 created by Bond. Last updated: March 2026.*
