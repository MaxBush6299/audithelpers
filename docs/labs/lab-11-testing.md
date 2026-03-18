# Lab 11: End-to-End Testing

**Time required:** 30 minutes  
**Owner:** Felix  
**Prerequisites:** Lab 10 (Generate JSON Output)  
**Objective:** Test the complete audit evidence pipeline end-to-end by uploading a test image and verifying each stage produces expected output.

---

## What You'll Learn

In this lab, you will:

- ✅ Prepare and upload a test image from your audit evidence folder
- ✅ Monitor Logic App execution in real-time using Azure Portal
- ✅ Verify each pipeline stage (trigger, Document Intelligence, OpenAI, validation, output)
- ✅ Inspect the JSON result file in Blob Storage
- ✅ Troubleshoot common failures at each stage

---

## Success Criteria

Before you start, know what success looks like:

> **A running Logic App that, given an image and an audit point, can give approval/rejection with a confidence score and explanation.**

After this lab, you should be able to:
- Upload an image → Logic App triggers
- Stage 2 extracts text via Document Intelligence
- Stage 3 analyzes image via Azure OpenAI Vision
- Stage 4 validates the output
- Stage 5 writes a JSON file to `audit-output` container
- Download and parse that JSON file to confirm verdict, confidence, and explanation

---

## Prerequisites

Verify these are ready before starting:

- ✅ **Lab 10 completed:** Your Logic App outputs JSON to `audit-output` container
- ✅ **Storage Account deployed:** With containers: `audit-input`, `audit-output`
- ✅ **Document Intelligence deployed:** Endpoint and key configured in Logic App
- ✅ **Azure OpenAI deployed:** GPT-4 or GPT-5 deployment configured in Logic App
- ✅ **Test image available:** A sample image from your audit evidence folder (JPG, PNG, or similar)
  - Recommended: A screenshot of a system interface, compliance dashboard, or audit evidence
  - Size: 1-20 MB (typically)
  - Content: Anything that could be audit evidence (receipts, forms, screenshots, photos)

---

## Understanding the End-to-End Flow

The audit pipeline has 5 stages:

| Stage | What It Does | Input | Output |
|-------|--------------|-------|--------|
| **1. Trigger** | Detects image uploaded to `audit-input` | Image file | Blob metadata (name, path) |
| **2. Extract** | Document Intelligence extracts text from image | Image + OCR model | Text with layout |
| **3. Analyze** | Azure OpenAI Vision analyzes image + text | Image + extracted text | Analysis & evaluation |
| **4. Validate** | Validation logic formats the output | Analysis result | Structured verdict object |
| **5. Output** | JSON written to `audit-output` container | Verdict object | JSON file (`verdict_<timestamp>.json`) |

In this lab, you'll monitor each stage and verify the outputs.

---

## Step 1: Prepare Your Test Image

### 1.1 Choose a Test Image

You'll use your own audit evidence. Choose a sample image that:
- Is a screenshot, photo, or scan of a document
- Contains readable text or visual information
- Is between 1-20 MB in size
- Is in a common format: `.jpg`, `.png`, `.gif`, `.tiff`, or `.pdf`

**Example test images:**
- Screenshot of a system dashboard or interface
- Photo of compliance documentation
- Scanned regulatory form or checklist
- Any real audit evidence from your folder

### 1.2 Note the Image Details

Before uploading, note:
- **File name:** e.g., `compliance-report.jpg`
- **Content:** What's in the image (e.g., "Dashboard showing MFA enabled")
- **Expected verdict:** What you think should happen (e.g., "APPROVED - MFA is enabled")

This helps you verify the Logic App produces sensible output.

---

## Step 2: Upload Test Image to Azure Portal

### 2.1 Navigate to Storage Account

