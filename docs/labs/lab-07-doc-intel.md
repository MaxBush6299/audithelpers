# Lab 7: Integrate Document Intelligence

**Estimated duration:** 25 minutes  
**Owner:** Bond  
**Objective:** Add a Document Intelligence action to your Logic App workflow to extract text and structure from evidence images using the Layout API.

---

## What You'll Learn

In this lab, you will:

- ✅ Understand the Document Intelligence Layout API and how it extracts text from images
- ✅ Add an HTTP action to call the Document Intelligence API from Logic App Designer
- ✅ Handle asynchronous responses using operation-location headers
- ✅ Poll for results using a delay and GET request
- ✅ Parse JSON responses to extract the `analyzeResult.content` field
- ✅ Initialize and set variables to store extracted text for downstream actions
- ✅ Test your workflow by uploading an image and verifying text extraction

> **📝 Note:** This lab builds on Lab 6. Your Logic App already has a Blob trigger and a "Get blob content" action. In this lab, you'll add Document Intelligence integration between those actions and the eventual JSON output.

---

## Prerequisites

Before starting this lab, ensure you have:

- ✅ **Lab 6 complete:** Logic App created with Blob trigger and "Get blob content" action
- ✅ **Document Intelligence endpoint and key:** From Lab 2, stored in `.env` file
- ✅ **Logic App workflow open:** In Azure Portal, ready to edit
- ✅ **Sample image:** A test file (JPG or PNG) to upload for verification

---

## What Is the Document Intelligence Layout API?

**Document Intelligence** is an Azure Cognitive Service that uses AI to extract text, tables, and structure from documents and images.

**Why the Layout API?**
- **Text extraction:** Recognizes all text in an image, line by line
- **Structure preservation:** Understands layout (paragraphs, tables, headings)
- **Asynchronous:** Returns immediately with an `operation-location` header; results are ready after a few seconds
- **Multimodal-ready:** Extracted text becomes input for Azure OpenAI Vision (Lab 8)

**How it works in your workflow:**
1. User uploads an image to Blob Storage
2. Logic App reads the image bytes
3. HTTP action sends image to Document Intelligence Layout API
4. API returns an `operation-location` URL for polling
5. Logic App waits (delay or loop) and polls for results
6. When ready, Logic App extracts the text from the response
7. Text is stored in a variable for downstream actions (Azure OpenAI, validation, etc.)

---

## Step 1: Understand the Document Intelligence Request/Response Flow

### 1.1 The POST Request (Analyze Image)

Your Logic App will send:

```
POST {DOCUMENT_INTELLIGENCE_ENDPOINT}/formrecognizer/documentModels/prebuilt-layout:analyze?api-version=2023-07-31

Headers:
  Ocp-Apim-Subscription-Key: {your-key}
  Content-Type: image/jpeg (or image/png)

Body: (raw image bytes from the blob)
```

**What this does:**
- Tells Document Intelligence to analyze the image using the built-in "layout" model (no training required)
- Sends the image as raw bytes
- Includes your subscription key for authentication

**What you get back:**
- HTTP 202 (Accepted) — analysis started asynchronously
- Header `operation-location` — a polling URL to check for results
- No immediate results; you must poll

### 1.2 The GET Request (Retrieve Results)

After a delay (e.g., 10 seconds), your Logic App will GET:

```
GET {operation-location-url}

Headers:
  Ocp-Apim-Subscription-Key: {your-key}
```

**Response (HTTP 200 OK):**

```json
{
  "status": "succeeded",
  "analyzeResult": {
    "apiVersion": "2023-07-31",
    "modelId": "prebuilt-layout",
    "stringIndexType": "textElements",
    "content": "This is all the text extracted from the image in reading order.",
    "pages": [
      {
        "pageNumber": 1,
        "width": 8.5,
        "height": 11.0,
        "lines": [
          {
            "content": "First line of text",
            "boundingPolygon": [...],
            "spans": [...]
          }
        ]
      }
    ]
  }
}
```

