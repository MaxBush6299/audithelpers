# Lab 9: Build Validation Logic

**Estimated duration:** 25 minutes  
**Owner:** Bond  
**Objective:** Add a validation stage to your Logic App workflow that evaluates evidence against audit points using Azure OpenAI and returns a structured verdict (APPROVED/REJECTED).

---

## What You'll Learn

In this lab, you will:

- ✅ Understand the validation stage: combining extracted text + visual analysis to produce a verdict
- ✅ Add an HTTP action to call Azure OpenAI with a structured evaluation prompt
- ✅ Send extracted text (from Lab 7) and visual analysis (from Lab 8) as context
- ✅ Parse the JSON verdict response with the Parse JSON action
- ✅ Store verdict fields (approval status, confidence, explanation, evidence) in variables
- ✅ Hardcode an example audit point and extend later as needed
- ✅ Test your workflow end-to-end with a sample image and audit scenario

> **📝 Note:** This lab builds on Lab 8. Your Logic App now has:
> - Blob trigger
> - Get blob content
> - Document Intelligence extraction (Lab 7)
> - Azure OpenAI Vision analysis (Lab 8)
>
> In this lab, you'll add a second Azure OpenAI call to evaluate the combined evidence.

---

## Prerequisites

Before starting this lab, ensure you have:

- ✅ **Lab 8 complete:** Logic App with Document Intelligence extraction and Azure OpenAI Vision analysis
- ✅ **Azure OpenAI endpoint and key:** From Lab 3, stored in `.env` file
- ✅ **Logic App workflow open:** In Azure Portal, ready to edit
- ✅ **Variables from Labs 7–8:** 
  - `ExtractedText` (from Document Intelligence)
  - `AIAnalysis` (from OpenAI Vision)

---

## What Is Validation Logic?

**Validation** is the decision-making stage of your pipeline. It combines two inputs:

1. **Extracted Text** — The OCR'd text from the evidence document (Lab 7)
2. **Visual Analysis** — Azure OpenAI's interpretation of the image (Lab 8)

Together, these inputs are evaluated **against an audit point** (a specific requirement or policy). The result is a structured verdict:

```json
{
  "verdict": "APPROVED",
  "confidence": 0.92,
  "explanation": "The invoice clearly shows the required PO number and authorized signature.",
  "extracted_evidence": ["PO-2024-5678", "Signed by CFO"]
}
```

**Why a second Azure OpenAI call?**

- **Lab 8 analyzed the image:** "What do I see in this image?"
- **Lab 9 evaluates the evidence:** "Does this evidence meet the audit requirement?"

This separation allows auditors to define different evaluation criteria for different audit points without rebuilding the extraction stages.

---

## Step 1: Understand the Validation Prompt

### 1.1 The Structured Evaluation Prompt

You'll send Azure OpenAI a prompt that asks for a **JSON verdict**. The prompt includes:

- **The audit point:** What requirement must this evidence meet?
- **Extracted text:** OCR'd content from the document
- **Visual analysis:** Your previous AI analysis from Lab 8

Example prompt:

```
You are an audit evidence evaluator. Given the following:

AUDIT POINT: Invoice must include PO number, date, vendor name, and authorized signature.

EXTRACTED TEXT FROM DOCUMENT:
{ExtractedText variable}

VISUAL ANALYSIS OF IMAGE:
{AIAnalysis variable}

Evaluate whether this evidence supports the audit point. Return ONLY a JSON object:
{
  "verdict": "APPROVED" or "REJECTED",
  "confidence": 0.0 to 1.0,
  "explanation": "Your reasoning here",
  "extracted_evidence": ["key evidence 1", "key evidence 2"]
}
```

### 1.2 Understanding the Verdict Response

Azure OpenAI will return:

```json
{
  "choices": [
    {
      "message": {
        "content": "{\"verdict\": \"APPROVED\", \"confidence\": 0.95, \"explanation\": \"...\", \"extracted_evidence\": [...]}"
      }
    }
  ]
}
```

You'll extract the JSON from `choices[0].message.content` and parse it.

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
Document Intelligence (POST + GET)
  ↓
Azure OpenAI Vision (HTTP POST)
  ↓
