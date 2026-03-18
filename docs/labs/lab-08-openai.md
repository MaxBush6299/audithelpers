---
layout: default
title: Lab 8: OpenAI Vision
parent: Labs
nav_order: 9
---
# Lab 8: Add Azure OpenAI Vision

**Estimated duration:** 25 minutes  
**Owner:** Bond  
**Objective:** Add an Azure OpenAI Vision action to your Logic App to perform multimodal analysis—combining extracted text and image data to get AI-driven insights about audit evidence.

---

## What You'll Learn

In this lab, you will:

- ✅ Understand how Azure OpenAI Vision (GPT-4o/4-Turbo) performs multimodal analysis
- ✅ Send a base64-encoded image + text prompt to the Azure OpenAI Chat Completions API
- ✅ Build the multimodal message structure with system prompts and image URLs
- ✅ Configure HTTP headers and authentication for Azure OpenAI
- ✅ Parse the AI response to extract analysis results
- ✅ Store the AI analysis in a Logic App variable for downstream validation
- ✅ Test your workflow end-to-end: image → text extraction → AI analysis → output

> **📝 Note:** This lab builds on Lab 7. Your Logic App already has Document Intelligence integration and extracts text from images. In this lab, you'll add Azure OpenAI Vision to analyze *both* the image and extracted text together, producing AI-driven audit insights.

---

## Prerequisites

Before starting this lab, ensure you have:

- ✅ **Lab 7 complete:** Document Intelligence integration working with ExtractedText variable populated
- ✅ **Azure OpenAI deployment:** A GPT-4o or GPT-4-Turbo model deployed in Azure OpenAI (from Lab 3)
- ✅ **Azure OpenAI endpoint and key:** Stored in `.env` file
- ✅ **Logic App workflow open:** In Azure Portal, ready to edit
- ✅ **Sample image:** Same test file from Lab 7 for end-to-end verification

---

## What Is Azure OpenAI Vision?

**Azure OpenAI** is Microsoft's enterprise-grade API for OpenAI models. The **vision capability** (GPT-4o/4-Turbo with vision) allows you to send images directly to the model alongside text prompts.

**Why multimodal analysis?**
- **Combined context:** Image + extracted text + business context in a single request
- **Audit-ready:** Ask the AI to validate evidence, check compliance, extract specific details
- **Confidence scores:** Get structured responses (e.g., JSON) with evidence ratings
- **Flexible prompts:** Customize instructions for different audit points

**How it works in your workflow:**
1. Document Intelligence extracts text from the image (Lab 7 output)
2. Logic App converts the blob content to base64
3. HTTP action sends the image + extracted text to Azure OpenAI Chat Completions API
4. GPT-4o/4-Turbo analyzes both, following your system prompt
5. Logic App parses the response and stores the AI analysis in a variable
6. Later labs use this analysis for validation and scoring

---

## Architecture: Where Azure OpenAI Fits

```
Blob Upload
    ↓
[Blob Trigger]
    ↓
[Get blob content]
    ↓
[Document Intelligence] → ExtractedText variable
    ↓
[Azure OpenAI Vision] ← YOU ARE HERE (Lab 8)
    ↓
[Parse response] → AIAnalysis variable
    ↓
[Validation Logic] (Lab 9)
    ↓
[JSON Output] (Lab 10)
```

---

## Step 1: Prepare Your Environment Variables

Before configuring the HTTP action in Logic App, verify your Azure OpenAI credentials are stored securely.

### 1.1 Check Your `.env` File

From Lab 3, you should have:

```
AZURE_OPENAI_ENDPOINT=https://[your-resource].openai.azure.com/
AZURE_OPENAI_KEY=<your-api-key>
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o  # or gpt-4-turbo
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

**Where to find these:**
1. Go to **Azure Portal** → **Azure OpenAI** resource
2. Click **Keys and Endpoint** (under "Resource Management")
3. Copy **Key 1** and **Endpoint**
4. Verify your deployment name by clicking **Model deployments** → see your GPT-4o/4-Turbo deployment

> ⚠️ **Security reminder:** In this lab, you'll paste your key into a Logic App action. For production, use Key Vault + Managed Identity (see post-lab hardening section).

---

## Step 2: Understand the Azure OpenAI Chat Completions API

### 2.1 The Request Format

You'll make an HTTP POST request to Azure OpenAI with the following structure:

```
POST https://[your-resource].openai.azure.com/openai/deployments/[deployment-name]/chat/completions?api-version=2024-02-15-preview

