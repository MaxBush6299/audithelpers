# Lab 10: Generate JSON Output

**Estimated duration:** 20 minutes  
**Owner:** Bond  
**Objective:** Compose the final audit results into a structured JSON object and write it to Blob Storage, completing the Logic App pipeline.

---

## What You'll Learn

In this lab, you will:

- ✅ Use the "Compose" action to build a structured JSON output
- ✅ Include all audit analysis results (verdict, confidence, explanation, evidence)
- ✅ Add metadata (processing time, timestamp, source file)
- ✅ Write the final JSON to Azure Blob Storage using the "Create blob" action
- ✅ Understand the complete pipeline flow from trigger to output

> **🎯 Note:** This lab completes **Phase 3** of the pipeline. Your Logic App is now ready for end-to-end testing in Lab 11.

---

## Prerequisites

Before starting this lab, ensure you have:

- ✅ **Lab 9 complete:** Validation logic in place (verdict, confidence, explanation, evidence as outputs)
- ✅ **Logic App open** in the Designer with all previous actions (Labs 6–9)
- ✅ **Storage Account** with `audit-output` container (from Lab 4)
- ✅ **Understanding of the output structure:** The JSON format that will be written to Blob Storage

---

## The JSON Output Structure

Your Logic App will produce a JSON object with this structure:

```json
{
  "audit_point_id": "AP-001",
  "source_file": "slide_008.png",
  "verdict": "APPROVED",
  "confidence": 0.92,
  "explanation": "The slide clearly shows calibration details matching the audit requirements.",
  "extracted_evidence": [
    "calibration_date: 2024-03-15",
    "technician: J. Smith",
    "equipment_status: Operational"
  ],
  "processing_time_ms": 2340,
  "timestamp": "2024-03-18T15:30:00Z"
}
```

### Field Descriptions

| Field | Source | Description |
|-------|--------|-------------|
| `audit_point_id` | Input parameter or hardcoded | The audit point identifier (e.g., "AP-001") |
| `source_file` | Trigger output | Name of the blob (image file) that was processed |
| `verdict` | Lab 9 output | Approval decision (APPROVED, REJECTED, NEEDS_REVIEW) |
| `confidence` | Lab 9 output | Confidence score (0.0–1.0) |
| `explanation` | Lab 9 output | Human-readable reasoning for the verdict |
| `extracted_evidence` | Lab 9 output | Array of key findings from the image |
| `processing_time_ms` | Calculated | Time elapsed from trigger to completion (milliseconds) |
| `timestamp` | Generated | UTC timestamp when processing completed |

---

## Step 1: Open Your Logic App in the Designer