(empty — where you'll add validation logic)
```

### 2.2 Position Your Cursor

1. In Logic App Designer, click the **+** button below your last action (the OpenAI Vision HTTP POST)
2. Select **Add an action**

---

## Step 3: Initialize a Variable for the Audit Point

Before calling Azure OpenAI for validation, you'll store the audit point in a variable. For this lab, you'll hardcode an example.

### 3.1 Add a Variable Action

1. In the **Choose an action** search, type `Initialize variable`
2. Click **Initialize variable** (from the Variables connector)
3. Fill in the fields:

   | Field | Value |
   |-------|-------|
   | **Name** | `AuditPoint` |
   | **Type** | String |
   | **Value** | Copy-paste the audit requirement below: |

   ```
   Invoice must include: PO number, vendor name, date, and authorized signature.
   ```

4. Click **Save** (the blue icon in the top toolbar, or press Ctrl+S)

**Why hardcode it here?**  
In a production system, the audit point would come from a database or user input (Lab 12 with Power Apps). For this lab, you hardcode it to focus on the validation logic itself.

---

## Step 4: Add the Validation HTTP Action (Call Azure OpenAI)

### 4.1 Add Another HTTP Action

1. Click the **+** button below the `AuditPoint` variable action
2. Select **Add an action**
3. Search for `HTTP` and click **HTTP** (from the built-in connector)
4. Configure the HTTP action:

   | Field | Value |
   |-------|-------|
   | **Method** | `POST` |
   | **URI** | `https://{your-ai-service-name}.openai.azure.com/openai/deployments/{your-deployment-name}/chat/completions?api-version=2024-02-15-preview` |
   | **Headers** | (see Step 4.2 below) |
   | **Body** | (see Step 4.3 below) |

   Replace:
   - `{your-ai-service-name}` — Your Azure OpenAI service name (e.g., `my-openai-service`)
   - `{your-deployment-name}` — Your deployment name (e.g., `gpt-4-vision`)

### 4.2 Add Headers

In the **Headers** field, enter:

```json
{
  "api-key": "{your-openai-key}",
  "Content-Type": "application/json"
}
```

Or use **Header** key-value pairs:

| Key | Value |
|-----|-------|
| `api-key` | `{your-openai-key}` (from `.env` or Lab 3 deployment) |
| `Content-Type` | `application/json` |

### 4.3 Add the Request Body

In the **Body** field, enter:

```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are an audit evidence evaluator. Your task is to assess whether provided evidence meets specific audit requirements. Always respond with a valid JSON object containing: verdict (APPROVED or REJECTED), confidence (0.0 to 1.0), explanation (string), and extracted_evidence (array of strings). Do not include any text outside the JSON object."
    },
    {
      "role": "user",
      "content": "AUDIT POINT: {AuditPoint variable}\n\nEXTRACTED TEXT FROM DOCUMENT:\n{ExtractedText variable}\n\nVISUAL ANALYSIS OF IMAGE:\n{AIAnalysis variable}\n\nEvaluate whether this evidence supports the audit point. Return ONLY a JSON object with fields: verdict, confidence, explanation, extracted_evidence."
    }
  ],
  "temperature": 0.5,
  "max_tokens": 500
}
```

To insert variables dynamically:

1. Click in the **Body** field where you want to insert a variable
2. Click the **lightning bolt icon** (Add dynamic content) on the right
3. From the **Variables** section, select `AuditPoint`, `ExtractedText`, or `AIAnalysis`
4. Click **Insert**

The body will now contain dynamic references:

```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are an audit evidence evaluator. Your task is to assess whether provided evidence meets specific audit requirements. Always respond with a valid JSON object containing: verdict (APPROVED or REJECTED), confidence (0.0 to 1.0), explanation (string), and extracted_evidence (array of strings). Do not include any text outside the JSON object."
    },
    {
      "role": "user",
      "content": "@{concat('AUDIT POINT: ', variables('AuditPoint'), '\n\nEXTRACTED TEXT FROM DOCUMENT:\n', variables('ExtractedText'), '\n\nVISUAL ANALYSIS OF IMAGE:\n', variables('AIAnalysis'), '\n\nEvaluate whether this evidence supports the audit point. Return ONLY a JSON object with fields: verdict, confidence, explanation, extracted_evidence.')}"
    }
  ],
  "temperature": 0.5,
  "max_tokens": 500
}
```

5. Click **Save**

---

## Step 5: Parse the Validation Response

### 5.1 Add a Parse JSON Action

After the validation HTTP action, you'll parse the OpenAI response:

1. Click the **+** button below the HTTP validation action
2. Select **Add an action**
3. Search for `Parse JSON` and click **Parse JSON** (from the Data Operations connector)

### 5.2 Configure Parse JSON

Fill in the fields:

| Field | Value |
|-------|-------|
| **Content** | (click the lightning bolt, select the **Body** output from the HTTP validation action above) |
| **Schema** | (see Step 5.3) |

### 5.3 Provide the JSON Schema

In the **Schema** field, paste the schema for the Azure OpenAI response:

```json
{
  "type": "object",
  "properties": {
    "choices": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "message": {
            "type": "object",
            "properties": {
              "content": {
                "type": "string"
              }
            }
          }
        }
      }
    }
  }
}
```

Click **Save**

---

## Step 6: Extract and Parse the Verdict JSON

The `content` field contains a JSON string. You need to extract it and parse it again.

### 6.1 Initialize Variables for Verdict Fields

Add four new variable actions to store the verdict components:

1. Click **+** below the Parse JSON action
2. **Add an action** → **Initialize variable**
3. Create variable #1:

   | Field | Value |
   |-------|-------|
   | **Name** | `Verdict` |
   | **Type** | String |
   | **Value** | Leave blank for now (you'll set it dynamically) |

4. Click **Save**

Repeat for three more variables:

**Variable #2:**

| Field | Value |
|-------|-------|
| **Name** | `Confidence` |
| **Type** | Number |
| **Value** | `0` |

**Variable #3:**

| Field | Value |
|-------|-------|
| **Name** | `Explanation` |
| **Type** | String |
| **Value** | Leave blank |

**Variable #4:**

| Field | Value |
|-------|-------|
| **Name** | `ExtractedEvidence` |
| **Type** | Array |
| **Value** | Leave blank |

### 6.2 Add Parse JSON for Verdict Object

Now parse the `content` string as JSON:

1. Click **+** below the last variable initialization
2. **Add an action** → **Parse JSON**
3. Fill in:

   | Field | Value |
   |-------|-------|
   | **Content** | Click the lightning bolt, find the **choices** array output from the previous Parse JSON, then drill into `[0].message.content` |
   | **Schema** | (see below) |

For the **Content** field, you're extracting the first choice's message content. In the dynamic content picker, you may need to:
- Click **Expression**
- Enter: `body('Parse_JSON')?['choices']?[0]?['message']?['content']`
- Click **Add**

For the **Schema**, paste:

```json
{
  "type": "object",
  "properties": {
    "verdict": {
      "type": "string"
    },
    "confidence": {
      "type": "number"
    },
    "explanation": {
      "type": "string"
    },
    "extracted_evidence": {
      "type": "array",
      "items": {
        "type": "string"
      }
    }
  }
}
```

Click **Save**

---

## Step 7: Set Verdict Variables

Now populate your verdict variables with the parsed data:

### 7.1 Set Verdict Variable

1. Click **+** below the latest Parse JSON action
2. **Add an action** → search for `Set variable`
3. Click **Set variable** (from the Variables connector)
4. Fill in:

   | Field | Value |
   |-------|-------|
   | **Name** | `Verdict` |
   | **Value** | Click the lightning bolt, select **verdict** from the Parse JSON Verdict output |

5. Click **Save**

### 7.2 Set Confidence Variable

1. Click **+** below
2. **Add an action** → **Set variable**
3. Fill in:

   | Field | Value |
   |-------|-------|
   | **Name** | `Confidence` |
   | **Value** | Click the lightning bolt, select **confidence** from the Parse JSON Verdict output |

4. Click **Save**

### 7.3 Set Explanation Variable

1. Click **+** below
2. **Add an action** → **Set variable**
3. Fill in:

   | Field | Value |
   |-------|-------|
   | **Name** | `Explanation` |
   | **Value** | Click the lightning bolt, select **explanation** from the Parse JSON Verdict output |

4. Click **Save**

### 7.4 Set Extracted Evidence Variable

1. Click **+** below
2. **Add an action** → **Set variable**
3. Fill in:

   | Field | Value |
   |-------|-------|
   | **Name** | `ExtractedEvidence` |
   | **Value** | Click the lightning bolt, select **extracted_evidence** from the Parse JSON Verdict output |

4. Click **Save**

---

## Step 8: Test Your Validation Workflow

### 8.1 Run a Test

1. Click the **Save** button (top toolbar)
2. Click the **Run Trigger** button
3. Select **With input**
4. For **blobName**, enter a test image name (e.g., `test-invoice.jpg`)
5. Click **Run**

### 8.2 Monitor Execution

1. The workflow will run. You'll see the flow with each action highlighted in real-time
2. If any action fails, click on it to see the error details
3. Once complete, scroll through the actions to verify:
   - ✅ **Get blob content** retrieved the image
   - ✅ **Document Intelligence** extracted text into `ExtractedText`
   - ✅ **OpenAI Vision** returned visual analysis into `AIAnalysis`
   - ✅ **Validation HTTP** returned a response
   - ✅ **Parse JSON (OpenAI response)** parsed the choices array
   - ✅ **Parse JSON (Verdict)** parsed the verdict object
   - ✅ Variables are populated: `Verdict`, `Confidence`, `Explanation`, `ExtractedEvidence`

### 8.3 View the Variables

Click on each **Set variable** action to expand it and verify the values:

```
Verdict: APPROVED
Confidence: 0.92
Explanation: The invoice includes all required fields: PO number (PO-2024-5678), vendor name (ACME Corp), date (2024-03-15), and signature.
ExtractedEvidence: ["PO-2024-5678", "ACME Corp", "2024-03-15", "Authorized Signature"]
```

### 8.4 Troubleshoot Common Issues

**Issue:** "Parse JSON returned invalid JSON"
- **Cause:** Azure OpenAI returned non-JSON text
- **Fix:** Check the HTTP response body in the validation action. Ensure your system prompt asks for JSON-only output.

**Issue:** "Confidence field is not a number"
- **Cause:** OpenAI returned a string (e.g., "0.92") instead of a number (e.g., 0.92)
- **Fix:** The Parse JSON schema will coerce it. If still failing, add a **Compose** action to convert it: `float(body('Parse_JSON_Verdict').confidence)`

**Issue:** "Verdict is empty"
- **Cause:** The parsing didn't capture the data correctly
- **Fix:** Click the failing **Set variable** action and view the dynamic content. Ensure you selected the correct field from the Parse JSON output.

---

## Step 9: Review Your Validation Stage

Your workflow now includes:

```
Trigger: When a blob is created
  ↓
Get blob content
  ↓
Document Intelligence (POST + GET)
  ↓
Azure OpenAI Vision (HTTP POST)
  ↓
Initialize variable: AuditPoint
  ↓
HTTP action: Call Azure OpenAI for validation
  ↓
Parse JSON (OpenAI response)
  ↓
Parse JSON (Verdict object)
  ↓
Set variable: Verdict
  ↓
Set variable: Confidence
  ↓
Set variable: Explanation
  ↓
Set variable: ExtractedEvidence
  ↓
(Next: Generate JSON Output — Lab 10)
```

---

## What's Next?

You've built the validation logic that evaluates evidence and returns a structured verdict. Now you'll:

- **Lab 10:** Generate a JSON output file that combines all results (extracted text, visual analysis, and verdict) for downstream consumption (Power Apps, dashboards, audit logs).

---

## Optional Extension: Load Audit Points from a Database

In a production system, audit points shouldn't be hardcoded. Consider these options:

1. **Load from a SQL Database:** Add a database action before the validation HTTP call to fetch the audit point based on an audit ID
2. **Load from a SharePoint List:** Use the SharePoint connector to fetch audit requirements maintained by auditors
3. **Load from Power Apps:** Have the Power Apps portal (Lab 12) pass the audit point as input to the Logic App
4. **Load from Azure Table Storage:** Store audit points in a table and query by key

For now, your hardcoded example demonstrates the full flow. Return to this after Lab 10 if needed.

---

## Summary

In this lab, you:

- ✅ Added a validation HTTP action that calls Azure OpenAI a second time
- ✅ Sent a structured prompt with audit point, extracted text, and visual analysis
- ✅ Parsed the JSON verdict response
- ✅ Stored verdict fields in variables (verdict, confidence, explanation, evidence)
- ✅ Tested the workflow end-to-end

Your Logic App now performs the complete evaluation pipeline: **Extract → Analyze → Validate → (Soon) Output**.

---

## Navigation

[← Previous: Add Azure OpenAI Vision](lab-08-openai.md)  
[Next: Generate JSON Output →](lab-10-output.md)

---

*Lab written by Bond. Last updated: March 2026*