Headers:
  api-key: {your-key}
  Content-Type: application/json

Body: (JSON with multimodal messages)
```

### 2.2 The Multimodal Message Structure

Azure OpenAI messages can include both text and images. Here's what you'll send:

```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are an expert audit evidence evaluator. Analyze the provided image and text, then respond with a structured assessment of whether the evidence supports the audit requirement. Be concise and focus on compliance indicators."
    },
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Audit Point: Is there evidence of a signed approval form?\n\nExtracted Text from Image:\n{extracted_text}\n\nBased on the image AND the extracted text above, does this evidence support the audit requirement? Respond with: PASS/FAIL and a brief explanation."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "data:image/jpeg;base64,{base64_encoded_image_here}"
          }
        }
      ]
    }
  ],
  "max_tokens": 500,
  "temperature": 0.5
}
```

**Key points:**
- **System message:** Sets the context and tone for the AI
- **User message:** An array containing both text and image
- **Text content:** Your prompt + audit context + extracted text from Lab 7
- **Image content:** Base64-encoded image with data URL prefix (`data:image/jpeg;base64,...`)
- **max_tokens:** Controls response length (500 is good for brief analysis)
- **temperature:** 0.5 = balanced between deterministic and creative

---

## Step 3: Add the Azure OpenAI HTTP Action in Logic App Designer

### 3.1 Open Your Logic App in Edit Mode

1. Go to **Azure Portal**
2. Search for and open your **Logic App** resource
3. Click **Logic App Designer** (or **Edit** if you see it)
4. Locate the **Document Intelligence** section in your workflow

Your workflow should look like:
```
[Blob trigger] → [Get blob content] → [Document Intelligence POST] → [Delay] → [Document Intelligence GET] → [Parse JSON] → [Set ExtractedText variable]
```

### 3.2 Add a New HTTP Action After ExtractedText Variable

1. Click the **+** button below the **Set ExtractedText variable** action
2. Search for **HTTP** and select the **HTTP** action (not "HTTP Webhook")
3. This is where you'll configure the Azure OpenAI call

### 3.3 Configure the HTTP Action

In the HTTP action, set the following fields:

**Method:**
```
POST
```

**URI:**
```
https://{your-openai-resource}.openai.azure.com/openai/deployments/{deployment-name}/chat/completions?api-version=2024-02-15-preview
```

Replace:
- `{your-openai-resource}` — from your `.env` (e.g., `my-org-openai`)
- `{deployment-name}` — your model deployment (e.g., `gpt-4o`)

**Headers:**

Click **Add new parameter** → **Headers** and add these two:

| Key | Value |
|-----|-------|
| `api-key` | `{your-openai-key}` |
| `Content-Type` | `application/json` |

Replace `{your-openai-key}` with your actual Azure OpenAI key from `.env`.

### 3.4 Build the Request Body

This is the critical part. Click **Add new parameter** → **Body**.

In the Body field, you'll construct the multimodal JSON. Logic App requires you to build this as an **expression** or **static JSON**. 

Here's the recommended approach: **Use the Expression tab** to dynamically construct the body.

Click the **Body** field and switch to the **Expression** tab. Paste this code:

```
json(concat('{
  "messages": [
    {
      "role": "system",
      "content": "You are an expert audit evidence evaluator. Analyze the provided image and extracted text to assess whether the evidence supports the specified audit requirement. Respond concisely with a PASS or FAIL determination and a brief justification."
    },
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Audit Point: Verify compliance with evidence review standards.\n\nExtracted Text from Image:\n', variables('ExtractedText'), '\n\nAnalyze the above image and text. Does the evidence demonstrate compliance? Respond with: PASS/FAIL and a 1–2 sentence explanation."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "data:image/jpeg;base64,', base64(body(''Get_blob_content'')), '"
          }
        }
      ]
    }
  ],
  "max_tokens": 500,
  "temperature": 0.5
}'
))
```

> **📝 Note on base64 encoding:** The expression `base64(body('Get_blob_content'))` automatically encodes the blob content. If you're using a different action name (e.g., "Read blob content"), replace `Get_blob_content` accordingly.

**Alternative: If using the Body field directly (non-expression mode):**

Use the static JSON below and replace placeholders:

```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are an expert audit evidence evaluator. Analyze the provided image and extracted text to assess whether the evidence supports the specified audit requirement. Respond concisely with a PASS or FAIL determination and a brief justification."
    },
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Audit Point: Verify compliance with evidence review standards.\n\nExtracted Text from Image:\n[Your ExtractedText variable here]\n\nAnalyze the above image and text. Does the evidence demonstrate compliance? Respond with: PASS/FAIL and a 1–2 sentence explanation."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "data:image/jpeg;base64,[base64-encoded-image-here]"
          }
        }
      ]
    }
  ],
  "max_tokens": 500,
  "temperature": 0.5
}
```

---

## Step 4: Parse the Azure OpenAI Response

### 4.1 Add a Parse JSON Action

After the HTTP call, add a **Parse JSON** action:

1. Click **+** below the HTTP action
2. Search for **Parse JSON**
3. In the **Content** field, select the **Body** output from the HTTP action (from dynamic content)

### 4.2 Define the Schema

The Azure OpenAI response has this structure:

```json
{
  "id": "chatcmpl-...",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "gpt-4o",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "PASS: The document shows a signed approval form with current date and authorized signature."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 150,
    "completion_tokens": 30,
    "total_tokens": 180
  }
}
```

Paste this schema in the **Schema** field:

```json
{
  "type": "object",
  "properties": {
    "id": {
      "type": "string"
    },
    "object": {
      "type": "string"
    },
    "created": {
      "type": "integer"
    },
    "model": {
      "type": "string"
    },
    "choices": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "index": {
            "type": "integer"
          },
          "message": {
            "type": "object",
            "properties": {
              "role": {
                "type": "string"
              },
              "content": {
                "type": "string"
              }
            }
          },
          "finish_reason": {
            "type": "string"
          }
        }
      }
    },
    "usage": {
      "type": "object",
      "properties": {
        "prompt_tokens": {
          "type": "integer"
        },
        "completion_tokens": {
          "type": "integer"
        },
        "total_tokens": {
          "type": "integer"
        }
      }
    }
  }
}
```

---

## Step 5: Store the AI Analysis in a Variable

### 5.1 Initialize the AIAnalysis Variable (Once)

If you haven't already, add a variable initialization at the start of your Logic App (after the trigger):

1. Click **+** near the top, after the trigger
2. Search for **Initialize variable**
3. Set:
   - **Name:** `AIAnalysis`
   - **Type:** `String`
   - **Value:** (leave empty)

### 5.2 Set the AIAnalysis Variable from the OpenAI Response

After the **Parse JSON** action, add a **Set variable** action:

1. Click **+** below Parse JSON
2. Search for **Set variable**
3. Configure:
   - **Name:** `AIAnalysis`
   - **Value:** (from dynamic content) `message` → `content` from the parsed response

This extracts the AI's response text (e.g., "PASS: The document shows...") and stores it for use in later labs.

---

## Step 6: Test the Complete Workflow

### 6.1 Upload a Test Image

1. Save your Logic App (click **Save**)
2. Go to your **Storage Account** → **Blob containers** (where you configured the trigger)
3. Upload a test image (JPG or PNG, 100 KB–4 MB)

### 6.2 Monitor the Workflow Run

1. Go back to your **Logic App** → **Overview**
2. Look for a run triggered by your upload
3. Click on the run to see details

### 6.3 Verify Each Step

- ✅ **Blob trigger** fired
- ✅ **Get blob content** returned image bytes
- ✅ **Document Intelligence POST** returned operation-location
- ✅ **Delay** waited appropriately
- ✅ **Document Intelligence GET** returned extracted text
- ✅ **Set ExtractedText** shows actual text
- ✅ **HTTP (OpenAI)** returned 200 OK
- ✅ **Parse JSON** parsed the response
- ✅ **Set AIAnalysis** shows the AI's response (PASS/FAIL + explanation)

### 6.4 Inspect the AI Analysis Output

Click on the **Set AIAnalysis** action and check the output. You should see something like:

```
PASS: The image contains a clearly visible signed approval form with current date and authorized signature. The extracted text confirms key compliance fields are present.
```

If the response is empty or shows an error, see the troubleshooting section.

---

## Step 7: Customize the AI Prompt for Your Audit Points

### 7.1 Understanding Prompt Engineering

The `"content"` field in the user message is your **audit prompt**. It controls what the AI analyzes and how it responds.

**Current prompt (generic):**
```
Audit Point: Verify compliance with evidence review standards.
```

**Example: Customize for accounts payable audit:**
```
Audit Point: Verify that the invoice contains all required fields: vendor name, invoice date, invoice number, total amount, and approval signature.