1. Go to [portal.azure.com](https://portal.azure.com)
2. Search for and open **Logic Apps**
3. Click your Logic App from Lab 5 (e.g., `audit-logic-app`)
4. In the left menu, click **Logic App Designer**
   - You should see your workflow with all previous actions (trigger, Get Blob, Document Intelligence, OpenAI Vision, Validation logic)

---

## Step 2: Add the Compose Action

The **Compose** action constructs a JSON object from dynamic content and expressions.

1. Click the **+** button below your last action (the Validation logic from Lab 9) to add a new action
2. In the **Choose an operation** search box, type **compose**
3. Under the **Data Operations** category, select **Compose**
   - This action doesn't require a connection; it runs locally in the Logic App

---

## Step 3: Configure the Compose Action

The Compose action has a single input field called **Inputs**. You'll build the JSON structure here using dynamic content and expressions.

### Fill in the Inputs Field

Click inside the **Inputs** field and manually enter the JSON structure. For each field, use dynamic content from previous actions:

```json
{
  "audit_point_id": "AP-001",
  "source_file": @{triggerBody()?['Name']},
  "verdict": @{body('Validation_Logic')?['verdict']},
  "confidence": @{body('Validation_Logic')?['confidence']},
  "explanation": @{body('Validation_Logic')?['explanation']},
  "extracted_evidence": @{body('Validation_Logic')?['extracted_evidence']},
  "processing_time_ms": @{sub(ticks(utcNow()), ticks(triggerOutputs()?['headers']['x-ms-client-request-id']))},
  "timestamp": @{utcNow('u')}
}
```

> **⚠️ Dynamic Content Note:** Replace `Validation_Logic` with the actual name of your validation action from Lab 9. When typing `@`, the Designer will show available dynamic content from previous steps.

### Using the Expression Builder (Optional)

If typing expressions directly is cumbersome, use the Designer's dynamic content picker:

1. Click inside the **Inputs** field
2. A **Dynamic content** panel appears on the right
3. For `source_file`, search for "Name" in dynamic content → select **Name** from the trigger
4. For `verdict`, `confidence`, etc., select the corresponding outputs from your Lab 9 action
5. For `timestamp`, in the **Expression** tab, use `utcNow('u')`

> **💡 Tip:** For simplicity, you can hardcode `audit_point_id` as `"AP-001"` or make it dynamic if your input trigger provides it.

### Processing Time Calculation

To calculate processing time between the trigger and the Compose action:

1. In the **Expression** tab, use:
   ```
   div(sub(ticks(utcNow()), ticks(triggerOutputs()?['headers']?['Date'])), 10000)
   ```
   - This subtracts the trigger's start time from the current time and divides by 10,000 to convert to milliseconds

2. **Alternative (simpler):** Hardcode an estimate like `2340` for now; you can calculate it dynamically in later refinements

---

## Step 4: Verify the Compose Output

1. Click outside the **Inputs** field to confirm your entry
2. The Compose action now shows a summary of your JSON structure
3. Do **not** save yet — we'll add the Blob Storage write action next

---

## Step 5: Add the Create Blob Action

The **Create blob** action (from Azure Blob Storage) writes the JSON output to your `audit-output` container.

1. Click the **+** button below the Compose action
2. In the **Choose an operation** search box, type **blob**
3. Under **Azure Blob Storage**, select **Create blob** (from Microsoft)

---

## Step 6: Configure the Create Blob Action

When you select **Create blob**, a connection panel appears. Configure the following fields:

### Connection

1. If you don't have an existing connection, click **Change connection** → **Use connection string**
2. Paste your Storage Account connection string from your `.env` file:
   ```
   DefaultEndpointProtocol=https;AccountName=XXXXX;AccountKey=XXXXX;EndpointSuffix=core.windows.net
   ```
3. Click **Create** to establish the connection
   - If you already have a connection from Lab 6 or Lab 7, select it here

### Container Name

1. In the **Container** field, click the dropdown
2. Select **audit-output** (the output container you created in Lab 4)
   - If it doesn't appear, verify it exists in your Storage Account

### Blob Name

1. In the **Blob name** field, enter an expression to generate unique blob names:
   ```
   @{concat(utcNow('yyyyMMdd_HHmmss'), '-', triggerBody()?['Name'], '.json')}
   ```
   - **Example output:** `20240318_153000-slide_008.png.json`
   - This creates a timestamped filename to avoid collisions

2. **Alternative format** (simpler):
   ```
   @{triggerBody()?['Name']}-result.json
   ```
   - **Example output:** `slide_008.png-result.json`

### Blob Content

1. In the **Blob content** field, click the **Dynamic content** button
2. Under the **Outputs** section, find **Outputs** (from the Compose action) and select it
   - This inserts the entire JSON object from the Compose action

> **💡 Alternative:** You can also manually reference the Compose output using:
> ```
> @{outputs('Compose')}
> ```

### Configuration Summary

Your Create blob action should now look like this:

| Field | Value |
|-------|-------|
| **Container** | `audit-output` |
| **Blob name** | `@{concat(utcNow('yyyyMMdd_HHmmss'), '-', triggerBody()?['Name'], '.json')}` |
| **Blob content** | Dynamic content: Outputs from Compose |

---

## Step 7: Save the Logic App

1. At the top of the Designer, click **Save**
2. Wait for the confirmation message: "Logic app saved"
3. Your complete pipeline is now saved and ready for testing

---

## Step 8: Review the Complete Workflow

Your Logic App now includes:

1. **Trigger (Lab 6):** When a blob is added or modified in `audit-input`
2. **Get Blob (Lab 7):** Retrieves the full blob content (image)
3. **Analyze Document (Lab 7):** Sends the image to Document Intelligence for text extraction
4. **Analyze Image (Lab 8):** Sends the extracted text + image to Azure OpenAI Vision for semantic analysis
5. **Validation Logic (Lab 9):** Applies business rules to generate verdict, confidence, explanation, and evidence
6. **Compose (Lab 10):** Structures all outputs into a JSON object
7. **Create Blob (Lab 10):** Writes the JSON to `audit-output` for consumption by Power Apps or other systems

---

## Step 9: Understand Data Flow

As data flows through your pipeline:

- **Trigger output** → Provides blob name and properties
- **Get Blob output** → Provides blob content (image binary)
- **Document Intelligence output** → Provides extracted text and table data
- **OpenAI Vision output** → Provides semantic analysis and suggestions
- **Validation Logic output** → Provides verdict, confidence, explanation, evidence
- **Compose output** → Combines all into a single JSON object
- **Create Blob output** → Writes the JSON to Blob Storage with a timestamped filename

---

## Step 10: Test the Pipeline (Preview)

Before the full end-to-end test in Lab 11, verify your workflow structure:

1. In the Designer, click **Save** (if not already saved)
2. Click **Trigger history** or **Run history** (in the main Logic App panel, not the Designer)
3. Check if there are any existing runs from previous labs
4. If you see errors, click a failed run and review the action that failed
5. Make corrections and save again

> **🔍 Note:** The full test (uploading an image and verifying the JSON output) happens in Lab 11. For now, you're checking that the workflow structure is valid.

---

## Troubleshooting

### "Create blob" Action Won't Connect

**Issue:** Connection fails or container list is empty.

**Solutions:**
1. Verify the Storage Account connection string is correct (includes `AccountKey=`)
2. Ensure the `audit-output` container exists in your Storage Account
3. Go to Storage Account → Containers and check the exact name
4. Try deleting the connection and re-creating it with a fresh connection string

### Compose Action Shows Red Error

**Issue:** Expression syntax error in the Inputs field.

**Solutions:**
1. Check for matching braces: `{` and `}`
2. Verify field names match your Lab 9 action outputs (e.g., "verdict", "confidence")
3. Use the **Expression** tab instead of typing directly to avoid typos
4. Reference the correct action name for Lab 9 (check the action's label in the Designer)

### Blob Name Collision

**Issue:** Multiple blobs have the same name.

**Solutions:**
1. Use the timestamped format: `@{concat(utcNow('yyyyMMdd_HHmmss'), '-', triggerBody()?['Name'], '.json')}`
2. Append a unique identifier if needed: `@{concat(triggerBody()?['Name'], '-', guid(), '.json')}`

---

## Key Concepts Summary

| Concept | Purpose |
|---------|---------|
| **Compose action** | Builds a structured JSON object from dynamic content and expressions |
| **Create blob action** | Writes content to Azure Blob Storage with a specified name and container |
| **Dynamic content** | References outputs from previous actions (e.g., trigger data, action results) |
| **Expressions** | Formulas that transform or generate data (e.g., `utcNow()`, `concat()`) |
| **Audit output** | The final JSON that represents the audit decision and analysis |

---

## Phase 3 Complete: Full Pipeline Overview

You have now built the complete **Phase 3** workflow:

### What the Pipeline Does

1. **Listens** for image uploads in the `audit-input` container
2. **Extracts** text and tables from the image using Document Intelligence
3. **Analyzes** the content semantically with Azure OpenAI Vision
4. **Applies** business validation rules to generate a verdict
5. **Structures** the results into a standardized JSON object
6. **Persists** the JSON to the `audit-output` container for downstream systems

### Audit Output Consumption

The JSON output can now be:
- Viewed in Power Apps (Lab 12 - optional)
- Consumed by a frontend application (REST API)
- Analyzed for audit trail and compliance reporting
- Imported into spreadsheets or BI tools

### Next: End-to-End Testing

In **Lab 11**, you will:
- Upload a sample image to `audit-input`
- Monitor the Logic App execution
- Verify the JSON output in `audit-output`
- Validate the audit decision against expected results

---

## Next Steps

- In **Lab 11**, you'll run the full pipeline with a real image and verify the output
- Afterward, you can extend the Logic App by adding error handling, retries, or additional actions
- Auditors can maintain and modify this workflow as audit requirements evolve

---

## Navigation

[← Previous: Build Validation Logic](lab-09-validation.md)

[Next: End-to-End Testing →](lab-11-testing.md)
