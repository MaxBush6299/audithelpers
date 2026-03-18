---
layout: default
title: Lab 0: Environment Setup
parent: Labs
nav_order: 1
---
# Lab 0: Environment Setup

**Estimated duration:** 30 minutes  
**Owner:** Moneypenny  
**Objective:** Prepare your Azure environment, configure secrets, and understand RBAC requirements for the AI Calibration pipeline.

---

## What You'll Learn

In this lab, you will:

- ✅ Create an Azure Resource Group with a naming convention
- ✅ Set up a `.env` file locally with placeholders for service endpoints and keys
- ✅ Understand Azure RBAC roles required for each service
- ✅ Learn security best practices for managing secrets
- ✅ Get ready for Labs 2-4 (Azure service deployments)

> **📝 Note:** This lab does NOT deploy Azure services. You'll create the Resource Group and configure your local environment. The actual service deployments happen in Labs 2-4.

---

## Prerequisites

Before starting this lab, ensure you have:

- ✅ **Azure subscription** with **Contributor** or **Owner** access at the subscription or Resource Group level
- ✅ **Permissions to create:**
  - Resource Groups
  - Storage Accounts
  - Azure AI Services (Document Intelligence, Azure OpenAI)
- ✅ **Quota check:** Request quota for **GPT-4o** or **GPT-4 Turbo** deployments (vision capability required). See [Request quota increase in Azure AI Services](https://learn.microsoft.com/en-us/azure/ai-services/quota-and-limits)
- ✅ **Audit evidence files** — A folder of images (PPTX slides, screenshots, forms, or photos) that you'll use to test the pipeline. You bring your own data; no sample files are provided.
- ✅ **Text editor or IDE** — VS Code, Notepad, or equivalent (to create and edit `.env` file)
- ✅ **Git installed** (to clone the repository in later labs)

---

## Step 1: Create an Azure Resource Group

A Resource Group is a logical container for all Azure resources in this project. Keeping them together makes management and cleanup easier.

### 1.1 Navigate to the Azure Portal

1. Go to [Azure Portal](https://portal.azure.com)
2. Sign in with your Azure account

### 1.2 Create a New Resource Group

1. In the search bar at the top, type **resource groups** and select **Resource Groups**
2. Click **+ Create**
3. Fill in the details:
   - **Subscription:** Select your Azure subscription
   - **Resource group name:** Use this naming convention: `rg-audit-pipeline-{your-initials}`
     - *Example:* If your name is Jane Smith, use `rg-audit-pipeline-js`
     - *Reason:* Naming conventions help organize resources when multiple team members share a subscription
   - **Region:** Choose a region close to you or your organization. Recommended: **East US 2** or **West US 2** (good quota availability for AI services)
4. Click **Review + create**
5. Review the details and click **Create**

Wait for the deployment to complete (~10 seconds). You'll see a **Deployment succeeded** message.

> **💡 Tip:** Copy the Resource Group name to a text file. You'll reference it in every later lab.

---

## Step 2: Understand RBAC Roles for This Project

Azure uses **Role-Based Access Control (RBAC)** to manage who can do what with Azure resources. For this project, you need specific roles for each Azure service. If your subscription has restrictions, share these roles with your Azure administrator.

### 2.1 Required RBAC Roles

Below is a summary of RBAC roles required for each Azure service in this pipeline:

| Azure Service | Required Roles | Why |
|---|---|---|
| **Resource Group** | Contributor, Owner | Create and manage resources within the group |
| **Storage Account** | Storage Account Contributor, Storage Blob Data Contributor | Upload/download files, manage blob containers |
| **Document Intelligence** | Cognitive Services Contributor, Cognitive Services User | Deploy the service and call it from Logic App |
| **Azure AI Services (Azure OpenAI)** | Cognitive Services Contributor, Cognitive Services User | Deploy GPT-4 model and call it from Logic App |
| **Logic Apps** | Logic App Contributor | Create and manage workflows |

> **📝 Note:** If your organization uses custom RBAC roles or has stricter policies, work with your Azure administrator to map these requirements to your environment.

### 2.2 Principle of Least Privilege

Only grant the minimum permissions needed:

- ✅ **DO:** Grant Contributor access to the Resource Group for the duration of the project
- ✅ **DO:** Use managed identities in Logic App (Labs 5-10 show how)
- ❌ **DON'T:** Use subscription-level Owner access if Resource Group Contributor is sufficient
- ❌ **DON'T:** Share credentials or keys directly; use Azure Key Vault (post-lab hardening)

For production deployments, consider assigning users to specific roles per service rather than Contributor.

---

## Step 3: Create and Configure Your .env File

The `.env` file stores configuration values like Azure service endpoints and API keys. Later labs will reference this file to connect to your Azure services.

### 3.1 Create a `.env` File Locally

1. Open your text editor or IDE
2. Create a new file named `.env` (no extension prefix, just `.env`)
3. Save it in your project root directory (e.g., `C:\Users\{YourName}\ai-calibration\.env` on Windows)

### 3.2 Add Configuration Template

Copy and paste the following template into your `.env` file. You'll fill in the actual values as you complete Labs 2-4:

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

# Storage Account (Lab 4)
STORAGE_ACCOUNT_NAME=youraccountname
STORAGE_ACCOUNT_KEY=your-storage-account-key-here
STORAGE_CONTAINER_INPUT=input-evidence
STORAGE_CONTAINER_OUTPUT=output-results

# Logic App (Lab 5+)
LOGIC_APP_NAME=logic-app-audit-pipeline
LOGIC_APP_RESOURCE_GROUP=rg-audit-pipeline-{your-initials}
```

### 3.3 Understand Each Variable

| Variable | Purpose | Example |
|---|---|---|
| `AZURE_SUBSCRIPTION_ID` | Your Azure subscription GUID | `12345678-1234-1234-1234-123456789abc` |
| `AZURE_RESOURCE_GROUP` | Resource Group name from Step 1 | `rg-audit-pipeline-js` |
| `AZURE_LOCATION` | Azure region for resources | `eastus2` or `westus2` |
| `DOCUMENT_INTELLIGENCE_ENDPOINT` | HTTP endpoint for Document Intelligence | `https://eastus2.api.cognitive.microsoft.com/` |
| `DOCUMENT_INTELLIGENCE_KEY` | API key for Document Intelligence | 32-character alphanumeric key |
| `AZURE_OPENAI_ENDPOINT` | HTTP endpoint for Azure OpenAI | `https://my-deployment.openai.azure.com/` |
| `AZURE_OPENAI_KEY` | API key for Azure OpenAI | 32-character alphanumeric key |
| `STORAGE_ACCOUNT_NAME` | Name of your blob storage account | `myauditpipelineacct` |
| `STORAGE_ACCOUNT_KEY` | Primary or secondary key for storage | 88-character key (base64-encoded) |

---

## Step 4: Secure Your .env File

Your `.env` file contains API keys and secrets. Treat it with care.

### 4.1 Never Commit .env to Git

1. Ensure your `.gitignore` file includes `.env`:
   - If you already have a `.gitignore`, add this line: `*.env`
   - If you don't have one, create a file named `.gitignore` in your project root with:
     ```
     # Environment variables
     *.env
     .env
     .env.local
     ```

2. Verify the file is ignored before committing:
   ```bash
   git status
   # The .env file should NOT appear in the list of "Changes to be committed"
   ```

> **⚠️ Warning:** If you accidentally commit a `.env` file with real keys, immediately rotate those keys in the Azure Portal. A committed secret is a compromised secret.

### 4.2 Never Share Your API Keys

- ❌ DON'T post keys in Slack, email, or GitHub issues
- ❌ DON'T commit keys to any branch (even private ones)
- ❌ DON'T share `.env` files with teammates
- ✅ DO use Azure Key Vault for shared team environments (see "Next Steps" below)

### 4.3 Understand Your Local .env

The `.env` file stays on your machine. Each team member has their own:

```
Your Machine:
  - ai-calibration/
    - .env (YOUR keys, never committed)
    - .gitignore (includes .env)
    - src/ (code files)
```

This way, your API keys never leave your machine or get checked into version control.

---

## Step 5: Verify Your Setup

Use this checklist to confirm your environment is ready for Labs 2-4:

- ✅ **Resource Group created:** `rg-audit-pipeline-{your-initials}` exists in Azure Portal
- ✅ **`.env` file created:** Located in your project root with template values
- ✅ **`.gitignore` configured:** `.env` file will not be committed
- ✅ **Audit evidence ready:** You have a folder of test images ready to upload in Lab 11
- ✅ **RBAC understood:** You know what roles you need and have them (or know who to ask)
- ✅ **Azure subscription check:** You can create Cognitive Services resources (Document Intelligence, Azure OpenAI)

If any of these are missing, go back to the relevant step before proceeding to Lab 1.

---

## Troubleshooting

### Q: I don't have permission to create a Resource Group

**A:** Contact your Azure administrator and share the prerequisites section. You may need Contributor role at the subscription level, or your admin can create the Resource Group for you and assign you Contributor access to it.

### Q: What if I forget my `.env` file location?

**A:** The `.env` file should be in your **project root directory** (the same folder where `run_pipeline.py`, `README.md`, and other main files live). Store its path in a text file or your IDE for reference.

### Q: Can I use `env` instead of `.env`?

**A:** No. The leading dot (`.env`) is required. Most Azure SDKs and Python packages specifically look for `.env` (with the dot). Using `env` without the dot won't work.

### Q: What's the difference between `.env` and `.env.local`?

**A:** Both are ignored by `.gitignore`. Use `.env` for this lab. `.env.local` is sometimes used for local-only overrides and is a convention choice.

### Q: My Resource Group name doesn't match the naming convention. Can I rename it?

**A:** Renaming a Resource Group is not possible. If you need to start over:
1. Delete the Resource Group from Azure Portal (this deletes all resources in it)
2. Create a new one with the correct naming convention
3. Update your `.env` file with the new name

### Q: I got an error: "User does not have permission to perform action 'Microsoft.Resources/resourceGroups/write'"

**A:** You don't have Contributor access to the subscription. Contact your Azure administrator and request Contributor access to the subscription (or to a specific Resource Group if that's your organization's policy).

---

## Security & Post-Lab Hardening

This lab sets up a basic, unsecured environment for learning. For production use, implement these hardening steps **after** you complete the core labs (Labs 0-11):

1. **Rotate API keys regularly** — Every 90 days, regenerate keys in Azure Portal
2. **Use Azure Key Vault** — Store production secrets in Key Vault instead of `.env`
3. **Enable managed identities** — Logic App should authenticate to Azure services via managed identity, not keys
4. **Add authentication to Logic App** — Require OAuth or API key for external callers
5. **Enable Azure Monitor & Log Analytics** — Track all API calls and failures
6. **Audit and compliance** — Enable Azure Policy to enforce tagging, encryption, and access controls

See [Azure Well-Architected Framework - Security](https://learn.microsoft.com/en-us/azure/architecture/framework/security/) for more.

---

## Key Concepts

### Resource Groups

A **Resource Group** is a logical container that holds all Azure resources for a project. It simplifies:
- **Organization:** All audit pipeline resources live together
- **Billing:** One Resource Group = one cost center
- **Cleanup:** Delete the group = delete all resources instantly

### RBAC (Role-Based Access Control)

**RBAC** determines **who** can do **what** on Azure resources:
- **Who:** Azure users, groups, or service principals (managed identities)
- **What:** Specific actions like "create storage account" or "read keys"
- **Where:** Scoped to a subscription, Resource Group, or individual resource

For this project, **Contributor** role at the Resource Group level is the minimum needed.

### Environment Variables (.env)

The `.env` file is a local, untracked file that stores configuration values:
- **Never committed** to Git
- **Not shared** with teammates
- **Used by code** at runtime to read endpoints and keys
- **Python:** `dotenv` library loads `.env` automatically in Labs 5+

---

## Next Steps

You're now ready for **Lab 1**! In Lab 1, you'll review the architecture of the audit pipeline and understand how the 5 stages work together.

Before Lab 1, optionally:
- Review [Azure Storage documentation](https://learn.microsoft.com/en-us/azure/storage/) if you're unfamiliar with blob storage
- Review [Azure RBAC documentation](https://learn.microsoft.com/en-us/azure/role-based-access-control/) for deeper concepts

When you're ready to proceed:

[Next: Understanding the Architecture →](lab-01-architecture.md)

---

*Lab 0 created by Moneypenny. Last updated: March 2026.*