Extracted Text from Image:
[extracted text]

Does the invoice show all required fields? Respond with: PASS/FAIL and explain which fields are present or missing.
```

### 7.2 How to Update the Prompt

1. Open the Logic App Designer
2. Click on the **HTTP (OpenAI)** action → **Body**
3. Edit the text inside the **"type": "text"** field:
   - Replace "Audit Point: Verify compliance..." with your specific requirement
   - Keep the structured format: "Audit Point: ...\n\nExtracted Text: ...\n\nRespond with: PASS/FAIL..."
4. Save and test with a new image

> **💡 Tip:** For better results, be specific in your audit points. Instead of "Check the document," try "Verify that the invoice total matches the line items and includes sales tax."

---

## Multimodal Concepts: Base64 Encoding

### Why Base64?

Images need to be text-encoded to travel in JSON. **Base64** is the standard encoding for this.

**The expression:** `base64(body('Get_blob_content'))`

This:
1. Takes the blob content (raw bytes)
2. Encodes it as Base64 text
3. Prepends the data URL prefix: `data:image/jpeg;base64,`
4. Results in a URL that Azure OpenAI can decode and analyze

**What you see in the final message:**
```
"url": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD..."
```

The `...` represents thousands of Base64-encoded characters. Azure OpenAI decodes this server-side.

---

## Testing Scenario: End-to-End Flow

**Scenario:** Audit compliance form check

1. **Upload:** You upload a scanned compliance form to your blob container
2. **Trigger:** Logic App Blob trigger fires
3. **Get blob:** Image bytes retrieved
4. **Extract text:** Document Intelligence finds text: "Approval: Signed by Manager Date: 2025-03-18"
5. **OpenAI analysis:** GPT-4o sees both the image AND extracted text, responds: "PASS: Form contains required signature and current date."
6. **Store:** AIAnalysis variable = "PASS: Form contains..."
7. **Output:** Later labs use this PASS/FAIL and explanation for validation logic

---

## Phase 3 Milestone: Multimodal Analysis Complete ✅

You've completed the **multimodal analysis stage** of your 5-stage pipeline:

| Stage | Lab | Status |
|-------|-----|--------|
| 1. Image Ingestion (Blob Trigger) | Lab 6 | ✅ Complete |
| 2. Text Extraction (Document Intelligence) | Lab 7 | ✅ Complete |
| 3. **Multimodal Analysis (Azure OpenAI Vision)** | **Lab 8** | **✅ Complete** |
| 4. Validation & Matching | Lab 9 | ⏳ Next |
| 5. JSON Output & Storage | Lab 10 | ⏳ Coming |

Your Logic App now:
- Extracts text from images with Document Intelligence
- Sends images + text to Azure OpenAI Vision (GPT-4o/4-Turbo)
- Gets structured AI analysis (PASS/FAIL + explanation)
- Stores results in variables for downstream use

Next, you'll build the validation logic to compare AI analysis against audit requirements and produce scored results.

---

## Security & Post-Lab Hardening

This lab uses your Azure OpenAI key directly in the Logic App action. For production use, implement these hardening steps **after** you complete the core labs:

1. **Use Managed Identity** — Replace API key with Logic App system-assigned identity
   - Enable managed identity on the Logic App
   - Grant the identity access to Azure OpenAI (RBAC role: "Cognitive Services OpenAI User")
   - Remove the `api-key` header; let Azure handle authentication

2. **Store keys in Key Vault** — Don't paste keys in Logic App actions
   - Create an Azure Key Vault
   - Store your OpenAI key in Key Vault
   - Reference it from Logic App using Key Vault connector

3. **Monitor API usage** — Track costs and detect abuse
   - Enable Azure Monitor on your OpenAI resource
   - Set up alerts for unexpected token usage

4. **Audit logging** — Record all API calls
   - Enable diagnostic logs in Azure OpenAI
   - Route logs to a Log Analytics workspace

See [Azure OpenAI security best practices](https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/security) for more.

---

## Troubleshooting

### Q: I'm getting HTTP 401 (Unauthorized)

**A:** Your Azure OpenAI key is incorrect or expired.

1. Go to **Azure Portal** → **Azure OpenAI** resource
2. Click **Keys and Endpoint**
3. Copy **Key 1** and verify it matches your Logic App
4. Update the `api-key` header in the HTTP action
5. Try the run again

### Q: I'm getting HTTP 404 (Not Found)

**A:** The deployment name or endpoint is incorrect.

1. Verify your deployment name:
   - Azure Portal → Azure OpenAI → **Model deployments**
   - Check the exact deployment name (e.g., `gpt-4o`, not `gpt4o`)
2. Verify your endpoint:
   - Should be `https://[resource-name].openai.azure.com/`
   - Not `https://[resource-name].openai.com/` (that's the public OpenAI endpoint)
3. Update the URI in the HTTP action and retry

### Q: I'm getting HTTP 400 (Bad Request)

**A:** The request body is malformed JSON.

1. Click the **HTTP (OpenAI)** action → **Body**
2. Verify the JSON is valid:
   - No missing commas or quotes
   - All braces/brackets are balanced
   - If using expressions, check for escaping issues
3. Use a JSON validator (online tool) to check the body structure
4. Fix the JSON and retry

### Q: The AIAnalysis variable is empty

**A:** The response parsing failed.

1. Click the **Parse JSON** action in your run details
2. Look at the **Output** — what does the full response look like?
3. If the structure doesn't match the schema, update the schema to match
4. Click on **Set AIAnalysis** and verify it's pulling from the correct field

### Q: Azure OpenAI took too long / hit rate limits

**A:** OpenAI is processing many requests or the model is slow.

1. Increase the timeout:
   - In Logic App settings, increase the HTTP timeout (default: 120 seconds)
2. Check your quota:
   - Azure Portal → Azure OpenAI → **Quotas**
   - Verify you haven't hit your rate limit or token limit
3. If needed, upgrade your OpenAI quota or add retries in your workflow

### Q: The AI response is generic or unhelpful

**A:** The prompt needs refinement.

1. In the HTTP action **Body**, edit the user message text
2. Add more context: specific field names, expected values, examples
3. Example improvement:
   - Before: "Is the form signed?"
   - After: "Is the form signed by an authorized manager (not just any signature)? Look for 'Manager Approval' label and a readable name next to the signature."
4. Re-test with the same image to see improved results

### Q: Base64 encoding failed

**A:** The blob content is not being retrieved correctly.

1. Verify the **Get blob content** action is working:
   - Check the action output in your run details
   - Should show binary data
2. Verify the **Get blob content** action name matches the expression:
   - If you renamed it to "Read blob content", update `base64(body('Get_blob_content'))` to `base64(body('Read_blob_content'))`
3. Check the image file size:
   - Must be under 100 MB for Logic App blobs
   - Azure OpenAI accepts up to 20 MB base64 per image

---

## Key Concepts Recap

| Concept | Definition |
|---------|-----------|
| **Multimodal** | AI model that understands multiple input types (text + image) |
| **GPT-4o/4-Turbo Vision** | Azure OpenAI model with image analysis capability |
| **Base64 encoding** | Text representation of binary data; allows images in JSON |
| **Chat Completions API** | Azure OpenAI endpoint for Q&A with conversation context |
| **System prompt** | Instructions that define the AI's role and behavior |
| **User message** | Your actual question or task; can contain text + images |
| **max_tokens** | Maximum length of the AI response (500 = ~200 words) |
| **temperature** | Controls randomness (0.5 = balanced, deterministic-creative) |

---

## Review Checklist

Before moving to Lab 9, verify:

- ✅ Azure OpenAI HTTP action is configured with correct URI and deployment name
- ✅ Headers include `api-key` and `Content-Type: application/json`
- ✅ Request body contains multimodal message structure with system + user messages
- ✅ User message includes both text (audit prompt) and image (base64)
- ✅ Parse JSON action schema matches the Azure OpenAI response structure
- ✅ AIAnalysis variable is initialized and set with the parsed response
- ✅ Test upload completed successfully
- ✅ AIAnalysis variable shows actual AI response (PASS/FAIL + explanation)
- ✅ Logic App is saved (no unsaved changes)

All set? Move to **Lab 9: Build Validation Logic** →

---

## Navigation

[← Previous: Integrate Document Intelligence](lab-07-doc-intel.md)

[Next: Build Validation Logic →](lab-09-validation.md)

---

*Lab 8 created by Bond. Last updated: March 2026.*
