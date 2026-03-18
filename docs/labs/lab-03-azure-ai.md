# Lab 3: Deploy Azure OpenAI

**Estimated duration:** 25 minutes  
**Owner:** Bond  
**Objective:** Deploy an Azure OpenAI resource with a vision-capable model (GPT-4o or GPT-4 Turbo), configure the deployment, and retrieve the endpoint and API key.

---

## What You'll Learn

In this lab, you will:

- ✅ Understand what Azure OpenAI provides (enterprise GPT models with compliance and isolation)
- ✅ Understand why vision capability matters for your audit pipeline
- ✅ Deploy an Azure OpenAI resource in your Resource Group
- ✅ Deploy a **GPT-4o** or **GPT-4 Turbo** model (both have vision capability)
- ✅ Retrieve your endpoint, deployment name, and API key
- ✅ Add configuration to your `.env` file

> **📝 Note:** This lab assumes you completed **Lab 0** (Environment Setup). You'll use the Resource Group and `.env` file created there.

---

## Prerequisites

Before starting this lab, ensure you have:

- ✅ **Lab 0 completed:** Resource Group (`rg-audit-pipeline-{your-initials}`) created in Azure Portal
- ✅ **`.env` file created** in your project root
- ✅ **Azure subscription with sufficient quota** for GPT-4o or GPT-4 Turbo deployments
  - Vision models may require quota approval in some regions
  - See [Azure OpenAI quota and limits](https://learn.microsoft.com/en-us/azure/ai-services/openai/quotas-limits) for your region
- ✅ **Contributor or Owner** access to your Resource Group
- ✅ **Supported region** — Not all Azure regions offer Azure OpenAI. Check [Azure OpenAI regional availability](https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/models#model-summary-table-and-region-availability-updated-august-2024)

---

## What is Azure OpenAI?

**Azure OpenAI** provides enterprise access to OpenAI's GPT models (like GPT-4 and GPT-3.5-Turbo) hosted on Microsoft's infrastructure. Unlike the public OpenAI API, Azure OpenAI offers:

- ✅ **Network isolation** — Your data stays within Azure
- ✅ **Compliance** — Meets regulatory requirements (HIPAA, FedRAMP, SOC 2)
- ✅ **RBAC integration** — Control access with Azure identities
- ✅ **Regional availability** — Deploy models in regions close to your users

For this audit pipeline, you need a **vision-capable model** because your workflow will:

1. Upload image evidence (screenshots, PPTX slides, forms, photos)
2. Send images directly to Azure OpenAI
3. Have GPT-4o or GPT-4 Turbo **analyze the image** and respond to audit questions
4. Get a confidence score and explanation back

**Why GPT-4o or GPT-4 Turbo?** Both are **multimodal** — they can understand text *and* images. GPT-4o is faster and cheaper; GPT-4 Turbo is more capable for complex reasoning. Either works for this lab.

---

## Step 1: Navigate to Azure OpenAI in the Azure Portal

### 1.1 Open Azure Portal

1. Go to [Azure Portal](https://portal.azure.com)
2. Sign in with your Azure account

### 1.2 Create a New Resource

1. Click **+ Create a resource** (top-left button or use search bar)
2. In the search box at the top, type **Azure OpenAI** and press Enter
3. Select **Azure OpenAI** from the results (published by Microsoft)
4. Click **Create**

---

## Step 2: Fill in Deployment Details

You're now on the **Create Azure OpenAI** page. Fill in each field:

### 2.1 Basics Tab

1. **Subscription:** Select your Azure subscription
2. **Resource Group:** Select `rg-audit-pipeline-{your-initials}` (created in Lab 0)
3. **Region:** 
   - Check [Azure OpenAI regional availability](https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/models#model-summary-table-and-region-availability-updated-august-2024)
   - Recommended regions with good quota availability: **East US 2**, **West US 2**, **West Europe**
   - ⚠️ **Quota Warning:** Vision models (GPT-4o, GPT-4 Turbo) may not be available in all regions. If you don't see quota for your preferred region, try another region or [request a quota increase](https://learn.microsoft.com/en-us/azure/ai-services/quotas-and-limits)
4. **Name:** Use the naming convention: `aoai-audit-{your-initials}`
   - *Example:* If your initials are MB, use `aoai-audit-mb`
   - *Reason:* This clearly identifies the resource as an Azure OpenAI instance for the audit pipeline
5. **Pricing tier:** Select **Standard S0** (provides sufficient throughput for this lab)

### 2.2 Network Tab (Optional)

- For this lab, use **All networks** (default)
- In production, restrict to **Selected networks** and use private endpoints

### 2.3 Tags Tab (Optional)

Add tags to organize your resources:

- **project:** `audit-pipeline`
- **owner:** `{your-initials}`
- **environment:** `lab`

---

## Step 3: Review and Create

1. Click **Review + create** at the bottom
2. Review the details:
   - Verify the Resource Group is correct
   - Verify the Region is in the supported list
   - Verify the Name follows the naming convention
3. Click **Create**

Azure will now deploy the Azure OpenAI resource. This takes **2-5 minutes**. You'll see a progress bar and notifications in the top-right.

> **💡 Tip:** While waiting, read the next section to understand model deployments. You won't deploy a model until your resource is ready.

---

## Step 4: Deploy a Model

Once your Azure OpenAI resource is deployed, you need to deploy a specific model within it. Think of the resource as a "container" and the model deployment as the "engine" inside it.

### 4.1 Navigate to Your Azure OpenAI Resource

1. When deployment completes, click **Go to resource** (or search for your resource name in the portal)
2. You're now on your Azure OpenAI resource page

### 4.2 Open Azure OpenAI Studio

1. On the resource page, look for the **Overview** tab (top-left)
2. Scroll down and find the **Essentials** section
3. Click **Go to Azure OpenAI Studio** (or the link labeled "Explore in Azure OpenAI Studio")

You're now in **Azure OpenAI Studio** — a dedicated interface for managing models and deployments.

### 4.3 Create a New Deployment

1. On the left sidebar, click **Deployments**
2. Click **+ Create new deployment** or **+ Deploy model**
3. A dialog will appear asking which model to deploy

### 4.4 Select the Model

You have two options. Choose **one**:

#### Option A: GPT-4o (Recommended)
- **Advantages:** Faster, lower cost, good vision capability
- **Model name:** `gpt-4o`
- **Version:** Latest available (typically `2024-08-06` or later)

#### Option B: GPT-4 Turbo
- **Advantages:** Slightly more capable for complex reasoning
- **Model name:** `gpt-4-turbo`
- **Version:** Latest available (typically `2024-04-09` or later)

**For this lab, we recommend Option A (GPT-4o)** because it's faster and cheaper, and it has excellent vision capability.

Select your choice and proceed.

> **⚠️ Note:** If you don't see GPT-4o or GPT-4 Turbo in the dropdown, you may need to [request quota](https://learn.microsoft.com/en-us/azure/ai-services/quotas-and-limits) in your region. Vision models sometimes require explicit quota approval.

### 4.5 Configure the Deployment

1. **Deployment name:** Use this naming convention: `gpt-4o-audit` (or `gpt-4-turbo-audit` if you chose Option B)
   - *Example:* `gpt-4o-audit`
2. **Model version:** Accept the default (latest version)
3. **Deployment capacity units (TPM):** Keep the default value for this lab (e.g., `10K`)
   - TPM = "Tokens Per Minute" — a measure of how much text the model can process
   - Default is sufficient for a lab environment
4. Click **Create**

Azure will now deploy the model. This takes **1-2 minutes**. Once complete, your model is ready to use.

---

## Step 5: Get Your Endpoint and Key

Now you need to retrieve your Azure OpenAI **endpoint** and **API key** to configure your `.env` file.

### 5.1 Get the Endpoint and Deployment Name

1. In Azure OpenAI Studio, click **Deployments** (left sidebar)
2. You should see your deployment listed (e.g., `gpt-4o-audit`)
3. Next to your deployment name, click the **three dots** (**⋯**) or click the deployment name itself
4. Look for a button that says **"Copy endpoint"** or **"View API calls"** — copy the endpoint URL
   - **Endpoint format:** `https://{resource-name}.openai.azure.com/`
   - *Example:* `https://aoai-audit-mb.openai.azure.com/`
5. **Deployment name** is what you set in Step 4.5 (e.g., `gpt-4o-audit`)

> **💡 Tip:** You can also find the endpoint on your Azure OpenAI resource page in the Azure Portal under **Keys and Endpoint**.

### 5.2 Get Your API Key

1. In Azure OpenAI Studio, click **API keys** (left sidebar, or look in the top navigation)
2. You'll see **Key 1** and **Key 2** — copy **Key 1** (a 32-character alphanumeric string)
3. ⚠️ **Treat this key like a password** — never share it, never commit it to Git

> **Alternative:** You can also get the key from Azure Portal:
> 1. Navigate to your Azure OpenAI resource
> 2. Click **Keys and Endpoint** (left sidebar under **Resource Management**)
> 3. Copy **Key 1**

---

## Step 6: Update Your .env File

Now add your Azure OpenAI configuration to your `.env` file.

### 6.1 Open Your .env File

1. Open your `.env` file in a text editor or IDE (created in Lab 0)
2. Find the section labeled `# Azure AI Services / Azure OpenAI (Lab 3)`

### 6.2 Fill in the Values

Replace the placeholders with your actual values:

```bash
# Azure AI Services / Azure OpenAI (Lab 3)
AZURE_OPENAI_ENDPOINT=https://aoai-audit-mb.openai.azure.com/
AZURE_OPENAI_KEY=your-32-character-api-key-here
AZURE_OPENAI_DEPLOYMENT=gpt-4o-audit
```

**What each value means:**

| Variable | Value | Example |
|---|---|---|
| `AZURE_OPENAI_ENDPOINT` | The base URL for your Azure OpenAI resource | `https://aoai-audit-mb.openai.azure.com/` |
| `AZURE_OPENAI_KEY` | Your API key (keep this secret!) | `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6` |
| `AZURE_OPENAI_DEPLOYMENT` | The deployment name you created | `gpt-4o-audit` |

### 6.3 Save the File

- Save your `.env` file
- ✅ Verify the file is still in `.gitignore` (should be, from Lab 0)
- ✅ Never commit this file to Git

---

## Step 7: Verify Your Deployment (Optional)

You can quickly test your deployment without writing code by using Azure OpenAI Studio's chat interface:

1. In Azure OpenAI Studio, click **Chat** (left sidebar)
2. Select your deployment (`gpt-4o-audit` or similar) from the dropdown
3. Type a test message: `"Hello, can you see this?"` or `"What is 2+2?"`
4. You should get a response back

This confirms your endpoint and key are working correctly.

---

## Key Concepts

### Azure OpenAI vs. Public OpenAI API

| Feature | Azure OpenAI | Public API |
|---|---|---|
| **Compliance** | HIPAA, FedRAMP, SOC 2 | Limited |
| **Isolation** | Network isolation, no data sharing | Shared infrastructure |
| **RBAC** | Azure identities | API keys only |
| **Regions** | Multiple Azure regions | Single endpoint |
| **Cost model** | Subscription-based or pay-as-you-go | Token-based |

For enterprise audit pipelines, Azure OpenAI is the right choice.

### Multimodal Models

**Multimodal** means the model can process multiple types of input:

- **GPT-4o / GPT-4 Turbo:** Can read text *and* images
  - You send: `"Analyze this screenshot and tell me if it complies with SOX 404 requirements"` + image
  - Model responds: `"This screenshot shows a login form. Recommendation: ..."`
  - Use case: Your audit pipeline sends evidence images and gets analysis back

- **GPT-3.5-Turbo:** Text-only
  - Can't see images
  - Cheaper, but not suitable for visual evidence analysis

For this project, you *need* a vision-capable model (GPT-4o or GPT-4 Turbo).

### Deployments

A **deployment** is an instance of a model within your Azure OpenAI resource. One resource can have multiple deployments:

```
Azure OpenAI Resource (aoai-audit-mb)
├── Deployment 1: gpt-4o-audit (GPT-4o model)
└── Deployment 2: gpt-4-turbo-audit (GPT-4 Turbo model)
```

In this lab, you deployed one model. In production, you might have separate deployments for testing vs. production, or different models for different tasks.

---

## Troubleshooting

### Q: I don't see Azure OpenAI in the "Create a resource" search

**A:** 
1. Verify your subscription has access to Azure OpenAI (some subscriptions are restricted)
2. Check that you're in a supported region
3. Try searching for **"Cognitive Services"** instead — Azure OpenAI is under that umbrella

### Q: I don't see GPT-4o or GPT-4 Turbo in the model dropdown

**A:** 
1. Those models may not be available in your region
2. You may need to [request quota](https://learn.microsoft.com/en-us/azure/ai-services/quotas-and-limits)
3. Try a different region (East US 2 or West Europe usually have good availability)
4. As a temporary workaround, you can use **GPT-3.5-Turbo** (text-only) to test your pipeline, then upgrade to a vision model later

### Q: I got a "Resource creation failed" error

**A:**
1. Check that your Resource Group exists (you created it in Lab 0)
2. Verify you have Contributor access to the Resource Group
3. Check that the resource name is unique in Azure (Azure OpenAI names must be globally unique)
4. Try a different region if your first choice is unavailable

### Q: I can't see the "Go to Azure OpenAI Studio" link

**A:**
1. Make sure your deployment is finished (check notifications in top-right corner)
2. Refresh the page
3. Manually navigate: Go to your resource page → click **Resource Management** → **Keys and Endpoint** → scroll to see the Studio link
4. Or, directly visit the Studio: `https://{resource-name}.openai.azure.com/` (replace with your resource name)

### Q: My API key isn't working

**A:**
1. Verify you copied the full key (32 characters)
2. Make sure you're using **Key 1** (not Key 2)
3. Check that your `.env` file path is correct and the app is reading it
4. Verify your endpoint URL ends with a slash: `https://aoai-audit-mb.openai.azure.com/`

### Q: I need to regenerate my API key

**A:**
1. Go to your Azure OpenAI resource in the Azure Portal
2. Click **Keys and Endpoint** (left sidebar)
3. Click **Regenerate Key 1** or **Regenerate Key 2**
4. Update your `.env` file with the new key
5. Old keys will stop working after regeneration

---

## Security & Best Practices

### For Development (This Lab)

- ✅ Store keys in `.env` file (local, not committed)
- ✅ Use `.gitignore` to prevent accidental commits
- ✅ Keep `.env` on your machine only — never share it

### For Production (After Labs Complete)

- ✅ Use **Azure Key Vault** instead of `.env`
- ✅ Use **managed identities** in your Logic App to authenticate
- ✅ Enable **API rate limiting** and **request throttling** in Azure OpenAI
- ✅ Enable **logging and monitoring** with Azure Monitor
- ✅ Rotate keys every **90 days**
- ✅ Restrict model deployments by **role** (e.g., only Contributor can view keys)

See [Azure OpenAI security best practices](https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/safety-best-practices) for more.

---

## Next Steps

You've successfully deployed Azure OpenAI and configured your `.env` file. Next:

1. **Lab 4:** Deploy a Storage Account to hold your audit evidence files
2. **Lab 5+:** Create a Logic App workflow that chains together Document Intelligence → Azure OpenAI → storage for results

Before proceeding to Lab 4:

- Verify your `.env` file has all three values: `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_KEY`, `AZURE_OPENAI_DEPLOYMENT`
- ✅ Optionally test your deployment using the Chat interface in Azure OpenAI Studio

Ready? Let's go.

---

[← Previous: Lab 2: Deploy Document Intelligence](lab-02-doc-intelligence.md) | [Next: Lab 4: Deploy Storage Account →](lab-04-storage.md)

---

*Lab 3 created by Bond. Last updated: March 2026.*