1. Go to [portal.azure.com](https://portal.azure.com)
2. Search for **Storage Accounts** and select your storage account (from Lab 0/4)
   - Name format: `storageaudit<initials>` or similar

### 2.2 Navigate to audit-input Container

1. In the left menu, click **Containers**
2. Click the **audit-input** container
   - You should see an empty container or previously uploaded test files

### 2.3 Upload Your Test Image

1. Click **Upload** at the top
2. In the upload panel:
   - Click **Select files** or drag your image into the area
   - Select your test image from Step 1.1
3. Click **Upload**
   - Status should show "Upload succeeded"

**Note the exact upload time** — you'll use this to find the matching run in Logic App history.

---

## Step 3: Monitor Logic App Execution in Real-Time

### 3.1 Navigate to Your Logic App

1. Go to [portal.azure.com](https://portal.azure.com)
2. Search for **Logic Apps** and select it
3. Click your Logic App (e.g., `audit-logic-app`)

### 3.2 Watch Runs History

1. In the left menu, click **Runs history** or **Overview** (depending on your view)
2. You should see recent runs listed with timestamps
3. **Within 1-2 minutes of uploading**, a new run should appear
   - Status will show: `Running`, `Succeeded`, or `Failed`
   - Timestamp should match your upload time (within 1 minute)

**If no run appears within 2 minutes:**
- See **Troubleshooting: Trigger not firing** below

### 3.3 Click the Run to See Details

Once the run appears:

1. Click the run to open its details view
2. You'll see a visual flow diagram showing each action:
   - Trigger (blob uploaded)
   - Document Intelligence action
   - OpenAI action
   - Validation action
   - Write JSON to Blob action

Each action shows:
- **Status:** Green checkmark (✓ Succeeded), Red X (✗ Failed), or Spinning icon (⧗ Running)
- **Duration:** How long the action took
- **Inputs/Outputs:** The data passed in and produced

---

## Step 4: Verify Each Pipeline Stage

### 4.1 Verify Trigger Fired

In the run details:

1. Click the **Trigger** box (usually at the top or labeled "When a blob is added or modified")
2. Expand **Outputs**
3. Verify you see:
   - `Id`: The blob identifier
   - `DisplayName`: Your uploaded filename
   - `Path`: Path to blob in container

**Example output:**
```json
{
  "Id": "/subscriptions/.../audit-input/compliance-report.jpg",
  "DisplayName": "compliance-report.jpg",
  "Path": "/audit-input/compliance-report.jpg"
}
```

**✅ Success:** Trigger fired and detected your image.

---

### 4.2 Verify Document Intelligence Extracted Text

1. In the run details, click the **Document Intelligence** action (or "Extract text via OCR" action)
2. Expand **Outputs**
3. Verify you see a large JSON object containing:
   - `pages`: Array of pages analyzed
   - Each page has: `words`, `lines`, `paragraphs` with extracted text
   - Example structure:

```json
{
  "pages": [
    {
      "pageNumber": 1,
      "width": 612,
      "height": 792,
      "words": [
        {
          "text": "Compliance",
          "confidence": 0.99,
          "boundingBox": [...]
        }
      ]
    }
  ]
}
```

**Verify:**
- ✅ `words` array contains actual text from your image
- ✅ `confidence` scores are high (0.9 or above)
- ✅ No error messages in outputs

**❌ If failed:** Document Intelligence action shows red X
- See **Troubleshooting: Document Intelligence fails** below

---

### 4.3 Verify Azure OpenAI Analyzed the Image

1. In the run details, click the **Azure OpenAI Vision** action (or "Analyze with GPT-4" action)
2. Expand **Outputs**
3. Verify you see:
   - `content`: Text response from OpenAI (analysis of the image)
   - Should contain readable evaluation of your audit evidence

**Example output:**
```json
{
  "content": "The dashboard clearly shows Multi-Factor Authentication is enabled. All user accounts have MFA configured with green checkmarks visible. The interface timestamp and security indicators confirm MFA is actively enforced."
}
```

**Verify:**
- ✅ `content` is not empty and not an error message
- ✅ `content` describes what's in your image
- ✅ `content` makes sense as an analysis

**❌ If failed:** OpenAI action shows red X
- See **Troubleshooting: OpenAI fails** below

---

### 4.4 Verify Validation Logic Passed

1. In the run details, click the **Validation** action (or "Build verdict" action)
2. Expand **Outputs**
3. Verify you see a structured object with:
   - `verdict`: `"APPROVED"` or `"REJECTED"` (not null, not error)
   - `confidence`: A number between 0.0 and 1.0 (e.g., 0.95)
   - `explanation`: A text explanation of the verdict
   - `analyzed_text`: The text extracted in Stage 2
   - `timestamp`: When the analysis occurred

**Example output:**
```json
{
  "verdict": "APPROVED",
  "confidence": 0.95,
  "explanation": "Evidence clearly shows MFA is enabled across all accounts",
  "analyzed_text": "Multi-Factor Authentication...",
  "timestamp": "2026-03-20T14:32:15Z"
}
```

**Verify:**
- ✅ `verdict` is either `"APPROVED"` or `"REJECTED"` (not null, not error, not random)
- ✅ `confidence` is between 0.0 and 1.0
- ✅ `explanation` is non-empty and makes sense
- ✅ No error messages or null values

**❌ If failed:** Validation action shows red X
- See **Troubleshooting: Validation returns error** below

---

### 4.5 Verify JSON Written to Blob Storage

1. In the run details, click the **Write JSON to audit-output** action (or similar name)
2. Expand **Outputs**
3. Verify you see:
   - Success status (no error)
   - Metadata about the created blob (name, size, timestamp)

**Example output:**
```json
{
  "id": "/subscriptions/.../audit-output/verdict_20260320T143215.json",
  "displayName": "verdict_20260320T143215.json",
  "path": "/audit-output/verdict_20260320T143215.json"
}
```

**Verify:**
- ✅ Action succeeded (green checkmark)
- ✅ Blob name follows pattern `verdict_<timestamp>.json`
- ✅ Path shows `/audit-output/` container

**❌ If failed:** Output action shows red X
- See **Troubleshooting: Output not written** below

---

## Step 5: Download and Inspect the JSON Result

### 5.1 Navigate to audit-output Container

1. Go to [portal.azure.com](https://portal.azure.com)
2. Open your **Storage Account** (same as Step 2.1)
3. Click **Containers** in the left menu
4. Click the **audit-output** container

### 5.2 Find Your Result File

1. In the container, you should see one or more `.json` files
2. The most recent file (sorted by "Last modified" timestamp) is likely your result
3. Look for a file named something like: `verdict_20260320T143215.json`

**If you don't see any files:**
- Wait 10-30 seconds and refresh (F5)
- Check the run history again — did the "Write JSON" action actually complete?

### 5.3 Download the JSON File

1. Right-click the JSON file and select **Download**, OR
2. Click the file name to open it in the portal
3. Copy the file contents

**Example file contents:**
```json
{
  "verdict": "APPROVED",
  "confidence": 0.92,
  "explanation": "The audit evidence clearly shows MFA is enabled and enforced",
  "analyzed_text": "Multi-Factor Authentication enabled for all users. Security dashboard confirms active enforcement. Last audit: 2026-03-15.",
  "timestamp": "2026-03-20T14:32:15Z"
}
```

---

## Verification Checklist

Use this checklist to confirm end-to-end success:

### Pre-Test
- ☐ Test image selected and ready
- ☐ Logic App deployed and last saved within 24 hours
- ☐ Storage containers created (`audit-input`, `audit-output`)

### Execution
- ☐ Image uploaded to `audit-input` container
- ☐ Logic App run appears within 1-2 minutes
- ☐ Run status is `Succeeded` (not `Failed`)

### Stage Verification
- ☐ **Trigger fired:** Run shows blob detected with correct filename
- ☐ **Document Intelligence succeeded:** Text extraction shows readable content
- ☐ **Azure OpenAI succeeded:** Analysis is coherent and describes the image
- ☐ **Validation succeeded:** Verdict is `APPROVED` or `REJECTED`, not error
- ☐ **Confidence score valid:** Between 0.0 and 1.0 (not null, not negative)
- ☐ **Explanation makes sense:** Describes why verdict was given
- ☐ **JSON written:** File created in `audit-output` container

### Final Verification
- ☐ JSON file downloaded and opened successfully
- ☐ JSON is valid (parseable; not malformed)
- ☐ All required fields present: `verdict`, `confidence`, `explanation`, `timestamp`
- ☐ Verdict aligns with evidence (e.g., if image shows MFA enabled, verdict is APPROVED)

**All checkboxes marked?** ✅ **Congratulations, end-to-end testing passed!**

---

## Troubleshooting

### Issue: Trigger Not Firing (No Run Appears)

**Symptom:** You uploaded an image to `audit-input` 2+ minutes ago, but no run appears in Logic App history.

**Root causes and solutions:**

#### A. Trigger Disabled or Not Saved
- Go to Logic App Designer
- Verify the trigger exists and is enabled (green checkmark, not disabled icon)
- If you don't see a trigger, click the trigger area and re-add the "When a blob is added or modified" trigger
- **Save** the Logic App (Ctrl+S)
- Wait 1 minute and upload a new test image

#### B. Connection String Incorrect
- Go to Logic App Designer
- Click the trigger to expand it
- Check the connection:
  - If red X appears: Connection failed
  - Solution: Delete the connection and re-create it with the correct Storage Account connection string from your `.env` file
- Save and retry

#### C. Container Name Mismatch
- In Logic App Designer, click the trigger
- Verify the **Container** field shows exactly `audit-input` (case-sensitive in some systems)
- If wrong, correct it and save

#### D. Polling Interval Too Long
- In Logic App Designer, click the trigger
- Check **"How often to check for items"** — if it's set to "1 Hour", the Logic App might not have checked yet
- For testing, change to **"1 Minute"** and save
- Upload a new image and wait up to 2 minutes

#### E. Storage Account Permission Issue
- Verify your Storage Account connection is authenticated
- Go to Storage Account → Access Control (IAM)
- Ensure your user has "Storage Blob Data Contributor" or higher role
- If not, request access or create a new connection in Logic App

**Still not firing?** Try these:
1. Delete the Logic App trigger and add a new one
2. Test with a different file format (e.g., `.png` instead of `.jpg`)
3. Try uploading from Storage Account portal (not Azure Storage Explorer or CLI)

---

### Issue: Document Intelligence Fails

**Symptom:** The run starts but the Document Intelligence action shows a red X with error.

**Common errors and solutions:**

#### Error: "Invalid endpoint"
- **Cause:** Document Intelligence endpoint is malformed or unreachable
- **Solution:**
  - Go to Logic App Designer
  - Click the Document Intelligence action
  - Verify the endpoint URL (e.g., `https://eastus2.api.cognitive.microsoft.com/`)
  - Copy it from your `.env` file exactly, including the trailing slash
  - Save and retry

#### Error: "401 Unauthorized" or "Invalid key"
- **Cause:** API key is incorrect or expired
- **Solution:**
  - Go to Azure Portal → Document Intelligence resource
  - Click **Keys and Endpoint**
  - Verify Key 1 is not expired or rotated
  - If expired, generate a new key
  - Update the Logic App action with the new key
  - Save and retry

#### Error: "Image format not supported"
- **Cause:** Your test image is in an unsupported format
- **Solution:**
  - Use a different test image in `.jpg`, `.png`, `.tiff`, or `.gif` format
  - Verify file isn't corrupted (try opening it locally first)
  - Try a smaller image or screenshot

#### Error: "Quota exceeded"
- **Cause:** Document Intelligence has hit daily quota
- **Solution:**
  - Wait 24 hours for quota to reset, OR
  - Go to Document Intelligence resource → Upgrade pricing tier (if on free tier)
  - OR contact Azure Support to request quota increase

---

### Issue: Azure OpenAI Fails

**Symptom:** The OpenAI Vision action shows a red X with error.

**Common errors and solutions:**

#### Error: "Invalid endpoint" or "404 Not Found"
- **Cause:** OpenAI endpoint doesn't exist or URL is malformed
- **Solution:**
  - Go to Logic App Designer
  - Click the OpenAI action
  - Verify the endpoint URL (e.g., `https://myairesource.openai.azure.com/`)
  - Verify the deployment name (e.g., `gpt-4` or `gpt-5`)
  - Copy exact values from your `.env` file
  - Save and retry

#### Error: "401 Unauthorized" or "Invalid API key"
- **Cause:** OpenAI API key is missing, incorrect, or expired
- **Solution:**
  - Go to Azure Portal → Azure AI / OpenAI resource
  - Click **Keys and Endpoint**
  - Verify Key 1 (or Key 2)
  - Update Logic App action with the correct key
  - Save and retry

#### Error: "Model not found" or "Deployment doesn't exist"
- **Cause:** The deployment name is wrong or deployment is not active
- **Solution:**
  - Go to Azure Portal → Azure AI resource → Model deployments
  - Verify your GPT-4 or GPT-5 deployment exists and is "Succeeded"
  - If not, create a new deployment or check the name
  - Update Logic App action with correct deployment name
  - Save and retry

#### Error: "Quota exceeded" or "Rate limited"
- **Cause:** You've exceeded token limits or request rate
- **Solution:**
  - Wait a few minutes before retrying
  - If persistent, check Azure OpenAI quota in Portal
  - Request quota increase from Azure Support

#### Error: "Image too large"
- **Cause:** Your test image exceeds OpenAI's size limits
- **Solution:**
  - Try a smaller image (< 10 MB)
  - Compress the image locally and re-upload
  - Try a different screenshot or photo

---

### Issue: Validation Returns Error or Null Verdict

**Symptom:** The Validation action succeeds but produces `verdict: null` or error output.

**Common causes and solutions:**

#### A. Invalid JSON from Previous Stages
- **Cause:** Document Intelligence or OpenAI output is malformed
- **Solution:**
  - Check Step 4.2 and 4.3 — verify those outputs are valid JSON
  - If those stages failed, fix them first (see previous troubleshooting)

#### B. Validation Logic Bug
- **Cause:** The validation action has a formula or parsing error
- **Solution:**
  - Go to Logic App Designer
  - Click the Validation action
  - Review the logic/code (should extract `verdict`, `confidence`, etc.)
  - If using a Compose or Parse JSON action, verify the schema matches the actual data
  - Test locally with sample data if possible
  - Reach out to team (lab creator Bond can help debug validation logic)

#### C. Expected Fields Missing
- **Cause:** OpenAI output doesn't include required fields for validation
- **Solution:**
  - Check Step 4.3 again — OpenAI response should have `content` field
  - If missing, verify OpenAI action is configured correctly (deployment name, model, prompt)
  - Re-upload a test image and retry

**Still seeing errors?** Collect this info and reach out to the team:
- Screenshot of the failed run and error message
- Content of the Validation action's Inputs and Outputs
- Your test image (if shareable)

---

### Issue: Output Not Written (JSON File Missing from audit-output)

**Symptom:** Logic App run succeeded, but no JSON file appears in `audit-output` container.

**Root causes and solutions:**

#### A. File Actually Exists, Just Not Visible
- **Solution:**
  - Refresh the audit-output container (press F5)
  - Wait 10-30 seconds (blob upload has slight delay)
  - Sort by "Last modified" to find newest file
  - Try a second test upload

#### B. Write Action Didn't Complete
- **Solution:**
  - Click the run details
  - Scroll to the "Write JSON to audit-output" action
  - Expand it and check status:
    - Red X = action failed (check error message)
    - Green ✓ = action succeeded but file might not exist yet (wait and refresh)
    - Spinning icon = still running (wait a few seconds)

#### C. Storage Account Connection Failed
- **Cause:** Logic App doesn't have permission to write to Blob Storage
- **Solution:**
  - Go to Logic App Designer
  - Click the "Write JSON" action
  - Check the connection:
    - If red X: Connection failed
    - Delete the connection and re-create using Storage Account connection string
  - Verify Storage Account allows your user to write blobs (IAM → Storage Blob Data Contributor)
  - Save and retry

#### D. Container Doesn't Exist
- **Cause:** `audit-output` container was deleted or never created
- **Solution:**
  - Go to Storage Account → Containers
  - If `audit-output` doesn't exist, click **+ Container** and create it
  - Update Logic App action if needed to use correct container name
  - Save and retry

#### E. Filename Collision or Permissions
- **Cause:** File already exists or overwrite protection is on
- **Solution:**
  - Verify the "Write JSON" action uses a unique filename (typically includes timestamp)
  - Check Blob Storage access policies — ensure your app can overwrite blobs
  - Try uploading with a different test image name to force a new run with different timestamp

**Still no file?** Try this diagnostic:
1. Manually upload a `.json` file to `audit-output` via Portal (as a test)
2. If that succeeds, the container is writable → the issue is with the Logic App action
3. If that fails, the Storage Account has permission issues → check IAM and access policies

---

## Success Confirmation

When you've completed all steps and passed the verification checklist, you have successfully:

✅ **End-to-End Tested the Audit Pipeline**

Your system is now ready for:
1. **Real audit evidence:** You can use this setup to process actual compliance evidence
2. **Lab 12 (Optional):** Build a Power Apps frontend for auditors to upload and view results
3. **Production hardening:** Add authentication, Key Vault, Azure Monitor, alerts
4. **Scaling:** Enable the auditor to process batches of evidence with consistent verdicts

---

## Next Steps

### Option A: Process Real Evidence (Recommended)
1. Prepare your actual audit evidence (screenshots, photos, scanned forms)
2. Create an audit point and instruction (e.g., "Is MFA enabled?" with evidence requirements)
3. Upload evidence to `audit-input`
4. Monitor the run and review the verdict JSON
5. Repeat for each piece of evidence

### Option B: Build a Power Apps Portal (Optional — Lab 12)
If you want a user-friendly interface for auditors:
- [Lab 12: Power Apps Audit Portal (Optional)](lab-12-power-apps.md)
- Enables non-technical users to upload evidence and view verdicts
- Adds approval/rejection audit trail and comments
- Integrates with the Logic App workflow

### Option C: Production Hardening (Post-Lab)
Before deploying to production:
- Add authentication (Azure AD for Logic App triggers)
- Move secrets to Azure Key Vault
- Set up Azure Monitor and alerts
- Enable managed identity for Logic App
- Add data retention policies
- Set up backup and disaster recovery

---

## Common Questions (FAQ)

### Q: How long does a full run take?
**A:** Typically 1-3 minutes:
- Trigger detection: 1-2 minutes (polling interval)
- Document Intelligence extraction: 5-15 seconds
- Azure OpenAI analysis: 10-30 seconds
- Validation and JSON write: 2-5 seconds

### Q: Can I upload multiple images and process them in parallel?
**A:** Yes, but they'll run sequentially (one per trigger poll). For high throughput, use Azure Functions or Scale Set approach (outside this lab).

### Q: What if the verdict is wrong?
**A:** Check:
1. Is the image clear and readable?
2. Does the Azure OpenAI prompt match your audit requirements?
3. Is the validation logic correct (check the formula in the Validation action)?
4. Try a different test image to see if the issue is consistent

### Q: Can I modify the verdict format (JSON structure)?
**A:** Yes, in the "Write JSON" action, edit the Compose action to output a different JSON schema. Lab 10 covers this.

### Q: How do I delete old test runs and JSON files?
**A:** 
- **Delete runs:** Go to Logic App → Runs history → select run → Delete
- **Delete JSON files:** Go to Storage Account → Containers → audit-output → select file → Delete

### Q: Is this scalable for thousands of audit images?
**A:** Yes, but not out of the box. Current design uses Logic App Consumption tier (polling), which handles ~100s per day. For higher throughput:
- Upgrade to Logic App Standard with queue-based triggers
- Add Azure Functions for parallel processing
- Use Durable Functions for long-running workflows
- See team for production architecture recommendations

---

## Key Takeaways

1. **Trigger:** Monitor "Runs history" for real-time feedback
2. **Verify each stage:** Click each action to see Inputs/Outputs
3. **Trust the JSON:** If JSON file exists and is valid, the pipeline worked
4. **Debug systematically:** Start with trigger, then Document Intelligence, then OpenAI, then validation
5. **Test before scaling:** Run a few end-to-end tests with diverse evidence before processing production data

---

## Team Contacts

- **Pipeline questions:** Bond (bond@team.local)
- **Azure services:** Moneypenny (moneypenny@team.local)
- **Architecture:** M (m@team.local)
- **Testing/troubleshooting:** Felix (felix@team.local)

---

[← Previous: Generate JSON Output](lab-10-output.md) | [Next: Power Apps Audit Portal (Optional) →](lab-12-powerapps.md)

---

*Lab 11 created by Felix. Last updated: March 2026.*