**Key fields:**
- `status`: "succeeded", "running", or "failed"
- `analyzeResult.content`: **The full extracted text** (what you'll use)
- `analyzeResult.pages`: Detailed per-page structure (optional)

---

## Step 2: Return to Your Logic App Workflow

### 2.1 Open Your Workflow in Portal

1. Go to [Azure Portal](https://portal.azure.com)
2. Search for your Logic App (e.g., `logic-app-audit-pipeline-{initials}`)
3. Click on it to open
4. In the left menu, click **Workflows** (under "Development")
5. Click on your workflow (e.g., `AnalyzeEvidence`)
6. Click **Edit** (or the pencil icon) to open Logic App Designer

You should see your current workflow:
```
Trigger: When a blob is created
  ↓
Get blob content
  ↓
(empty — where you'll add Document Intelligence)
```

### 2.2 Add the Document Intelligence POST Action

Your next step is to add an HTTP action to call Document Intelligence.

1. Click **+ New step** (below "Get blob content")
2. Search for **HTTP** in the search box
3. Select **HTTP** (under Actions)

You now have an HTTP action placeholder. Fill it in:

4. **Method:** Select **POST** (dropdown)

5. **URI:** Paste this URL, replacing placeholders with your values:
   ```
   https://{your-region}.api.cognitive.microsoft.com/formrecognizer/documentModels/prebuilt-layout:analyze?api-version=2023-07-31
   ```
   
   Replace `{your-region}` with the region from your Document Intelligence endpoint in `.env` (e.g., `eastus2`, `westus`, etc.).
   
   **Example:** If your endpoint is `https://eastus2.api.cognitive.microsoft.com/`, use:
   ```
   https://eastus2.api.cognitive.microsoft.com/formrecognizer/documentModels/prebuilt-layout:analyze?api-version=2023-07-31
   ```

6. **Headers:** Click **Add new parameter** → **Headers** (if not already visible)
   
   Add two headers:
   - **Header 1:**
     - Name: `Ocp-Apim-Subscription-Key`
     - Value: Paste your Document Intelligence key from `.env`
   
   - **Header 2:**
     - Name: `Content-Type`
     - Value: `image/jpeg` (adjust to `image/png` if you're testing with PNG files)

7. **Body:** 
   - In the **Body** field, click the expression bar and select the **Get blob content** output
   - Or manually type: `@body('Get_blob_content')`
   - This sends the raw image bytes to Document Intelligence

8. **Rename the action (optional):**
   - Click the three dots (`...`) in the top-right of the HTTP action
   - Click **Rename**
   - Type: `Document Intelligence - Analyze Image`
   - Click the checkmark to save

Your HTTP action now looks like:

```
POST https://eastus2.api.cognitive.microsoft.com/formrecognizer/documentModels/prebuilt-layout:analyze?api-version=2023-07-31

Headers:
  Ocp-Apim-Subscription-Key: <your-key>
  Content-Type: image/jpeg

Body: @body('Get_blob_content')
```

9. Click **Save** (top-left of Logic App Designer)

---

## Step 3: Add a Delay and Polling Loop

The Document Intelligence API returns asynchronously. You'll add a delay, then poll for results.

### 3.1 Add a Delay Action

1. Click **+ New step** (below the "Document Intelligence - Analyze Image" action)
2. Search for **Delay** in the search box
3. Select **Delay** (under Actions)

4. Configure:
   - **Count:** `10`
   - **Unit:** `Second`

This pauses for 10 seconds, giving Document Intelligence time to process your image.

5. Click **Save**

### 3.2 Add a GET Action to Retrieve Results

Now you'll make a second HTTP call to fetch the results.

1. Click **+ New step** (below the Delay action)
2. Search for **HTTP** in the search box
3. Select **HTTP** (under Actions)

4. Configure:
   - **Method:** `GET`
   
   - **URI:** 
     - Click the expression bar
     - Select **Headers** → **operation-location** (from the "Document Intelligence - Analyze Image" response)
     - Or type: `@outputs('Document Intelligence - Analyze Image')['headers']['operation-location']`
   
   - **Headers:** Add one header:
     - Name: `Ocp-Apim-Subscription-Key`
     - Value: Your Document Intelligence key from `.env`

5. **Rename the action (optional):**
   - Rename to: `Get Document Intelligence Results`

Your GET action now looks like:

```
GET @outputs('Document Intelligence - Analyze Image')['headers']['operation-location']

Headers:
  Ocp-Apim-Subscription-Key: <your-key>
```

6. Click **Save**

---

## Step 4: Initialize and Parse Variables

Now you'll extract the text from the Document Intelligence response and store it in a variable for downstream use.

### 4.1 Add Initialize Variable Action (Extract Text)

1. Click **+ New step** (below the GET action)
2. Search for **Initialize variable** in the search box
3. Select **Initialize variable** (under Actions)

4. Configure:
   - **Name:** `ExtractedText`
   - **Type:** `String`
   - **Value:** Leave blank for now (you'll set it in the next step)

5. Click **Save**

### 4.2 Add a Parse JSON Action (Optional but Recommended)

Parsing the response helps you access the text cleanly.

1. Click **+ New step** (below the Initialize Variable action)
2. Search for **Parse JSON** in the search box
3. Select **Parse JSON** (under Actions)

4. Configure:
   - **Content:** Click the expression bar and select the output from "Get Document Intelligence Results"
     - Or type: `@body('Get_Document_Intelligence_Results')`
   
   - **Schema:** Paste the Document Intelligence response schema:
   ```json
   {
     "type": "object",
     "properties": {
       "status": {
         "type": "string"
       },
       "analyzeResult": {
         "type": "object",
         "properties": {
           "apiVersion": {
             "type": "string"
           },
           "modelId": {
             "type": "string"
           },
           "content": {
             "type": "string"
           },
           "pages": {
             "type": "array"
           }
         }
       }
     }
   }
   ```

5. Click **Save**

This allows you to reference the JSON properties cleanly in downstream actions (e.g., `body('Parse_JSON')?['analyzeResult']['content']`).

### 4.3 Set the ExtractedText Variable

1. Click **+ New step** (below the Parse JSON action)
2. Search for **Set variable** in the search box
3. Select **Set variable** (under Actions)

4. Configure:
   - **Name:** `ExtractedText` (select from dropdown — you created this in Step 4.1)
   - **Value:** Click the expression bar
     - Select the Parsed JSON output: `body('Parse_JSON')?['analyzeResult']['content']`
     - Or type manually: `@body('Parse_JSON')?['analyzeResult']['content']`

5. Click **Save**

Now your workflow extracts the full text into the `ExtractedText` variable, ready for Azure OpenAI in Lab 8.

---

## Step 5: Review Your Complete Workflow

Your Logic App workflow should now look like this:

```
✅ When a blob is created (Blob trigger)
   ↓
✅ Get blob content
   ↓
✅ Document Intelligence - Analyze Image (POST)
   ↓
✅ Delay 10 seconds
   ↓
✅ Get Document Intelligence Results (GET)
   ↓
✅ Parse JSON
   ↓
✅ Initialize variable: ExtractedText
   ↓
✅ Set variable: ExtractedText = analyzeResult.content
   ↓
(Next: Lab 8 adds Azure OpenAI here)
```

Click **Save** to persist all changes.

---

## Step 6: Test Your Workflow

Now you'll upload a test image to verify Document Intelligence integration.

### 6.1 Prepare a Test Image

- Find a simple text image (e.g., a screenshot, document page, receipt, or handwritten note)
- Save it as JPG or PNG
- Size: 100 KB to 4 MB (Document Intelligence limits)

### 6.2 Upload to Blob Storage

1. Go to [Azure Portal](https://portal.azure.com)
2. Search for your Storage Account (from Lab 4)
3. Click on it
4. In the left menu, click **Containers** (under "Data storage")
5. Click on the **audit-input** container
6. Click **+ Upload**
7. Select your test image
8. Click **Upload**

### 6.3 Monitor the Logic App Run

1. Return to your Logic App in the Portal
2. In the left menu, click **Runs** (under "Development")
3. You should see a new run starting
4. Click on the run to open it

Monitor the run:
- ✅ **When a blob is created** — Triggered
- ✅ **Get blob content** — Retrieved image bytes
- ✅ **Document Intelligence - Analyze Image** — Returned 202 + operation-location header
- ✅ **Delay** — Waited 10 seconds
- ✅ **Get Document Intelligence Results** — Retrieved analysis with status "succeeded"
- ✅ **Parse JSON** — Parsed the response
- ✅ **Initialize variable** — Created ExtractedText
- ✅ **Set variable** — Extracted text stored

### 6.4 Verify Extracted Text

1. Click on the **Set variable** step in the run details
2. Look at the **Outputs** section
3. You should see the `ExtractedText` variable populated with all text from your image

**Example output:**
```
This is all the text from your image, extracted line by line in reading order. If your image had multiple lines, tables, or paragraphs, they appear here.
```

If you see text, Document Intelligence integration is working! ✅

### 6.5 Troubleshooting Test Failures

**Run failed at "Document Intelligence - Analyze Image"?**
- Check your Document Intelligence key and region in the URI
- Verify the image is JPG or PNG (not other formats)
- Ensure `Content-Type` matches your image format

**Run failed at "Get Document Intelligence Results"?**
- The `operation-location` header might be missing or malformed
- Check the HTTP response headers from the POST action
- Document Intelligence may need more than 10 seconds; increase the delay to 15–20 seconds

**ExtractedText is empty or null?**
- The response schema might not match your actual response
- Click on the "Get Document Intelligence Results" output to see the raw JSON
- Update the Parse JSON schema if needed

---

## Understanding the Response Structure

### Full Document Intelligence Response

When Document Intelligence finishes analyzing your image, the response looks like:

```json
{
  "status": "succeeded",
  "analyzeResult": {
    "apiVersion": "2023-07-31",
    "modelId": "prebuilt-layout",
    "stringIndexType": "textElements",
    "content": "All extracted text here, in reading order.",
    "pages": [
      {
        "pageNumber": 1,
        "width": 8.5,
        "height": 11.0,
        "lines": [
          {
            "content": "Line 1 of text",
            "boundingPolygon": [
              {"x": 0.5, "y": 1.0},
              {"x": 2.5, "y": 1.0},
              {"x": 2.5, "y": 1.3},
              {"x": 0.5, "y": 1.3}
            ],
            "spans": [...]
          },
          {
            "content": "Line 2 of text",
            "boundingPolygon": [...],
            "spans": [...]
          }
        ],
        "tables": [
          {
            "rowCount": 3,
            "columnCount": 2,
            "cells": [...]
          }
        ]
      }
    ]
  }
}
```

### Key Fields Explained

| Field | Purpose | Used By |
|-------|---------|---------|
| `status` | "running", "succeeded", or "failed" | Conditional logic (if needed) |
| `analyzeResult.content` | **Full extracted text in reading order** | Lab 8 (Azure OpenAI Vision) |
| `analyzeResult.pages` | Per-page structure, lines, tables, bounding boxes | Advanced scenarios (not required) |
| `analyzeResult.pages[].lines[]` | Individual lines with coordinates | Page-specific processing |
| `analyzeResult.pages[].tables[]` | Extracted tables | Structured data extraction |

**For this lab, you only need `analyzeResult.content`** — it's the complete text that Azure OpenAI will analyze in Lab 8.

---

## Key Concepts Recap

### Asynchronous Processing

Document Intelligence doesn't return results immediately. Instead:
1. **POST**: Start analysis → get `operation-location` header
2. **Wait**: Pause for processing (typically 3–10 seconds)
3. **GET**: Poll the `operation-location` → retrieve results

This is common for large file processing (your images might be 1–2 MB).

### Polling Pattern in Logic Apps

The flow you built is a **polling pattern**:
```
Initiate async operation (POST)
  ↓
Wait (Delay)
  ↓
Check for results (GET)
  ↓
(Optional: Loop back if status is "running" or add an Until loop for robust polling)
```

For this lab, a simple 10-second delay is sufficient. In production, you might add an **Until** loop to poll every second until status is "succeeded".

### Variables for Downstream Actions

You initialized `ExtractedText` as a String variable and populated it with the extracted content. In Lab 8, you'll pass `ExtractedText` to Azure OpenAI Vision for multimodal analysis (comparing text + image together).

---

## What's Next?

Your Logic App now:
- ✅ Triggers on blob uploads
- ✅ Extracts image bytes
- ✅ Calls Document Intelligence Layout API
- ✅ Polls for results
- ✅ Parses and stores extracted text

**Next step: Lab 8 — Add Azure OpenAI Vision**

In Lab 8, you'll:
- Add another HTTP action to call Azure OpenAI Vision API
- Send both the `ExtractedText` and the image blob to OpenAI
- Get a multimodal analysis (combining text + vision)
- Store the AI response for validation logic

---

## Phase 3 Milestone: Text Extraction Complete ✅

You've completed the **text extraction stage** of your 5-stage pipeline:

| Stage | Lab | Status |
|-------|-----|--------|
| 1. Image Ingestion (Blob Trigger) | Lab 6 | ✅ Complete |
| 2. **Text Extraction (Document Intelligence)** | **Lab 7** | **✅ Complete** |
| 3. Multimodal Analysis (Azure OpenAI Vision) | Lab 8 | ⏳ Next |
| 4. Validation & Matching | Lab 9 | ⏳ Coming |
| 5. JSON Output & Storage | Lab 10 | ⏳ Coming |

---

## Security & Post-Lab Hardening

This lab uses your Document Intelligence key directly in the Logic App action. For production use, implement these hardening steps **after** you complete the core labs:

1. **Use Managed Identity** — Replace API key with Logic App system-assigned identity
2. **Store keys in Key Vault** — Don't paste keys in Logic App actions
3. **Rotate keys** — Every 90 days, regenerate in Azure Portal
4. **Enable Azure Monitor** — Track all API calls and audit access

See [Azure Cognitive Services security best practices](https://learn.microsoft.com/en-us/azure/cognitive-services/security-features-and-considerations) for more.

---

## Troubleshooting

### Q: I'm getting HTTP 401 (Unauthorized)

**A:** Your Document Intelligence key is incorrect or expired.
1. Go to Azure Portal → Document Intelligence resource
2. Click **Keys and Endpoint** (under "Resource Management")
3. Copy **Key 1** and verify it matches your `.env` file
4. Update the `Ocp-Apim-Subscription-Key` header in the HTTP action

### Q: I'm getting HTTP 400 (Bad Request)

**A:** The request format is invalid. Check:
1. **URI:** Ensure the region in the endpoint matches your Document Intelligence location (e.g., `eastus2`)
2. **Content-Type:** Verify it matches your image format (`image/jpeg` or `image/png`)
3. **Body:** Ensure the "Get blob content" action is outputting raw image bytes, not Base64-encoded

### Q: The ExtractedText variable is empty or shows "null"

**A:** The response might have a different structure than expected.
1. Click on "Get Document Intelligence Results" in the run details
2. Look at the full response JSON
3. Find where the text content actually is
4. Update the Parse JSON schema and Set variable expression to match

### Q: Document Intelligence returned status "failed"

**A:** The image couldn't be analyzed. Check:
1. **Image size:** Must be 100 KB to 4 MB (Document Intelligence limits)
2. **Image format:** Only JPG and PNG are supported
3. **Image clarity:** Blurry or heavily corrupted images may fail
4. Try a different test image

### Q: The run times out (takes longer than 1–2 minutes)

**A:** Document Intelligence might need more time (rare).
1. Increase the Delay from 10 seconds to 20–30 seconds
2. Or add an **Until** loop to poll with retries:
   ```
   Until status == "succeeded" OR count > 5:
     Delay 3 seconds
     GET operation-location
   ```

---

## Review Checklist

Before moving to Lab 8, verify:

- ✅ Document Intelligence POST action is configured with correct URI and headers
- ✅ Delay is set to at least 10 seconds
- ✅ GET action uses the `operation-location` header from the POST response
- ✅ Parse JSON action schema includes `analyzeResult.content`
- ✅ ExtractedText variable is initialized and set with parsed content
- ✅ Test upload succeeded and ExtractedText contains actual extracted text
- ✅ Logic App is saved (no unsaved changes)

All set? Move to **Lab 8: Add Azure OpenAI Vision** →

---

## Navigation

[← Previous: Add Image Upload Trigger](lab-06-doc-intel.md)

[Next: Add Azure OpenAI Vision →](lab-08-openai.md)

---

*Lab 7 created by Bond. Last updated: March 2026.*
